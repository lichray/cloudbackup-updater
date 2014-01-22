"""
Give py24 some PEP 343 support.
"""

import sys


class closing(object):
    def __init__(self, resource):
        self.__resource = resource

    def __enter__(self):
        return self.__resource

    def __exit__(self, *exc_info):
        self.__resource.close()


def with_(ctx):
    def decorator(f):
        target = ctx.__enter__()
        exc = True
        try:
            try:
                if f.func_code.co_argcount:
                    f(target)
                else:
                    f()

            except:
                exc = False
                if not ctx.__exit__(*sys.exc_info()):
                    raise

        finally:
            if exc:
                ctx.__exit__(None, None, None)

    return decorator
