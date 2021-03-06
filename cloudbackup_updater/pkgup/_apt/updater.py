"""
Package installation or upgrade for DEB-based systems
"""

import os
import sys
import gc
import logging

import apt
import apt_pkg

from cloudbackup_updater.ctxsoft import *


LOG = logging.getLogger()


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
                 if repo.desc_uri.endswith('/%s/InRelease' % name)
                 or repo.desc_uri.endswith('/%s/Release.gpg' % name)]

        if not repos:
            raise NoSuchRepo(name)

        self.__cache = apt.Cache()

        # apt.Cache leaks file descriptor.  We collect the old
        # one after a new one is created.
        # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=745487
        gc.collect()

    def package(self, name):
        try:
            self.__cache.update()

        except Exception, e:
            # May be other repository's failure
            LOG.exception(e)
            LOG.info('Update continued')

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

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        self.__cache.commit()
        self.__sync_cache()

    def install(self):
        @with_(self)
        def _as():
            self.__pkg.mark_install()

    def update(self, to):
        @with_(self)
        def _as():
            self.__pkg.mark_upgrade()
