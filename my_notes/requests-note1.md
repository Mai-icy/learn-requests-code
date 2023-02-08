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

https请求请使用`s.mount('http://', a)`

>关于重试：每个连接应该尝试的最大重试次数。注意，这只适用于DNS查找失败、套接字连接和连接超时，永远不会适用于数据已经到达服务器的请求。默认情况下，请求不会重试失败的连接。如果你需要精确控制重试请求的条件，导入urllib3的`` Retry ``类并传递它。

