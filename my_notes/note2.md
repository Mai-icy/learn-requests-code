# requests源码阅读整理

## 主要运行过程和思想

程序目录（源码的代码内文件注释）：

`models.py`: This module contains the primary objects that power Requests.

`session.py`: This module provides a Session object to manage and persist settings across
requests (cookies, auth, proxies).

`adapters.py`: This module contains the transport adapters that Requests uses to define
and maintain connections.

`api.py`: This module implements the Requests API.

### 在`models.py`文件中

将 请求 `Request`作为一个类，内部包含了请求的各种参数，请求类并不包含请求功能。它的功能只有储存相关参数和检查相关参数的合法性，以及扩大参数适应性。同时具有和其他类的适配性。

同时，请求分为`Request`类和`PreparedRequest`类。

`Request`类用于接收和储存数据，并不检查数据合法性

通过`prepare()`操作，即检查请求参数合法性。`Request`类将生成合法的可用的`PreparedRequest`类，见以下源码

`Request`类的`prepare`操作

```python
class Request(RequestHooksMixin):
    ...
	def prepare(self):
        """Constructs a :class:`PreparedRequest <PreparedRequest>` for transmission and returns it."""
        p = PreparedRequest()
        p.prepare(
            method=self.method,
            url=self.url,
            headers=self.headers,
            files=self.files,
            data=self.data,
            json=self.json,
            params=self.params,
            auth=self.auth,
            cookies=self.cookies,
            hooks=self.hooks,
        )
        return p
    ...
```

`Request`类调用`PreparedRequest`的`prepare()`

检查合法性的过程：

```python
class PreparedRequest(RequestEncodingMixin, RequestHooksMixin):
    ...
	def prepare(
        self,
        method=None,
        url=None,
        headers=None,
        files=None,
        data=None,
        params=None,
        auth=None,
        cookies=None,
        hooks=None,
        json=None,
    ):
        """Prepares the entire request with the given parameters."""

        self.prepare_method(method)
        self.prepare_url(url, params)
        self.prepare_headers(headers)
        self.prepare_cookies(cookies)
        self.prepare_body(data, files, json)
        self.prepare_auth(auth, url)

        # Note that prepare_auth must be last to enable authentication schemes
        # such as OAuth to work on a fully prepared request.

        # This MUST go after prepare_auth. Authenticators could add a hook
        self.prepare_hooks(hooks)
    ...
```

结构严密，可观性相当。

利用了`Mixin`类的组合，增加了代码复用性。

由于`Request`类并不检查编码，故不使用`RequestEncodingMixin`。

`RequestEncodingMixin`虽然只被使用了一次，应当可以直接并入`PreparedRequest`类中，但是同时可以发现，移出的`RequestEncodingMixin`内容仅和很复杂的编码关系有关，为了利于测试，单独出来是合理的，并且增进了代码的可读性。



`Response`类的思想相似，将回复作为一个类，装填回复的内容并返回给用户以便操作。`Response`类额外提供了一个序列化功能，可以序列化回复类进行保存。

`Response`类提供了一个`close()`函数，是因为考虑到回复的数据量可能较大，可主动调用`close()`用于释放`raw`对象即内容的空间。又由于`Response`类提供了上下文管理器`with`关键词的功能，可这样使用：

```python
with requests.get("https://www.baidu.com") as response:
	data = response.status_code
    ...  # get the data you want
print(data)
...  # use the data
```

在需要的数据远小于收到数据大小的时候可以使用。



### 在`session.py`文件中

其中包含了类`Session`，这也是用户直接操作的对象，该对象负责处理上面讲的`Request`和`Response`类，`Session`管理他们并且发送他们以及装填他们。为了使用的便利，`Request`一般并不会被用户使用。例如以下代码：

```python
import requests

session = requests.Session()
response = session.get("https://www.baidu.com")

```

> `requests.Session()`和`requests.session()`没有什么区别，`session()`只是`session.py`文件中的一个函数，源码如下：
>
> ```
> def session():
>     """
>     Returns a :class:`Session` for context-management.
> 
>     .. deprecated:: 1.0.0
> 
>         This method has been deprecated since version 1.0.0 and is only kept for
>         backwards compatibility. New code should use :class:`~requests.sessions.Session`
>         to create a session. This may be removed at a future date.
> 
>     :rtype: Session
>     """
>     return Session()
> ```
>
> 其中也写道可能会在未来被删除，实际上就是实例化一个`Session`类。

