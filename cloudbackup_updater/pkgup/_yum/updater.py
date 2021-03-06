"""
Package installation or upgrade for RPM-based systems
"""

import sys
import subprocess
import logging

import yum
from yum.rpmtrans import RPMBaseCallback
import urlgrabber

from cloudbackup_updater.ctxsoft import *


LOG = logging.getLogger()


class NotInstalled(Exception):
    pass


class NoSuchRepo(Exception):
    pass


def _broken_yum():
    return yum.__version_info__ < (3, 2, 29)


class GPGKeyTrustedYumBase(yum.YumBase):
    def _askForGPGKeyImport(self, po, userid, hexkeyid):
        return True


class Repository(object):
    def __init__(self, name):
        self.__yb = GPGKeyTrustedYumBase()
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

    def __run_cmdline(self, command, version=None):
            LOG.debug('Running command line')

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
        if not _broken_yum():
            @with_(self)
            def _as():
                self.__yb.install(name=self.__name)

        else:
            self.__run_cmdline('install')

    def update(self, to):
        if not _broken_yum():
            @with_(self)
            def _as():
                self.__yb.update(name=self.__name)

        else:
            self.__run_cmdline('update', version=to)


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
