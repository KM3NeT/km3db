#!/usr/bin/env python3
"""
Retrieves DETX files from the database.

Usage:
    detx [options] DET_ID
    detx [options] DET_ID RUN
    detx (-h | --help)
    detx --version

Options:
    DET_ID        The detector ID (e.g. 49)
    RUN           The run ID.
    -p P_CAL      Position calibration ID [default: 0].
    -r R_CAL      Rotation calibration ID [default: 0].
    -t T_CAL      Time calibration ID [default: 0].
    -v VERSION    DETX file format version [default: 2].
    -o OUT        Output folder or filename.
    -h --help     Show this screen.

Example:

    detx 49 8220  # retrieve the calibrated DETX for run 8220 of ORCA6

"""
import km3db
from km3db.logger import log
from docopt import docopt


def main():
    args = docopt(__doc__, version=km3db.version)

    try:
        det_id = int(args["DET_ID"])
    except ValueError:
        log.error("Please proivde a valid detector ID (e.g. 49).")
        return

    if args["RUN"] is not None:
        detx = km3db.tools.detx_for_run(
            det_id, int(args["RUN"]), version=int(args["-v"])
        )
    else:
        detx = km3db.tools.detx(
            det_id,
            pcal=args["-p"],
            rcal=args["-r"],
            tcal=args["-t"],
            version=int(args["-v"]),
        )

    if detx is None:
        log.error("No detx found.")
        return

    if args["-o"]:
        with open(args["-o"], "w") as fobj:
            fobj.write(detx)
    else:
        try:
            print(detx)
        except BrokenPipeError:
            pass