用户只写了`session.get("https://www.baidu.com")`因为一般的访问，不考虑多的东西，就只要`url`就好了，其中的过程为创建一个`Request`对象，塞入`url`以及其他的参数的默认（因为我们没有给出），再将`Request`对象进行`prepare()`即参数合法性检查得到一个`PreparedRequest`，发送它，得到`Response`对象，并且返回。

简单来说是这样，但复杂上来说，请求由于是`urllib`库来实现，所以写了一个`adapters.py`内部包含了对`urllib`的封装和适配，属于适配器模式。session获取对应的适配器`Adapter`，将请求传入，得到回复，此时由于网站跳转的特例，需要再有处理。

见`Session.send()`源码：

```python
    def send(self, request, **kwargs):
        """Send a given PreparedRequest.

        :rtype: requests.Response
        """
        # Set defaults that the hooks can utilize to ensure they always have
        # the correct parameters to reproduce the previous request.
        kwargs.setdefault("stream", self.stream)
        kwargs.setdefault("verify", self.verify)
        kwargs.setdefault("cert", self.cert)
        if "proxies" not in kwargs:
            kwargs["proxies"] = resolve_proxies(request, self.proxies, self.trust_env)

        # It's possible that users might accidentally send a Request object.
        # Guard against that specific failure case.
        if isinstance(request, Request):
            raise ValueError("You can only send PreparedRequests.")

        # Set up variables needed for resolve_redirects and dispatching of hooks
        allow_redirects = kwargs.pop("allow_redirects", True)
        stream = kwargs.get("stream")
        hooks = request.hooks

        # Get the appropriate adapter to use
        adapter = self.get_adapter(url=request.url)

        # Start time (approximately) of the request
        start = preferred_clock()

        # Send the request
        r = adapter.send(request, **kwargs)

        # Total elapsed time of the request (approximately)
        elapsed = preferred_clock() - start
        r.elapsed = timedelta(seconds=elapsed)

        # Response manipulation hooks
        r = dispatch_hook("response", hooks, r, **kwargs)

        # Persist cookies
        if r.history:

            # If the hooks create history then we want those cookies too
            for resp in r.history:
                extract_cookies_to_jar(self.cookies, resp.request, resp.raw)

        extract_cookies_to_jar(self.cookies, request, r.raw)

        # Resolve redirects if allowed.
        if allow_redirects:
            # Redirect resolving generator.
            gen = self.resolve_redirects(r, request, **kwargs)
            history = [resp for resp in gen]
        else:
            history = []

        # Shuffle things around if there's history.
        if history:
            # Insert the first (original) request at the start
            history.insert(0, r)
            # Get the last request made
            r = history.pop()
            r.history = history

        # If redirects aren't being followed, store the response on the Request for Response.next().
        if not allow_redirects:
            try:
                r._next = next(
                    self.resolve_redirects(r, request, yield_requests=True, **kwargs)
                )
            except StopIteration:
                pass

        if not stream:
            r.content

        return r
```

其中还包含了`hook`函数的使用，以及cookies的延续和保存。关于cookies的延续，由于类名为Session即会话，是多次连接的窗口，可以想象做浏览器帮助用户和网站之间的连接，保存cookies也符合设计目的。

其他：

该文件内还包含了`merge_setting`,`merge_hooks`函数以及`SessionRedirectMixin`类。

> `Session`也支持序列化



### 在`adapters.py`文件中

只定义了`BaseAdapter`和`HTTPAdapter`，很显然他们是继承关系，其作用为适配了`urllib`的库。

请求利用了连接池，`urllib`的`PoolManager`类

代理利用`urllib`的`ProxyManager`类

证书认证也是`urllib`内包含的，做的仅是绑定证书



对于一般用户（仅使用`Session`或者直接使用`requests.get`等）`Adapter`仅使用了`send`函数。

`Adapter`包含了多项设置内容

```python
    def __init__(
        self,
        pool_connections=DEFAULT_POOLSIZE,
        pool_maxsize=DEFAULT_POOLSIZE,
        max_retries=DEFAULT_RETRIES,
        pool_block=DEFAULT_POOLBLOCK,
    ):
    """
	:param pool_connections: The number of urllib3 connection pools to cache.
    :param pool_maxsize: The maximum number of connections to save in the pool.
    :param max_retries: The maximum number of retries each connection
        should attempt. Note, this applies only to failed DNS lookups, socket
        connections and connection timeouts, never to requests where data has
        made it to the server. By default, Requests does not retry failed
        connections. If you need granular control over the conditions under
        which we retry a request, import urllib3's ``Retry`` class and pass
        that instead.
    :param pool_block: Whether the connection pool should block for connections.
    """
    ...
```

