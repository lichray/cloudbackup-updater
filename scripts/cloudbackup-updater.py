#!/usr/bin/env python

import os
import signal
import sys
import time
from getopt import getopt
import logging
import logging.handlers
import subprocess
from contextlib import contextmanager
from string import Template

import daemon
import daemon.pidfile
import requests

import dotlock
import pkgup


VERSION_FILE_TMPL = (
    '{}/windows/version.txt'
)

LOCK_FILE_TMPL = (
    '{}/backup-running.lock'
)

KEY_FILE_TMPL = (
    '{}/debian/agentrepo.key'
)

LOG = logging.getLogger()


def keep_upgraded(interval, url):
    while 1:
        try_upgrade(url)
        time.sleep(interval * 60)


def try_upgrade(url):
    try:
        vr_txt = remote_version(url)
        vr = version_triple(vr_txt)

    except ValueError:
        raise RuntimeError("remote version.txt is malformed: %s" % vr_txt)

    except Exception as e:
        LOG.exception(e)

    if pkgup.PKG_MGMT == 'yum':
        get_repository = lambda: pkgup.Repository(name='drivesrvr')
        add_repository = add_yum_repository

    elif pkgup.PKG_MGMT == 'apt':
        get_repository = lambda: pkgup.Repository(name='serveragent')
        add_repository = lambda u: add_apt_repository('serveragent', u)

    try:
        get_repository()

    except pkgup.NoSuchRepo:
        add_repository(url)

    repo = get_repository()
    pkg = repo.package('driveclient')
    backup_lock = dotlock.DotLock(
        LOCK_FILE_TMPL.format('/var/cache/driveclient'))

    try:
        vl_txt = pkg.installed_version()

    except pkgup.NotInstalled:
        LOG.info('Agent not installed')
        pkg.install()
        LOG.info('%s is newly installed', pkg.installed_nvra())

    else:
        if version_triple(vl_txt) < vr:
            LOG.info('Agent version is behind: %s', vr_txt)
            with backup_lock:
                LOG.info('Agent is idle; updating...')
                with driveclient_not_running():
                    pkg.update()
            LOG.info('%s is upgraded', pkg.installed_nvra())


@contextmanager
def driveclient_not_running():
    subprocess.call(['service', 'driveclient', 'stop'])
    LOG.info('Agent brought down')
    yield
    subprocess.call(['service', 'driveclient', 'start'])
    LOG.info('Agent brought up')


def add_yum_repository(url):
    p = subprocess.Popen(['yum-config-manager',
                          '--add-repo',
                          '{}/redhat/drivesrvr.repo'.format(url)],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)

    out = p.communicate()[0]

    if p.returncode == 0:
        LOG.info('Adding yum repository:\n%s', out)

    else:
        LOG.error('Failed to add yum repo:\n%s', out)
        sys.exit(1)


def add_apt_repository(name, url):
    add_apt_key(KEY_FILE_TMPL.format(url))

    with open('/etc/apt/sources.list.d/driveclient.list', 'w') as fp:
        fp.write('deb [arch=amd64] {}/debian/ {} main'.format(url, name))
        LOG.info('Adding apt repository')


def add_apt_key(uri):
    resp = requests.get(uri)

    if not resp.ok:
        raise RuntimeError('Failed to get keyfile %r' % uri)

    p = subprocess.Popen(['apt-key', 'add', '-'],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)

    out = p.communicate(resp.content)

    if p.returncode == 0:
        LOG.info('Adding apt key')

    else:
        LOG.error('Failed to add apt key:\n%s', out)
        sys.exit(1)


def remote_version(url):
    remote_version_file = VERSION_FILE_TMPL.format(url)
    resp = requests.get(remote_version_file)

    if not resp.ok:
        raise RuntimeError('Failed to communicate %r' % remote_version_file)

    return resp.content


def version_triple(version_text):
    return map(int, version_text.split('.'))


def main_quit(signum=0, frame=None):
    if signum:
        LOG.info('Exit on signal %d' % signum)

    sys.exit()


def main(cmd, *args):
    daemon_mode = False
    interval = 60
    cmd_name = os.path.basename(cmd)
    logfile = '/var/log/cloudbackup-updater.log'
    pidfile = '/var/run/cloudbackup-updater.pid'
    remote_prefix = 'http://agentrepo.drivesrvr.com'

    try:
        for k, v in getopt(args, 'di:l:r:vh')[0]:
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

    except Exception as e:
        print >> sys.stderr, '%s: %s' % (cmd_name, e)
        sys.exit(2)

    fmt = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')

    if daemon_mode:
        with daemon.DaemonContext(
                umask=077,
                pidfile=daemon.pidfile.TimeoutPIDLockFile(pidfile),
                signal_map={
                    signal.SIGTERM: main_quit,
                }):
            log_handler = logging.handlers.RotatingFileHandler(
                logfile, maxBytes=4096, backupCount=5)
            log_handler.setFormatter(fmt)
            LOG.addHandler(log_handler)

            keep_upgraded(interval, remote_prefix)

    else:
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(fmt)
        LOG.addHandler(log_handler)

        try:
            try_upgrade(remote_prefix)

        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main(*sys.argv)
