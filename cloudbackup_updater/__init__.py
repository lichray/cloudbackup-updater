#!/usr/bin/env python

import os
import signal
import sys
import time
from getopt import getopt
import logging
import logging.handlers
import subprocess
import urllib2
import random
from string import Template

from ctxsoft import *
import dotlock
import lockf
import pkgup
import pydaemon


VERSION_FILE_TMPL = (
    '%s/version.txt'
)

LOCK_FILE_TMPL = (
    '%s/backup-running.lock'
)

STATE_FILE_TMPL = (
    '%s/auto-upgradable.state'
)

KEY_FILE_TMPL = (
    '%s/debian/agentrepo.key'
)

LOG = logging.getLogger()


def keep_upgraded(interval, url):
    while 1:
        if run_in_process(try_upgrade, url, return_to_wait=True):
            do_wait()
            run_in_process(try_upgrade, url)

        time.sleep(interval * 60)


def run_in_process(f, *args, **kwargs):
    try:
        ef = move_exitfunc()
        pid = os.fork()

        if pid == 0:
            st = 0
            try:
                try:
                    st = f(*args, **kwargs)

                except Exception, e:
                    LOG.exception(e)

            finally:
                sys.exit(st)

        else:
            set_exitfunc(ef)
            _, status = os.waitpid(pid, 0)

            if os.WIFEXITED(status):
                return os.WEXITSTATUS(status)

    except OSError, e:
        LOG.exception(e)


def move_exitfunc():
    try:
        f = sys.exitfunc
        del sys.exitfunc

        return f

    except AttributeError:
        return None


def set_exitfunc(f):
    if f is not None:
        sys.exitfunc = f


def try_upgrade(url, return_to_wait=False):
    vr_txt = remote_version(url).strip()

    try:
        vr = version_triple(vr_txt)

    except ValueError:
        raise RuntimeError("remote version.txt is malformed: %s" % vr_txt)

    except Exception, e:
        LOG.exception(e)

    if pkgup.PKG_MGMT == 'yum':
        get_repository = lambda: pkgup.Repository(name='drivesrvr')
        add_repository = add_yum_repository

    elif pkgup.PKG_MGMT == 'apt':
        get_repository = lambda: pkgup.Repository(name='serveragent')
        add_repository = lambda u: add_apt_repository('serveragent', u)

    try:
        repo = get_repository()

    except pkgup.NoSuchRepo:
        add_repository(url)
        repo = get_repository()

    pkg = repo.package('driveclient')
    cachedir = '/var/cache/driveclient'
    backup_lock = dotlock.DotLock(LOCK_FILE_TMPL % cachedir)
    # rely on __del__ to close the file
    upgrade_state = lockf.Lockf(open(STATE_FILE_TMPL % cachedir, "w"))

    try:
        vl_txt = pkg.installed_version()

    except pkgup.NotInstalled:
        LOG.info('Agent not installed')
        pkg.install()
        LOG.info('%s is newly installed', pkg.installed_nvra())

    else:
        if version_triple(vl_txt) < vr:
            if return_to_wait:
                return 1

            LOG.info('Agent version is behind: %s', vr_txt)

            def update():
                @with_(driveclient_not_running())
                def _as():
                    pkg.update(to=vr_txt)

            if os.path.isdir(cachedir):
                @with_(backup_lock)
                @with_(upgrade_state)
                def _as():
                    LOG.info('Agent is idle; updating...')
                    update()

            else:
                update()

            LOG.info('%s is upgraded', pkg.installed_nvra())

    return 0


class driveclient_not_running(object):
    def __enter__(self):
        subprocess.call(['service', 'driveclient', 'stop'])
        LOG.info('Agent brought down')

    def __exit__(self, type, value, traceback):
        subprocess.call(['service', 'driveclient', 'start'])
        LOG.info('Agent brought up')


def add_yum_repository(url):
    uri = '%s/redhat/drivesrvr.repo' % url
    rfp = urllib2.urlopen(uri)

    if not 200 <= rfp.code < 300:
        raise RuntimeError('Failed to get repo file %r' % uri)

    @with_(closing(open('/etc/yum.repos.d/drivesrvr.repo', 'w')))
    def _as(fp):
        fp.write(rfp.read())
        LOG.info('Adding yum repository')


