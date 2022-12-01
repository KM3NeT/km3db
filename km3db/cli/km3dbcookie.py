#!/usr/bin/env python3
"""
Generate a cookie for the KM3NeT Oracle Web API.

Usage:
    km3dbcookie [-B | -C] [-o COOKIEFILE]
    km3dbcookie (-h | --help)
    km3dbcookie --version

Options:
    -B             Request the cookie for a class B network (12.23.X.Y).
    -C             Request the cookie for a class C network (12.23.45.Y).
    -o COOKIEFILE  Filepath to store the cookiefile [default: ~/.km3netdb_cookie].
    -h --help   Show this screen.

Example:

    km3dbcookie -B

"""
import km3db
from docopt import docopt


def main():
    args = docopt(__doc__, version=km3db.version)
    print(args)
    if args["-B"]:
        db = km3db.DBManager(network_class="B")
    elif args["-C"]:
        db = km3db.DBManager(network_class="C")
    else:
        db = km3db.DBManager()
    db.session_cookie