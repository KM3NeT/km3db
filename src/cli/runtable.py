# Filename: runtable.py
"""
Prints the run table for a given detector ID.

Usage:
    runtable [options] DET_ID
    runtable (-h | --help)
    runtable --version

Options:
    -h --help           Show this screen.
    -c                  Compact view.
    -n RUNS             Number of runs.
    -r FROM_RUN-TO_RUN  Range of runs (example: 3100-3200).
    -t TARGET           Job target (run/on/off)
    -s REGEX            Regular expression to filter the runsetup name/id.
    DET_ID              Detector ID (eg. D_ARCA001).

"""

import re
import sys

import km3db
from km3db.logger import log

__author__ = "Tamas Gal"
__copyright__ = "Copyright 2018, Tamas Gal and the KM3NeT collaboration."
__credits__ = []
__license__ = "MIT"
__maintainer__ = "Tamas Gal"
__email__ = "tgal@km3net.de"
__status__ = "Development"


def runtable(
    det_id, n=5, run_range=None, target=None, compact=False, sep="\t", regex=None
):
    """Print the run table of the last `n` runs for given detector"""
    runs = km3db.StreamDS(container="nt").get("runs", detid=det_id)

    if run_range is not None:
        try:
            from_run, to_run = [int(r) for r in run_range.split("-")]
        except ValueError:
            log.critical("Please specify a valid range (e.g. 3100-3200)!")
            raise SystemExit
        else:
            runs = [r for r in runs if from_run <= r.run <= to_run]

    if regex is not None:
        try:
            pattern = re.compile(regex)
        except re.error:
            log.error("Invalid regex!")
            return
        else:
            runs = [
                r
                for r in runs
                if re.match(pattern, r.runsetupname) or re.match(pattern, r.runsetupid)
            ]

    if target is not None:
        runs = [r for r in runs if r.jobtarget == target.capitalize()]

    if n is not None:
        runs = runs[-n:]

    if not runs:
        log.warning("No runs found.")
        return

    if compact:
        attributes = ["run", "runsetupname"]
        header = sep.join(attributes)

        def lineformatter(entry):
            return sep.join([str(getattr(entry, attr)) for attr in attributes])

    else:
        header = sep.join(runs[0]._fields)  # the dataset is homogenious

        def lineformatter(entry):
            return sep.join(map(str, entry))

    print(header)
    for entry in runs:
        print(lineformatter(entry))


def main():
    from docopt import docopt

    args = docopt(__doc__, version=km3db.version)

    try:
        n = int(args["-n"])
    except TypeError:
        n = None

    runtable(
        args["DET_ID"],
        n=n,
        run_range=args["-r"],
        target=args["-t"],
        regex=args["-s"],
        compact=args["-c"],
    )
