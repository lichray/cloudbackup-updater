try:
    from pkgup.yum.updater import *
    PKG_MGMT = 'yum'

except ImportError:
    from pkgup.apt.updater import *
    PKG_MGMT = 'apt'
