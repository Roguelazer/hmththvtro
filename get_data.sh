#!/bin/bash

set -e

CONGRESSROOT="govtrack.us::govtrackdata/congress/"
FIRST_CONGRESS=111
LEGISLATORS_CURRENT_YAML="govtrack.us::govtrackdata/congress-legislators/legislators-current.yaml"
LEGISLATORS_HISTORICAL_YAML="govtrack.us::govtrackdata/congress-legislators/legislators-historical.yaml"

RSYNC_ARGS="-a"

usage() {
    echo "$0 /path/to/writeable/data/directory"
}

datadir="$1"

if [ -z "$datadir" ]; then
    usage
    exit 2
fi

if [ ! -e "$datadir" ]; then
    mkdir "$datadir"
fi

mkdir -p "$datadir/hr"
mkdir -p "$datadir/votes"

if type md5sum >/dev/null 2>&1 ; then
    md5sum=md5sum
elif type md5  >/dev/null 2>&1 ; then
    md5sum=md5
else
    echo >&2 "no md5sum/md5 found"
    exit 1
fi

get_yaml() {
    src="$1"
    target="$2"
    json_target="$3"
    if [ -e "${target}.md5" ]; then
        old_md5="$(cat "${target}.md5")"
    else
        old_md5=""
    fi
    rsync $RSYNC_ARGS "$src" "$target"
    new_md5="$($md5sum "$target")"
    if [ ! -e "${json_target}" ] || [ "$old_md5" != "$new_md5" ]; then
        env/bin/python yaml2json.py "$target" "$json_target"
    fi
    echo "$new_md5" > "${target}.md5"
}

get_yaml "$LEGISLATORS_CURRENT_YAML" "${datadir}/legislators-current.yaml" "${datadir}/legislators-current.json"
get_yaml "$LEGISLATORS_HISTORICAL_YAML" "${datadir}/legislators-historical.yaml" "${datadir}/legislators-historical.json"

for congressnum in $(rsync --list-only "$CONGRESSROOT" | cut -d" " -f 12-); do
    if ! [[ "$congressnum" =~ ^[0-9]+$ ]] ; then
        continue
    fi
    if [ "$congressnum" -ge $FIRST_CONGRESS ]; then
        rsync $RSYNC_ARGS --include="**/data.json" --include="hr*" --exclude="*" "$CONGRESSROOT/$congressnum/*/hr/hr*" "$datadir/hr/$congressnum"
        rsync $RSYNC_ARGS --include="**/data.json" --include="h*" --exclude="*" "$CONGRESSROOT/$congressnum/votes/*/h*" "$datadir/votes/$congressnum"
    fi
done
