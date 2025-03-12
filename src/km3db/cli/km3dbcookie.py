#!/usr/bin/env python3
"""
Generate a cookie for the KM3NeT Oracle Web API.

Usage:
    km3dbcookie [-B | -C]
    km3dbcookie (-h | --help)
    km3dbcookie --version

Options:
    -B             Request the cookie for a class B network (12.23.X.Y).
    -C             Request the cookie for a class C network (12.23.45.Y).
    -h --help   Show this screen.

Example:

    $ km3dbcookie -B
    Please enter your KM3NeT DB username: tgal
    Password:
    Cookie saved as '/Users/tamasgal/.km3netdb_cookie'
    $ cat /Users/tamasgal/.km3netdb_cookie
    .in2p3.fr	TRUE	/	TRUE	0	sid	_tgal_131.188_70b78042c03a434594b041073484ce23


"""
import km3db
from docopt import docopt


def main():
    args = docopt(__doc__, version=km3db.version)
    if args["-B"]:
        db = km3db.DBManager(network_class="B")
    elif args["-C"]:
        db = km3db.DBManager(network_class="C")
    else:
        db = km3db.DBManager()
    db.request_session_cookie()

    print("Cookie saved as '{}'".format(km3db.core.COOKIE_FILENAME))
