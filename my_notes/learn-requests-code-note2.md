---
title: Python库requests源码阅读笔记 - 学习收获篇
date: 2023-02-09 12:49:05
tags: python requests 
categories: python 
---

# requests源码阅读笔记

## requests的使用方面

## 1 

可将`Response`实例直接置于条件判断中，转为bool为是否为200ok

源码：

```python
    def __bool__(self):
        """Returns True if :attr:`status_code` is less than 400.

        This attribute checks if the status code of the response is between
        400 and 600 to see if there was a client error or a server error. If
        the status code, is between 200 and 400, this will return True. This
        is **not** a check to see if the response code is ``200 OK``.
        """
        return self.ok
```

但我还是偏向于`raise_for_status()`方法

## 2

关于hook触发时机在

```python
    def send(self, request, **kwargs):
        """Send a given PreparedRequest.

        :rtype: requests.Response
        """
		...
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

```

的`dispatch_hook`函数内

```python
def dispatch_hook(key, hooks, hook_data, **kwargs):
    """Dispatches a hook dictionary on a given piece of data."""
    hooks = hooks or {}
    hooks = hooks.get(key)
    if hooks:
        if hasattr(hooks, "__call__"):
            hooks = [hooks]
        for hook in hooks:
            _hook_data = hook(hook_data, **kwargs)
            if _hook_data is not None:
                hook_data = _hook_data
    return hook_data
```

并可以给hook附带参数

hook的使用参见资料

## 3

添加重试次数的方法

```
:param max_retries: The maximum number of retries each connection
    should attempt. Note, this applies only to failed DNS lookups, socket
    connections and connection timeouts, never to requests where data has
    made it to the server. By default, Requests does not retry failed
    connections. If you need granular control over the conditions under
    which we retry a request, import urllib3's ``Retry`` class and pass
    that instead.

Usage::

  >>> import requests
  >>> s = requests.Session()
  >>> a = requests.adapters.HTTPAdapter(max_retries=3)
  >>> s.mount('http://', a)
```

https请求请使用`s.mount('https://', a)`

>关于重试：每个连接应该尝试的最大重试次数。注意，这只适用于DNS查找失败、套接字连接和连接超时，永远不会适用于数据已经到达服务器的请求。默认情况下，请求不会重试失败的连接。如果你需要精确控制重试请求的条件，导入urllib3的`` Retry ``类并传递它。

还有其他参见结构篇中写到。

## 4

在需要的数据远小于收到数据大小的时候可这样使用：

```python
with requests.get("https://www.baidu.com") as response:
	data = response.status_code
    ...  # get the data you want
print(data)
...  # use the data
```

可以确保大的数据被释放，防止后面用不到反而占用空间。

## 其他方面

## 1

```python
from urllib3.util import parse_url
url = "http://user:pass@www.baidu.com:77/path1?arg1=1&arg2=2#frag"
scheme, auth, host, port, path, query, fragment = parse_url(url)
print(scheme, auth, host, port, path, query, fragment)
>>> http user:pass www.baidu.com 77 /path1 arg1=1&arg2=2 frag
```

url分为

```
scheme://[<user>:<password>@]host[:port] / path /query#fragment
```

方括号代表可选

scheme：通信协议

fragment：锚点

## 2

def isinstance(__obj: object,
               __class_or_tuple: type | Tuple[type | Tuple[Any, ...], ...])
  -> bool

第二个参数可以使用元组包含类型

## 3

一对多的字典添加元素用`register`这个词  删除就用`deregister`

```python
def register_hook(self, event, hook):
    """Properly register a hook."""

    if event not in self.hooks:
        raise ValueError(f'Unsupported event specified, with event name "{event}"')

    if isinstance(hook, Callable):
        self.hooks[event].append(hook)
    elif hasattr(hook, "__iter__"):
        self.hooks[event].extend(h for h in hook if isinstance(h, Callable))
```

## 4

IDNA规范（Internationalized Domain Names in Applications）

用于支持其他语言例如中文，日文域名的实现提出的规范

