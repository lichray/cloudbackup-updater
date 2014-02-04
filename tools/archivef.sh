#!/bin/sh
set -e

path_tmpl="$1"
filename_tmpl=$(basename "$path_tmpl")
dir_tmpl="${filename_tmpl%*.tar.*}"
rel=$(git describe --tags)
path=$(printf "$path_tmpl" $rel)
dir=$(printf "$dir_tmpl" $rel)

git archive --prefix="$dir/" -o "$path" HEAD
