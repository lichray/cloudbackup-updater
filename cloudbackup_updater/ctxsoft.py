"""
Give py24 some PEP 343 support.
"""


class closing(object):
    def __init__(self, resource):
        self.__resource = resource

    def __enter__(self):
        return self.__resource

    def __exit__(self, *exc_info):
        self.__resource.close()
