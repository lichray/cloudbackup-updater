import errno
import os
import stat
import time


class DotLock(object):

    def __init__(self, filename):
        self.__filename = filename

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
        return "<%s: %r>" % (self.__class__.__name__, self.__filename)

    def acquire(self):
        """
        Acquire the lock (block forever).
        """

        while True:
            if self.try_acquire():
                break

            else:
                time.sleep(0.1)

    def try_acquire(self):
        try:
            self.__fd = os.open(self.__filename,
                                os.O_CREAT | os.O_EXCL,
                                stat.S_IRUSR)

            return True

        except OSError as e:
            if e.errno == errno.EEXIST:
                return False

            else:
                raise

    def release(self):
        os.close(self.__fd)
        os.unlink(self.__filename)
