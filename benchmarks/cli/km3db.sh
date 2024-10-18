#!/usr/bin/env sh
# set -euo pipefail

mkdir test_downloads

km3db -b -o test_downloads/ doc/testresult/A02964845/testresult_A02964845.zip
unzip testresult_A02964845.zip

km3db -b -o downloads/foo.zip doc/testresult/A02964845/testresult_A02964845.zip
unzip test_downloads/foo.zip

rm -rf test_downloads
