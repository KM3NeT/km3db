#!/usr/bin/env python3
"""
Access the KM3NeT StreamDS DataBase service.

Usage:
    streamds
    streamds list
    streamds info STREAM
    streamds get [-f FORMAT -o OUTFILE -g COLUMN] STREAM [PARAMETERS...]
    streamds upload [-q -x] CSV_FILE
    streamds (-h | --help)
    streamds --version

Options:
    STREAM      Name of the stream.
    PARAMETERS  List of parameters separated by space (e.g. detid=29).
    CSV_FILE    Whitespace separated data for the runsummary tables.
    -f FORMAT   Usually 'txt' for ASCII or 'text' for UTF-8 [default: txt].
    -o OUTFILE  Output file: supported formats '.csv' and '.h5'.
    -g COLUMN   Group dataset by the name of the given row when writing HDF5.
    -q          Test run! When uploading, a TEST_ prefix will be added to the data.
    -x          Do not verify the SSL certificate.
    -h --help   Show this screen.

"""
import getpass
import json
import logging
import os
import requests

import km3db
import km3db.extras
from docopt import docopt

log = logging.getLogger("streamds")

RUNSUMMARYNUMBERS_URL = "https://km3netdbweb.in2p3.fr/jsonds/runsummarynumbers/i"
RUNSUMMARYSTRINGS_URL = "https://km3netdbweb.in2p3.fr/jsonds/runsummarystrings/i"
RUNSUMMARYSTRINGS_COLUMNS = set(["UUID", "JPP"])
REQUIRED_COLUMNS = set(["run", "det_id", "source"])


def print_streams():
    """Print all available streams with their full description"""
    sds = km3db.StreamDS()
    sds.print_streams()


def print_info(stream):
    """Print the information about a stream"""
    sds = km3db.StreamDS()
    sds.help(stream)


def get_data(stream, parameters, fmt, outfile=None, groupby=None):
    """Retrieve data for given stream and parameters, or None if not found"""
    sds = km3db.StreamDS()
    if stream not in sds.streams:
        log.error("Stream '{}' not found in the database.".format(stream))
        return
    params = {}
    if parameters:
        for parameter in parameters:
            if "=" not in parameter:
                log.error("Invalid parameter syntax '{}'\n"
                          "The correct syntax is 'parameter=value'".format(
                              parameter))
                continue
            key, value = parameter.split("=")
            params[key] = value
    data = sds.get(stream, fmt, **params)
    if data is not None:
        if outfile is not None:
            write_output(outfile, stream, data, groupby)
        else:
            try:
                print(data)
            except BrokenPipeError:
                pass
    else:
        sds.help(stream)


def write_output(outfile, stream, data, groupby=None):
    """Writes the DB output to a file (HDF5 or CSV)"""
    _, ext = os.path.splitext(outfile)

    if ext == ".h5":
        write_output_hdf5(outfile, stream, data, groupby=groupby)
        exit(0)
    if ext == ".csv":
        write_output_csv(outfile, stream, data)
        exit(0)

    log.error("Unsupported filetype with '{}'".format(ext))
    exit(1)


def write_output_hdf5(outfile, stream, data, groupby):
    """Write DB output to HDF5"""
    h5py = km3db.extras.h5py()
    df = km3db.tools.topandas(data)
    with h5py.File(outfile, "a") as h5f:
        if groupby is not None:
            for group, _df in df.groupby(groupby):
                sa = km3db.tools.df_to_sarray(_df)
                dset_name = stream + "/{}".format(group)
                if dset_name in h5f:
                    log.warning(
                        "Dataset '{}' already exists, skipping...".format(dset_name)
                    )
                    continue
                h5f.create_dataset(
                    stream + "/{}".format(group),
                    compression="gzip",
                    compression_opts=3,
                    data=sa,
                )
        else:
            sa = km3db.tools.df_to_sarray(df)
            h5f[stream] = sa
    print("Database output written to '{}'.".format(outfile))


def write_output_csv(outfile, stream, data):
    """Write DB output to CSV"""
    with open(outfile, "w") as fobj:
        fobj.write(data)
    print("Database output written to '{}'.".format(outfile))


def available_streams():
    """Show a short list of available streams."""
    sds = km3db.StreamDS()
    print("Available streams: ")
    print(", ".join(sorted(sds.streams)))