[pypi](https://pypi.org/project/idna/)

Basic functions are simply executed:

```
>>> import idna
>>> idna.encode('ドメイン.テスト')
b'xn--eckwd4c7c.xn--zckzah'
>>> print(idna.decode('xn--eckwd4c7c.xn--zckzah'))
ドメイン.テスト
```

## 5

上下文管理器在requests里面的使用

```python
def __enter__(self):
    return self

def __exit__(self, *args):
    self.close()
```

使用例：

```python
with Session() as session:
    rep = session.get(url)
```

## 6

`__getstate__` 和`__setstate__`魔法方法

用于序列化

`pickle.dumps(obj)`序列化对象obj的属性，若该对象的类没有`__getstate__` 方法， 则属性内容由`__dict__` 提供，否则由`__getstate__` 提供，使用`__getstate__` 可自定义序列化对象的属性或其他任意内容；

> 注意：`__getstate__` 必须返回一个字典,

`pickle.loads(bytes)`反序列化时，会调用`__setstate__`方法，该方法所需参数为序列化时`__dict__` 或`__setstate__`提供的，前者提供为字典格式，后者提供格式具体看其返回值。

使用例：

```python
    def __init__(self):
        self._content_consumed = False
        
	def __getstate__(self):
        # Consume everything; accessing the content attribute makes
        # sure the content has been fully read.
        if not self._content_consumed:
            self.content

        return {attr: getattr(self, attr, None) for attr in self.__attrs__}

    def __setstate__(self, state):
        for name, value in state.items():
            setattr(self, name, value)

        # pickled objects do not have .raw
        setattr(self, "_content_consumed", True)
        setattr(self, "raw", None)
```

其中的`__attrs__`并不是魔法变量，作者定义的类静态变量

## 7

`__nonzero__`是在python2中判断语句中触发的，python3中被`__bool__`取代

[python2相关文档](https://docs.python.org/2/reference/datamodel.html#object.__nonzero)

[python3相关文档](https://docs.python.org/3.0/reference/datamodel.html#object.__bool__)

```python
class A:

    def __nonzero__(self):
        print("__nonzero__")
        return True

    def __bool__(self):
        print("__bool__")
        return True


if __name__ == '__main__':
    if A():
        ...
```

## 8

类内的`is_xxx`的表示状态的变量可以改为`property`属性值

可以减少一个成员变量，以防`__init__`函数内定义过乱

源码示例：

```python
    @property
    def is_redirect(self):
        """True if this Response is a well-formed HTTP redirect that could have
        been processed automatically (by :meth:`Session.resolve_redirects`).
        """
        return "location" in self.headers and self.status_code in REDIRECT_STATI

    @property
    def is_permanent_redirect(self):
        """True if this Response one of the permanent versions of redirect."""
        return "location" in self.headers and self.status_code in (
            codes.moved_permanently,
            codes.permanent_redirect,
        )
```

## 9

`charset_normalizer` 和 `chardet`库

用于判断bytes对应的编码

```python
try:
    import chardet
except ImportError:
    import charset_normalizer as chardet

text = b'\xe4\xbd\xa0\xe5\xa5\xbd'
print(chardet.detect(text)["encoding"])

>>> utf-8
```

## 10

尽量使用 `var is None`或者`var is not None`意思明确

## 11

`setdefault`配合省略关键词参数`**kwargs`很方便

示例：

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
		...
```

## 12

连接池概念

## 13

CA以及SSL证书概念

验证证书流程

证书概念：证书用于验证网站合法性，和纸质证书概念相同，电子证书也用于查看网站是否安全。

如何验证证书：

[参考资料1](https://blog.csdn.net/liangweimei/article/details/111677290)    [参考资料2](https://blog.csdn.net/qwe1765667234/article/details/124554074)

## 14

threading.local()

获取`ThreadLocal`对象

不同的线程访问这个对象使用的空间都是线程自己的空间。

## 15

如果一个变量为空就设置为某默认值

有以下写法：

```
hooks = hooks or {}
```

## 16

判断变量是否为函数

```python
if hasattr(hooks, "__call__"):
    ...
```

## 17

从kwargs中取值：

```python
def custom_function(**kwargs):
    foo = kwargs.pop('foo', None)
    bar = kwargs.pop('bar', None)
    ...

def custom_function2(**kwargs):
    foo = kwargs.get('foo')
    bar = kwargs.get('bar')
    ...
```

使用哪个取决于代码需求，没有最佳实践

## 18

`@contextlib.contextmanager`上下文修饰器

类似于类的上下文修饰器，只不过此时上下文处于一个函数中

使用例如下

```python
import contextlib
 
@contextlib.contextmanager
def test1():
    print("前面的部分")
    yield
    print("后面的部分")
 
if __name__ == '__main__':
    with test1():
        print("中间执行的代码块")
```

## 19

`frozenset()`内置函数

返回一个冻结的集合，冻结后集合不能再添加或删除任何元素。

语法：

```
class frozenset([iterable])
```

>为什么需要冻结的集合（即**不可变的集合**）呢？因为在集合的关系中，有**集合的中的元素是另一个集合**的情况，但是**普通集合（set）本身是可变的**，那么它的实例就**不能放在另一个集合中**（set中的元素必须是不可变类型）。
>
>所以，frozenset提供了不可变的集合的功能，当**集合不可变**时，它就**满足了作为集合中的元素的要求**，就可以放在另一个集合中了。

## 20

一个简单的猜测编码

```python
# Null bytes; no need to recreate these on each call to guess_json_utf
_null = "\x00".encode("ascii")  # encoding to ASCII for Python 3
_null2 = _null * 2
_null3 = _null * 3


def guess_json_utf(data):
    """
    :rtype: str
    """
    # JSON always starts with two ASCII characters, so detection is as
    # easy as counting the nulls and from their location and count
    # determine the encoding. Also detect a BOM, if present.
    sample = data[:4]
    if sample in (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE):
        return "utf-32"  # BOM included
    if sample[:3] == codecs.BOM_UTF8:
        return "utf-8-sig"  # BOM included, MS style (discouraged)
    if sample[:2] in (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE):
        return "utf-16"  # BOM included
    nullcount = sample.count(_null)
    if nullcount == 0:
        return "utf-8"
    if nullcount == 2:
        if sample[::2] == _null2:  # 1st and 3rd are null
            return "utf-16-be"
        if sample[1::2] == _null2:  # 2nd and 4th are null
            return "utf-16-le"
        # Did not detect 2 valid UTF-16 ascii-range characters
    if nullcount == 3:
        if sample[:3] == _null3:
            return "utf-32-be"
        if sample[1:] == _null3:
            return "utf-32-le"
        # Did not detect a valid UTF-32 ascii-range character
    return None
```



