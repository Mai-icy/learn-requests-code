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