其中默认参数为以下

```python
DEFAULT_POOLBLOCK = False
DEFAULT_POOLSIZE = 10
DEFAULT_RETRIES = 0
DEFAULT_POOL_TIMEOUT = None
```

如果有需求，可以按照以下设置以上参数

```python
import requests
s = requests.Session()
a = requests.adapters.HTTPAdapter(max_retries=3)  # 输入对应参数
s.mount('http://', a)
```

其中关于`Session`包含的`mount()`函数，一个`Session`对象仅包含两个`Adapter`对象，一个用于连接`http`请求一个用于连接`https`请求

`mount()`函数影响`get_adapter()`函数，可把`mount()`理解为`set_adapter`

以下源码助于理解，也是`Session`对象和`Adapter`对象之间的组合方法

```python
	def __init__(self)
    	...
        
        # Default connection adapters.
	    self.adapters = OrderedDict()
        self.mount("https://", HTTPAdapter())
        self.mount("http://", HTTPAdapter())

	def mount(self, prefix, adapter):
        """Registers a connection adapter to a prefix.

        Adapters are sorted in descending order by prefix length.
        """
        self.adapters[prefix] = adapter
        keys_to_move = [k for k in self.adapters if len(k) < len(prefix)]

        for key in keys_to_move:
            self.adapters[key] = self.adapters.pop(key)
            
    def get_adapter(self, url):
        """
        Returns the appropriate connection adapter for the given URL.

        :rtype: requests.adapters.BaseAdapter
        """
        for (prefix, adapter) in self.adapters.items():

            if url.lower().startswith(prefix.lower()):
                return adapter

        # Nothing matches :-/
        raise InvalidSchema(f"No connection adapters were found for {url!r}")
```

以上就说明了`requests`库中的类之间的关系

再说明最简单的`requests.get("https://www.baidu.com")`的情况

这些函数的操作被放入`api.py`

### 在`api.py`文件中

其中包含的函数都是及其简化用户使用`requests`库

包含了`get`,`options`,`head`,`post`,`put`,`patch`,`delete`多种用于请求的请求方法函数

以及`request(method, url, **kwargs)`函数这种通用函数

去掉注释它的源码为：

```python
def request(method, url, **kwargs):
    with sessions.Session() as session:
        return session.request(method=method, url=url, **kwargs)
    
def get(url, params=None, **kwargs):
    return request("get", url, params=params, **kwargs)

def head(url, **kwargs):
    kwargs.setdefault("allow_redirects", False)
    return request("head", url, **kwargs)

def post(url, data=None, json=None, **kwargs):
    return request("post", url, data=data, json=json, **kwargs)
...  # 其他省略
```

给用户一个低门槛的使用，考虑到请求有时就图一个网址填进去，其他的都不想考虑，此处就在实例化`Session`中默认了用户没有设置的所有参数。

## 数据结构的使用

### 在`structures.py`文件中

其设计了两个数据结构`CaseInsensitiveDict` 和`LookupDict`

#### `CaseInsensitiveDict`

功能：

- 不区分键的大小写，大小写不敏感
- 对于相同字母不同大小写的键会保留最后一次的键，覆盖之前的键
- 基于有序字典

使用组合的方式使用了`OrderedDict`，并继承了`MutableMapping`

重载了

`__setitem__`,`__getitem__`,`__delitem__`, `__iter__`, `__len__`,`__eq__`, `__repr__`

仅使用于请求回复中的`headers`

`headers`是不区分大小写的，在输入对应`header`会遇到多种不同大小写的键，使用该类保证输入兼容性。

#### `LookupDict`

功能：

- 有名字`name`的成员变量
- 使用方括号获取等价于`.get()`，是安全的不会报错

继承了`dict`

重载了

`__repr__`,`__getitem__`,`get`

仅用于对应状态码和错误的消息、情况的`status_codes.py`文件，但仅用于编辑`__doc__`文档环境变量

## 为python2和python3的兼容性

### 在`compat.py`文件中

判断python版本

```python
# Syntax sugar.
_ver = sys.version_info

#: Python 2.x?
is_py2 = _ver[0] == 2

#: Python 3.x?
is_py3 = _ver[0] == 3
```

试探引用

```python
has_simplejson = False
try:
    import simplejson as json

    has_simplejson = True
except ImportError:
    import json

if has_simplejson:
    from simplejson import JSONDecodeError
else:
    from json import JSONDecodeError
```

```python
try:
    import chardet
except ImportError:
    import charset_normalizer as chardet
```

## 其他

