"""
Package installation or upgrade for DEB-based systems
"""

import os
import sys
from contextlib import contextmanager

import apt
import apt_pkg


class NotInstalled(Exception):
    pass


class NoSuchRepo(Exception):
    pass


class Repository(object):
    def __init__(self, name):
        a = apt_pkg.Acquire()
        sl = apt_pkg.SourceList()
        sl.read_main_list()
        sl.get_indexes(a)
        repos = [repo for repo in a.items
                 if repo.desc_uri.endswith('/%s/Release.gpg' % name)]

        if not repos:
            raise NoSuchRepo(name)

        self.__cache = apt.Cache()

    def package(self, name):
        self.__cache.update()
        return Package(self.__cache, name)


class Package(object):
    def __init__(self, cache, name):
        self.__cache = cache
        self.__name = name
        self.__sync_cache()

    def __sync_cache(self):
        self.__cache.open()
        self.__pkg = self.__cache[self.__name]

    def __installed(self):
        if not self.__pkg.is_installed:
            raise NotInstalled(self.__pkg.name)

        return self.__pkg.installed

    def installed_nvra(self):
        return os.path.basename(self.__installed().filename).rsplit('.', 1)[0]

    def installed_version(self):
        return self.__installed().version.split('-', 1)[0]

    @contextmanager
    def transaction(self):
        yield
        self.__cache.commit()
        self.__sync_cache()

    def install(self):
        with self.transaction():
            self.__pkg.mark_install()


    def update(self):
        with self.transaction():
            self.__pkg.mark_upgrade()
