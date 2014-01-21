"""
Package installation or upgrade for RPM-based systems
"""

import sys
from contextlib import contextmanager

import yum
from yum.rpmtrans import RPMBaseCallback
import urlgrabber


class NotInstalled(Exception):
    pass


class NoSuchRepo(Exception):
    pass


class Repository(object):
    def __init__(self, name):
        self.__yb = yum.YumBase()
        self.__yb.repos.disableRepo('*')
        repos = self.__yb.repos.findRepos(name)

        if not repos:
            raise NoSuchRepo(name)

        repos[0].enable()

    def package(self, name):
        return Package(self.__yb, name)


class Package(object):
    def __init__(self, yb, name):
        self.__yb = yb
        self.__name = name

    def __installed(self):
        pkgs = self.__yb.rpmdb.searchNevra(name=self.__name)

        if not pkgs:
            raise NotInstalled(self.__name)

        return pkgs[0]

    def installed_nvra(self):
        p = self.__installed()
        return '%s-%s-%s.%s' % (p.name, p.version, p.release, p.arch)

    def installed_version(self):
        return self.__installed().version

    @contextmanager
    def transaction(self):
        self.__yb.repos.doSetup()
        yield
        self.__yb.resolveDeps()
        self.__yb.processTransaction(rpmDisplay=ProgressBar())

    def install(self):
        with self.transaction():
            self.__yb.install(name=self.__name)

    def update(self):
        with self.transaction():
            self.__yb.update(name=self.__name)


class ProgressBar(RPMBaseCallback):
    def __init__(self):
        RPMBaseCallback.__init__(self)
        self.lastmsg = None
        self.lastpackage = None

    def event(self, package, action,
              te_current, te_total, ts_current, ts_total):
        msg = '%s: %s %s/%s [%s/%s]' % (self.action[action], package,
                                        te_current, te_total,
                                        ts_current, ts_total)

        if msg != self.lastmsg:
            sys.stdout.write(msg)
            sys.stdout.flush()
            sys.stdout.write('\r')
            if te_current == te_total:
                sys.stdout.write('\n')

        self.lastmsg = msg
        self.lastpackage = package

    def scriptout(self, package, msgs):
        if msgs:
            sys.stdout.write(msgs)