def upload_runsummary(csv_filename, testrun=False, verify=False):
    """Reads the CSV file and uploads its contents to the runsummary table"""
    pd = km3db.extras.pandas()

    print("Checking '{}' for consistency.".format(csv_filename))
    if not os.path.exists(csv_filename):
        log.critical("{} -> file not found.".format(csv_filename))
        return
    try:
        df = pd.read_csv(csv_filename, delim_whitespace=True)
    except pd.errors.EmptyDataError as e:
        log.error(e)
        return

    cols = set(df.columns)

    if not REQUIRED_COLUMNS.issubset(cols):
        log.error("Missing columns: {}.".format(', '.join(
            str(c) for c in REQUIRED_COLUMNS - cols)))
        return

    parameters = cols - REQUIRED_COLUMNS
    if len(parameters) < 1:
        log.error("No parameter columns found.")
        return

    if len(df) == 0:
        log.critical("Empty dataset.")
        return

    print("Found data for parameters: {}.".format(', '.join(
        str(c) for c in parameters)))
    print("Converting CSV data into JSON")
    if testrun:
        log.warn("Test run: adding 'TEST_' prefix to parameter names")
        prefix = "TEST_"
    else:
        prefix = ""

    det_id_zero_mask = df['det_id'] == 0
    if sum(det_id_zero_mask) > 0:
        log.warning("Entries with 'det_id=0' found, removing them.")
        df = df[~det_id_zero_mask]
    df["det_id"] = df["det_id"].apply(km3db.tools.todetoid)
    print(df)

    data_runsummarynumbers = convert_runsummary_to_json(
        df[df.columns.difference(RUNSUMMARYSTRINGS_COLUMNS)], prefix=prefix)
    print("We have {:.3f} MB runsummarynumbers to upload.".format(
        len(data_runsummarynumbers) / 1024**2))
    _database_upload(data_runsummarynumbers, verify)

    data_runsummarystrings = convert_runsummary_to_json(
        df[REQUIRED_COLUMNS.union(RUNSUMMARYSTRINGS_COLUMNS)],
        prefix=prefix,
        isrunsummarystrings=True)
    print("We have {:.3f} MB runsummarystrings to upload.".format(
        len(data_runsummarystrings) / 1024**2))
    _database_upload(data_runsummarystrings, verify, isrunsummarystrings=True)


def _database_upload(data, verify=False, isrunsummarystrings=False):
    db = km3db.DBManager()  # noqa

    print("Requesting database session.")
    session_cookie = db.session_cookie

    print("Uploading the data to the database.")
    url = RUNSUMMARYSTRINGS_URL if isrunsummarystrings else RUNSUMMARYNUMBERS_URL
    print("URL: {}".format(url))
    r = requests.post(url,
                      cookies={"sid": session_cookie},
                      files={'datafile': data},
                      verify=verify)

    if r.status_code == 200:
        log.debug("POST request status code: {}".format(r.status_code))
        print("Database response:")
        db_answer = json.loads(r.text)
        for key, value in db_answer.items():
            print("  -> {}: {}".format(key, value))
        if db_answer["Result"] == "OK":
            print("Upload successful.")
        else:
            log.critical("Something went wrong.")
    else:
        log.error("POST request status code: {}".format(r.status_code))
        log.critical("Something went wrong...")
        return


def convert_runsummary_to_json(df,
                               comment='Uploaded via km3pipe.StreamDS',
                               prefix='TEST_',
                               isrunsummarystrings=False):
    """Convert a Pandas DataFrame with runsummary to JSON for DB upload"""
    data_field = []
    comment += ", by {}".format(getpass.getuser())
    for det_id, det_data in df.groupby("det_id"):
        runs_field = []
        data_field.append({"DetectorId": det_id, "Runs": runs_field})

        for run, run_data in det_data.groupby("run"):
            parameters_field = []
            runs_field.append({"Run": int(run), "Parameters": parameters_field})

            parameter_dict = {}
            for row in run_data.iterrows():
                for parameter_name in run_data.columns:
                    if parameter_name in REQUIRED_COLUMNS:
                        continue

                    if parameter_name not in parameter_dict:
                        entry = {"Name": prefix + parameter_name, "Data": []}
                        parameter_dict[parameter_name] = entry
                    data_value = getattr(row[1], parameter_name)
                    if not isrunsummarystrings:
                        try:
                            data_value = float(data_value)
                        except ValueError as e:
                            log.critical("Data values has to be floats!")
                            raise ValueError(e)
                    else:
                        data_value = str(data_value)
                    value = {
                        'S': str(getattr(row[1], 'source')),
                        'D': data_value
                    }
                    parameter_dict[parameter_name]['Data'].append(value)
            for parameter_data in parameter_dict.values():
                parameters_field.append(parameter_data)
    data_to_upload = {"Comment": comment, "Data": data_field}
    file_data_to_upload = json.dumps(data_to_upload)
    return file_data_to_upload


def main():
    args = docopt(__doc__)

    if args["info"]:
        print_info(args["STREAM"])
    elif args["list"]:
        print_streams()
    elif args["upload"]:
        upload_runsummary(args["CSV_FILE"], args["-q"], args["-x"])
    elif args["get"]:
        get_data(
            args["STREAM"],
            args["PARAMETERS"],
            fmt=args["-f"],
            outfile=args["-o"],
            groupby=args["-g"],
        )
    else:
        available_streams()
