# Filename: runinfo.py
"""
Prints the run table for a given detector ID.

Usage:
    runinfo DET_ID RUN
    runinfo (-h | --help)
    runinfo --version

Options:
    -h --help           Show this screen.
    DET_ID              Detector ID (eg. D_ARCA001).
    RUN                 Run number.

"""
from datetime import datetime, timezone
import km3db

log = km3db.logger.log


def runinfo(run_id, det_id):
    runs = km3db.StreamDS(container="nt").get("runs", detid=det_id)

    if runs is None:
        log.error("No runs found for detector ID {}".format(det_id))
        return

    for idx, run in enumerate(runs):
        if run.run == run_id:
            break
    else:
        log.error("No run with ID {} found for detector ID".format(run_id, det_id))
        return

    try:
        next_run = runs[idx + 1]
    except IndexError:
        next_run = None
        end_time = duration = float("NaN")
    else:
        duration = (next_run.unixstarttime - run.unixstarttime) / 1000 / 60
        end_time = iso8601utc(next_run.unixstarttime / 1000)

    print("Run {0} - detector ID: {1}".format(run_id, det_id))
    print("-" * 42)
    print(
        "  Start time:         {0}\n"
        "  End time:           {1}\n"
        "  Duration [min]:     {2:.2f}\n"
        "  Start time defined: {3}\n"
        "  Runsetup ID:        {4}\n"
        "  Runsetup name:      {5}\n"
        "  T0 Calibration ID:  {6}".format(
            iso8601utc(run.unixstarttime / 1000),
            end_time,
            duration,
            bool(run.starttime_defined),
            run.runsetupid,
            run.runsetupname,
            run.t0_calibsetid,
        )
    )


def iso8601utc(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def main():
    from docopt import docopt

    args = docopt(__doc__, version=km3db.version)

    runinfo(int(args["RUN"]), int(args["DET_ID"]))
