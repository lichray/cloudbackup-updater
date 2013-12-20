try:
    from pkgup.yum.updater import *

except ImportError:
    from pkgup.apt.updater import *
