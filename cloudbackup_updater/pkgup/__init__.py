try:
    from _yum.updater import *
    PKG_MGMT = 'yum'

except ImportError:
    from _apt.updater import *
    PKG_MGMT = 'apt'
