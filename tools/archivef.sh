#!/bin/sh
set -e

path_tmpl="$1"
filename_tmpl=$(basename "$path_tmpl")
dir_tmpl="${filename_tmpl%*.tar.*}"

suffix="${filename_tmpl##*.tar.}"
case "$suffix" in
xz)
	tool=xz
	;;
gz)
	tool=gzip
	;;
bz2)
	tool=bzip2
	;;
*)
	echo "$0: Unknown suffix: $suffix"
	exit 1
esac

rel=$(git describe --tags)
path=$(printf "$path_tmpl" $rel)
dir=$(printf "$dir_tmpl" $rel)

git archive --prefix="$dir/" HEAD | $tool > "$path"
