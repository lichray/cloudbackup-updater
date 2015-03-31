import errno
import fcntl
import os
import stat


class Lockf(object):

    def __init__(self, fh):
        self.__fh = fh

    def __enter__(self):
        """
        Context manager support.
        """

        self.acquire()
        return self

    def __exit__(self, *_exc):
        """
        Context manager support.
        """

        self.release()

    def __repr__(self):
        return repr(self.__fh)

    def acquire(self):
        fcntl.lockf(self.__fh, fcntl.LOCK_EX)

    def try_acquire(self):
        try:
            fcntl.lockf(self.__fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True

        except IOError, e:
            if e.errno == errno.EAGAIN or e.errno == errno.EACCES:
                return False
            else:
                raise

    def release(self):
        fcntl.lockf(self.__fh, fcntl.LOCK_UN)
