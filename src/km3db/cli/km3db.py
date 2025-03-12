#!/usr/bin/env python3
"""
Command line access to the KM3NeT DB web API.

Usage:
    km3db [options] URL
    km3db (-h | --help)
    km3db --version

Options:
    URL          The URL, starting from the database website's root.
    -b           Binary mode (use it to retrieve e.g. zip files).
    -o FILENAME  File to store the data.
    -h --help    Show this screen.

Example:

    km3db "streamds/runs.txt?detid=D_ARCA003"

"""
import os
import km3db
from docopt import docopt


def main():
    args = docopt(__doc__, version=km3db.version)
    db = km3db.DBManager()
    url = args["URL"]

    is_binary = args["-b"]

    try:
        result = db.get(url, binary=is_binary)
    except UnicodeDecodeError:
        print("The data does not a valid UTF-8 string. Try with '-b'.")
        exit(1)
    else:
        filename = args["-o"]
        if is_binary and filename is None:
            filename = os.path.basename(url)

        if result is not None:
            if filename is not None:
                fmode = "wb" if is_binary else "w"
                with open(filename, fmode) as fobj:
                    fobj.write(result)
                print(f"Data has been written to '{filename}'")
            else:
                print(result)
