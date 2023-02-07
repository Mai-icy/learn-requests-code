程序目录：

`models`: This module contains the primary objects that power Requests.



部分设计思想：

在`models`类内，

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



在`session.py`文件中

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



