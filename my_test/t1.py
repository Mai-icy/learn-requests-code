#!/usr/bin/python
# -*- coding:utf-8 -*-


def urlparse_test_1():
    from urllib.parse import urlparse
    url = "https://www.baidu.com:11451/test1/test2?arg1=1&arg2=2"

    p = urlparse(url)
    print(p)

    from requests.models import RequestEncodingMixin
    t1 = RequestEncodingMixin()
    t1.url = url
    print(t1.path_url)


def to_key_val_list_test1():
    from requests.utils import to_key_val_list

    var = [('key', 'val', "123")]
    var2 = {"wa": "1", "weq": " qwe"}

    print(to_key_val_list(var2))


def parse_url_test_1():
    from urllib3.util import parse_url
    url = "http://user:pass@www.baidu.com:77/path1?arg1=1&arg2=2#frag"
    scheme, auth, host, port, path, query, fragment = parse_url(url)
    print(scheme, auth, host, port, path, query, fragment)


def chardet_test_1():
    try:
        import chardet
    except ImportError:
        import charset_normalizer as chardet

    text = b'\xe4\xbd\xa0\xe5\xa5\xbd'

    print(chardet.detect(text)["encoding"])


def with_test_1():
    with requests.get("https://www.baidu.com") as response:
        data = response.status_code
        ...  # get the data you want
    print(data)


def api_test_2():
    import requests

    session = requests.session()
    response = session.get("https://www.baidu.com")

    data = response.text
    print(data)

if __name__ == '__main__':
    ...
    import requests

    # requests.get("http://user:pass@www.baidu.com:77/path1?arg1=1&arg2=2#frag")
    # urlparse_test_1()
    # to_key_val_list_test1()
    # parse_url_test_1()
    # chardet_test_1()
    api_test_2()