def add_apt_repository(name, url):
    add_apt_key(KEY_FILE_TMPL % url)

    @with_(closing(open('/etc/apt/sources.list.d/driveclient.list', 'w')))
    def _as(fp):
        fp.write('deb [arch=amd64] %s/debian/ %s main\n' % (url, name))
        LOG.info('Adding apt repository')


def add_apt_key(uri):
    fp = urllib2.urlopen(uri)

    if not 200 <= fp.code < 300:
        raise RuntimeError('Failed to get keyfile %r' % uri)

    p = subprocess.Popen(['apt-key', 'add', '-'],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)

    out = p.communicate(fp.read())[0]

    if p.returncode == 0:
        LOG.info('Adding apt key')

    else:
        LOG.error('Failed to add apt key:\n%s', out)
        sys.exit(1)


def remote_version(url):
    remote_version_file = VERSION_FILE_TMPL % url
    fp = urllib2.urlopen(remote_version_file)

    if not 200 <= fp.code < 300:
        raise RuntimeError('Failed to communicate %r' % remote_version_file)

    return fp.read()


def version_triple(version_text):
    return map(int, version_text.split('.'))


def do_wait():
    # E(x) = 6, Mode(x) = 4, at ~14%, Max(x) ~20
    # 10% ~ 2.2, 25% ~ 3.4, 50% ~ 5.3, 75% ~ 7.8, 90% ~ 10.6
    while True:
        x = random.gammavariate(3., 2.)
        if x < 24.:  # CDF(24) ~ 0.9995
            break
    if os.getenv('CLOUDBACKUP_UPDATER_DEBUG') is None:
        time.sleep(x * 3600)
    else:
        LOG.debug('Wait for %.1f minutes', x)
        time.sleep(x * 60)


def main_quit(signum=0, frame=None):
    if signum:
        LOG.info('Exit on signal %d' % signum)

    sys.exit()


def main_exec(cmd, *args):
    daemon_mode = False
    interval = 60
    cmd_name = os.path.basename(cmd)
    logfile = '/var/log/cloudbackup-updater.log'
    pidfile = '/var/run/cloudbackup-updater.pid'
    remote_prefix = 'http://agentrepo.drivesrvr.com'

    try:
        for k, v in getopt(args, 'di:l:p:r:vh')[0]:
            if k == '-h':
                print Template('''$cmd_name: [options]...
options:
  -d       daemon mode
  -i NUM   interval in minutes (defaults to $interval)
  -l PATH  path to log file (defaults to $logfile)
  -p PATH  path to pid file (defaults to $pidfile)
  -r URI   alternative remote repository
  -v       verbose logging
  -h       display this help''').substitute(locals())
                sys.exit(2)

            elif k == '-v':
                LOG.setLevel(logging.DEBUG)

            elif k == '-d':
                daemon_mode = True

            elif k == '-i':
                interval = int(v)

            elif k == '-l':
                logfile = v

            elif k == '-p':
                pidfile = v

            elif k == '-r':
                remote_prefix = v

    except Exception, e:
        print >> sys.stderr, '%s: %s' % (cmd_name, e)
        sys.exit(2)

    fmt = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')

    if daemon_mode:
        d = pydaemon.Daemon(umask=077, pidfile=pidfile, verbose=0)

        def _as():
            log_handler = logging.handlers.RotatingFileHandler(
                logfile, maxBytes=4096, backupCount=5)
            log_handler.setFormatter(fmt)
            LOG.addHandler(log_handler)

            signal.signal(signal.SIGTERM, main_quit)

            keep_upgraded(interval, remote_prefix)

        d.run = _as
        d.start()

    else:
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(fmt)
        LOG.addHandler(log_handler)

        try:
            try_upgrade(remote_prefix)

        except KeyboardInterrupt:
            pass


def main():
    main_exec(*sys.argv)
