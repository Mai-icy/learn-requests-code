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

