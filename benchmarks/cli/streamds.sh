#!/usr/bin/env bash
# set -euo pipefail

streamds -h

streamds list

streamds get detectors

streamds info detectors

streamds get detectors -o detectors.csv

streamds get toashort detid=D0ORCA010 minrun=13000 maxrun=13000 -g RUN -o KM3NeT_00000100_toashort.h5
