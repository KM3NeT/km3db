#!/usr/bin/env bash
# set -euo pipefail

streamds -h

streamds list

streamds get detectors

streamds info detectors

streamds get detectors -o detectors.csv

streamds get detectors -o detectors.h5

streamds get detectors -o detectors.h5 -g CITY
