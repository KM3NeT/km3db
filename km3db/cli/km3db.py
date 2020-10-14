#!/usr/bin/env python3
"""
Command line access to the KM3NeT DB web API.

Usage:
    km3db URL
    km3db (-h | --help)
    km3db --version

Options:
    URL         The URL, starting from the database website's root.
    -h --help   Show this screen.

Example:

    km3db "streamds/runs.txt?detid=D_ARCA003"

"""
import km3db
from docopt import docopt


def main():
    args = docopt(__doc__, version=km3db.version)
    db = km3db.DBManager()
    result = db.get(args["URL"])
    if result is not None:
        print(result)
