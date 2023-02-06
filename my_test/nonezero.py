#!/usr/bin/python
# -*- coding:utf-8 -*-


class A:

    def __nonzero__(self):
        print("__nonzero__")
        return True

    def __bool__(self):
        print("__bool__")
        return True


if __name__ == '__main__':
    a = A()

    if a:
        ...


