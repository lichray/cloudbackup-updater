#!/bin/sh
set -e

rel=$(git describe --tags | sed 's/-/./g')
rev=$(sed -n 's/^Release: *\(.*\)$/\1/p' redhat/*.spec)

if command -v dch >/dev/null 2>&1; then
	dch -v $rel-$rev -m 'ad-hoc testing'
else
	sed -i.bak 's/^\(Version: *\).*$/\1'$rel'/' redhat/*.spec
fi
