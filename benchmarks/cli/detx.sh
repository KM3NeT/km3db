#!/usr/bin/env bash
# set -euo pipefail

TMP_FILE=delete_me.detx

detx -h

detx 75 9209
detx -o $TMP_FILE 75 9209

detx -t A02973944 75
detx -t A02973944 -o $TMP_FILE 75

rm $TMP_FILE
