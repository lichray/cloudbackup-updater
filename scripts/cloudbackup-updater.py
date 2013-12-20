#!/usr/bin/env python

import os
import signal
import sys
import time
from getopt import getopt
import logging
import subprocess
from contextlib import contextmanager

import daemon
import requests

import dotlock
import pkgup


VERSION_FILE_TMPL = (
    '{}/windows/version.txt'
)

LOCK_FILE_TMPL = (
    '{}/backup-running.lock'
)

LOG = logging.getLogger()


def main(interval, url):
    while 1:
        try_upgrade(url)
        time.sleep(interval)


def try_upgrade(url):
    try:
        vr_txt = remote_version(url)
        vr = version_triple(vr_txt)

    except ValueError:
        raise RuntimeError("remote version.txt is malformed: %s" % vr_txt)

    except Exception as e:
        LOG.exception(e)

    try:
        pkgup.Repository(name='drivesrvr')

    except pkgup.NoSuchRepo:
        if hasattr(pkgup, 'yum'):
            add_yum_repository(url)

        elif hasattr(pkgup, 'apt'):
            add_apt_repository(url)

    repo = pkgup.Repository(name='drivesrvr')
    pkg = repo.package('driveclient')
    backup_lock = dotlock.DotLock(
        LOCK_FILE_TMPL.format('/var/cache/driveclient' if os.getuid() == 0
                              else expanduser('~/.driveclient')))

    try:
        vl_txt = pkg.installed_version()

    except pkgup.NotInstalled:
        LOG.info('Agent not installed')
        pkg.install()
        LOG.info('Version %s newly installed', pkg.installed_nvra())

    else:
        if version_triple(vl_txt) < vr:
            LOG.info('Agent version is behind: %s', vr_txt)
            with backup_lock:
                LOG.info('Agent is idle; updating...')
                with driveclient_not_running:
                    pkg.update()
            LOG.info('Version %s upgraded', pkg.installed_nvra())


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
        LOG.info('Adding yum repo:\n%s', out)

    else:
        LOG.error('Failed to add yum repo:\n%s', out)
        sys.exit(1)


def remote_version(url):
    remote_version_file = VERSION_FILE_TMPL.format(url)
    req = requests.get(remote_version_file)

    if not req.ok:
        raise RuntimeError('Failed to communicate %r' % remote_version_file)

    return req.content


def version_triple(version_text):
    return map(int, version_text.split('.'))


def main_quit(signum=0, frame=None):
    if signum:
        LOG.info('Exit on signal %d' % signum)

    sys.exit()


if __name__ == '__main__':
    daemon_mode = False
    interval = 60
    cmd_name = os.path.basename(sys.argv[0])
    log_fp = None
    remote_prefix = 'http://agentrepo.drivesrvr.com'

    try:
        for k, v in getopt(sys.argv[1:], 'di:l:r:vh')[0]:
            if k == '-h':
                print '''%s: [options]...
options:
  -d       daemon mode
  -i       interval in minutes (defaults to 60)
  -l       path to log file (defaults to stderr)
  -r       remote repository (built-in)
  -v       verbose logging
  -h       display this help''' % cmd_name
                sys.exit(2)

            elif k == '-v':
                LOG.setLevel(logging.DEBUG)

            elif k == '-d':
                daemon_mode = True

            elif k == '-i':
                interval = int(v)

            elif k == '-l':
                log_fp = open(v, "a")

            elif k == '-r':
                remote_prefix = v

    except Exception as e:
        print >> sys.stderr, '%s: %s' % (cmd_name, e)
        sys.exit(2)

    fmt = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')

    if daemon_mode:
        log_handler = logging.StreamHandler(log_fp)
        log_handler.setFormatter(fmt)
        LOG.addHandler(log_handler)

        with daemon.DaemonContext(
                working_directory=os.curdir,
                stderr=open(log_file, 'a'),
                umask=63,  # 077
                signal_map={
                    signal.SIGTERM: main_quit,
                }):
            main(interval, remote_prefix)

    else:
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(fmt)
        LOG.addHandler(log_handler)

        try:
            try_upgrade(remote_prefix)

        except KeyboardInterrupt:
            pass
