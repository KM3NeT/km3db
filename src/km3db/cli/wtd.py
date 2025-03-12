# Filename: wtd.py
"""
Prints information for a given DOM (and detector [O]ID)

Usage:
    wtd DET_ID_OR_OID DOM_ID
    wtd (-h | --help)
    wtd --version

Options:
    DOM_ID          The actual DOM ID.
    DET_ID_OR_OID   Detector ID (like 29) or OID (like D_ARCA003).
    -h --help       Show this screen.

"""

import km3db

__author__ = "Tamas Gal"
__copyright__ = "Copyright 2018, Tamas Gal and the KM3NeT collaboration."
__credits__ = []
__license__ = "MIT"
__maintainer__ = "Tamas Gal"
__email__ = "tgal@km3net.de"
__status__ = "Development"

log = km3db.logger.log


def main():
    from docopt import docopt

    args = docopt(__doc__, version=km3db.version)

    dom_id = int(args["DOM_ID"])
    det = args["DET_ID_OR_OID"]

    try:
        dom = km3db.CLBMap(km3db.tools.todetoid(det)).dom_ids[dom_id]
    except (TypeError, KeyError):
        log.error("No DOM with ID '{}' found in detector '{}'".format(dom_id, det))
        exit(1)
    else:
        for param, value in zip(dom._fields, dom):
            print("{}={}".format(param, value))
