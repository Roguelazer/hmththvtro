#!/bin/bash

set -e

CONGRESSROOT="govtrack.us::govtrackdata/congress/"
FIRST_CONGRESS=111
LEGISLATORS_CURRENT_YAML="govtrack.us::govtrackdata/congress-legislators/legislators-current.yaml"
LEGISLATORS_HISTORICAL_YAML="govtrack.us::govtrackdata/congress-legislators/legislators-historical.yaml"

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

rsync -a "$LEGISLATORS_CURRENT_YAML" "$datadir/"
rsync -a "$LEGISLATORS_HISTORICAL_YAML" "$datadir/"

for congressnum in $(rsync --list-only "$CONGRESSROOT" | cut -d" " -f 12-); do
    if ! [[ "$congressnum" =~ ^[0-9]+$ ]] ; then
        continue
    fi
    if [ "$congressnum" -ge $FIRST_CONGRESS ]; then
        rsync -a --include="**/data.json" --include="hr*" --exclude="*" "$CONGRESSROOT/$congressnum/*/hr/hr*" "$datadir/hr/$congressnum"
        rsync -a --include="**/data.json" --include="h*" --exclude="*" "$CONGRESSROOT/$congressnum/votes/*/h*" "$datadir/votes/$congressnum"
    fi
done
