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
import km3db

log = km3db.logger.log


def runinfo(run_id, det_id, show_trigger=False):
    runtable = km3db.StreamDS(container="nt").get("runtable", detid=det_id)

    if runtable is None:
        log.error("No runs found for detector ID {}".format(det_id))
        return

    for run in runtable:
        if run.run == run_id:
            break
    else:
        log.error("No run with ID {} found for detector ID".format(run_id, det_id))
        return

    if len(row) == 0:
        log.error("No database entry for run {0} found.".format(run_id))
        return
    next_row = df[df["RUN"] == (run_id + 1)]
    if len(next_row) != 0:
        end_time = next_row["DATETIME"].values[0]
        duration = (
            (next_row["UNIXSTARTTIME"].values[0] - row["UNIXSTARTTIME"].values[0])
            / 1000
            / 60
        )
    else:
        end_time = duration = float("NaN")
    print("Run {0} - detector ID: {1}".format(run_id, det_id))
    print("-" * 42)
    print(
        "  Start time:         {0}\n"
        "  End time:           {1}\n"
        "  Duration [min]:     {2:.2f}\n"
        "  Start time defined: {3}\n"
        "  Runsetup ID:        {4}\n"
        "  Runsetup name:      {5}\n"
        "  T0 Calibration ID:  {6}\n".format(
            row["DATETIME"].values[0],
            end_time,
            duration,
            bool(row["STARTTIME_DEFINED"].values[0]),
            row["RUNSETUPID"].values[0],
            row["RUNSETUPNAME"].values[0],
            row["T0_CALIBSETID"].values[0],
        )
    )


def main():
    from docopt import docopt

    args = docopt(__doc__, version=kp.version)

    runinfo(int(args["RUN"]), int(args["DET_ID"]), args["-t"])
