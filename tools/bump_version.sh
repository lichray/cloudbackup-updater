#!/bin/sh
set -e

rel=$(git describe --tags)

if command -v dch >/dev/null 2>&1; then
	dch -v $rel-2 -m 'ad-hoc testing'
else
	sed -i.bak 's/^\(Version: *\).*$/\1'$rel'/' redhat/*.spec
fi
