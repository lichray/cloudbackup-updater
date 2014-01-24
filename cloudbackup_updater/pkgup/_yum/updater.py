"""
Package installation or upgrade for RPM-based systems
"""

import sys
import subprocess

import yum
from yum.rpmtrans import RPMBaseCallback
import urlgrabber

from cloudbackup_updater.ctxsoft import *


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

    def __search(self):
        return self.__yb.rpmdb.searchNevra(name=self.__name)

    def __installed(self):
        pkgs = self.__search()

        if not pkgs:
            raise NotInstalled(self.__name)

        return pkgs[0]

    def __try_cmdline_if_no_action_taken_for(self, command, version=None):
        pkgs = self.__search()
        if not pkgs or (version is not None and pkgs[0].version != version):
            p = subprocess.Popen(['yum', command, "--disablerepo='*'",
                                  '--enablerepo=' + ','.join(
                                      map(lambda r: r.name,
                                          self.__yb.repos.listEnabled())),
                                  '-y', '-q', self.__name],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)

            out = p.communicate()[0]

            if p.returncode != 0:
                raise RuntimeError('yum command failed:\n' + out)

    def installed_nvra(self):
        p = self.__installed()
        return '%s-%s-%s.%s' % (p.name, p.version, p.release, p.arch)

    def installed_version(self):
        return self.__installed().version

    def __enter__(self):
        self.__yb.repos.doSetup()

    def __exit__(self, type, value, traceback):
        self.__yb.resolveDeps()
        self.__yb.processTransaction(rpmDisplay=ProgressBar())

    def install(self):
        @with_(self)
        def _as():
            self.__yb.install(name=self.__name)

        self.__try_cmdline_if_no_action_taken_for('install')

    def update(self, to):
        @with_(self)
        def _as():
            self.__yb.update(name=self.__name)

        self.__try_cmdline_if_no_action_taken_for('update', version=to)


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
