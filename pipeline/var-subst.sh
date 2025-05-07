#!/bin/bash
T=$(mktemp)
(echo "cat <<EOF >$1"; cat $1; echo "EOF";) > $T
. $T
rm $T