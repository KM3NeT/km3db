#!/usr/bin/env python3
from collections import OrderedDict, namedtuple
from functools import wraps
from inspect import Parameter, Signature
import io
import json

import numpy as np

import km3db.core
import km3db.extras
from km3db.logger import log


class APIv2:
    _api_endpoint = "apiv2.1.0/"
    _valid_operators = ("<", "<=", ">", ">=", "<>", "!=")

    def __init__(self, url=None, container=None):
        self._db = km3db.core.DBManager(url=url)
        self._endpoints = None
        self._update_endpoints()

    def __getattr__(self, attr, **kwargs):
        """Magic getter to select a specific stream"""
        if attr not in self.endpoints:
            raise AttributeError(
                "Invalid selector: '{}'. Please use one of these: {}".format(
                    attr, ", ".join(self.endpoints.keys())
                )
            )

        def func(**kwargs):
            url = "{}/s?".format(attr)
            for key, value in kwargs.items():
                key = str(key)
                value = str(value)
                url += "&" + key
                if any(value.startswith(op) for op in self._valid_operators):
                    url += value
                else:
                    url += "=" + value
            return self._get(url)

        func.__doc__ = self.endpoints[attr]["Description"]

        # TODO: schema not used yet
        # schema = _extract_schema(self.endpoints[attr]["Schema"])
        selectors = _extract_selectors(self.endpoints[attr]["Selectors"])

        func.__doc__ += "\n\nParameters:\n"
        sig_dict = OrderedDict()
        for sel, description in selectors.items():
            func.__doc__ += "    {}: {}\n".format(sel, description)
            sig_dict[Parameter(sel, Parameter.KEYWORD_ONLY)] = None

        func.__signature__ = Signature(parameters=sig_dict)

        return func

    @property
    def endpoints(self):
        return {e["Name"]: e for e in self._endpoints}

    def _update_endpoints(self):
        """Update the list of available endpoints"""
        self._endpoints = self._get()

    def _get(self, url="", default=None, **kwargs):
        """Return the data for a given APIv2 endpoint. Does not raise."""
        try:
            final_url = "{}{}".format(self._api_endpoint, url)
            response = json.loads(self._db.get(final_url))
        except json.JSONDecodeError:
            log.error("Invalid JSON data received from the DB")
            return default
        if not self._validate(response):
            return default
        return response["Data"]

    def _validate(self, response):
        """Returns True if the DB response is OK, False otherwise."""
        err = response["Error"]
        if err["Code"] != "OK":
            log.error(
                "Error from the DB ({}): {} (arguments: {})".format(
                    err["Code"], err["Message"], err["Arguments"]
                )
            )
            return False
        return True


def _extract_selectors(raw_strings):
    """Creates a dictionary from the raw DB output (list of strings).

    A string like "OperationId -> Filters by OperationId" will become an entry
    in the resulting dictionary with "OperationId" as key and "Filters by
    OperationId" as value.

    """
    selectors = dict()
    for entry in raw_strings:
        selector, description = entry.split(" -> ")
        selectors[selector] = description
    return selectors


class StreamDS:
    """Access to the streamds data stored in the KM3NeT database.

    Parameters
    ==========
    url: str (optional)
      The URL of the database web API
    container: str or None (optional)
      The default containertype when returning data.
        None (default): the data, as returned from the DB
          "nt": `namedtuple`, can be used when no pandas is available
          "pd": `pandas.DataFrame`, as returned in KM3Pipe v8 and below
    """

    def __init__(self, url=None, container=None):
        self._db = km3db.core.DBManager(url=url)
        self._streams = None
        self._update_streams()
        self._default_container = container

    @property
    def streams(self):
        return self._streams

    def _update_streams(self):
        """Update the list of available straems"""
        content = self._db.get("streamds")
        self._streams = OrderedDict()
        for entry in tonamedtuples("Stream", content):
            self._streams[entry.stream] = entry
            setattr(self, entry.stream, self.__getattr__(entry.stream))

    def __getattr__(self, attr):
        """Magic getter which optionally populates the function signatures"""
        if attr in self.streams:
            stream = self.streams[attr]
        else:
            raise AttributeError

        def func(**kwargs):
            return self.get(attr, **kwargs)

        func.__doc__ = stream.description

        sig_dict = OrderedDict()
        for sel in stream.mandatory_selectors.split(","):
            if sel == "-":
                continue
            sig_dict[Parameter(sel, Parameter.POSITIONAL_OR_KEYWORD)] = None
        for sel in stream.optional_selectors.split(","):
            if sel == "-":
                continue
            sig_dict[Parameter(sel, Parameter.KEYWORD_ONLY)] = None
        func.__signature__ = Signature(parameters=sig_dict)

        return func

    def print_streams(self):
        """Print the documentation for all available streams."""
        for stream in sorted(self.streams.values()):
            self._print_stream_parameters(stream)

    def _print_stream_parameters(self, stream):
        """Print the documentation for a given stream."""
        print("{}".format(stream.stream))
        print("-" * len(stream.stream))
        print("{}".format(stream.description))
        print("  available formats:   {}".format(stream.formats))
        print("  mandatory selectors: {}".format(stream.mandatory_selectors))
        print("  optional selectors:  {}".format(stream.optional_selectors))
        print()

    def help(self, stream_name):
        """Print help for a given stream"""
        try:
            self._print_stream_parameters(self.streams[stream_name])
        except KeyError:
            log.error("There is no stream called '{}'".format(stream_name))
            print(
                "Available streams:\n{}".format(
                    ", ".join(s.stream for s in sorted(self.streams.values()))
                )
            )

    def get(self, stream, fmt="txt", container=None, renamemap=None, **kwargs):
        """Retrieve the data for a given stream manually

        Parameters
        ==========
        stream: str
          Name of the stream (e.g. detectors)
        fmt: str ("txt", "text", "bin")
          Retrieved raw data format, depends on the stream type
        container: str or None
          The container to wrap the returned data, as specified in
          `StreamDS`.
        """
        sel = "".join(["&{0}={1}".format(k, v) for (k, v) in kwargs.items()])
        url = "streamds/{0}.{1}?{2}".format(stream, fmt, sel[1:])
        log.debug("URL: %s" % url)
        data = self._db.get(url)
        if not data:
            log.error("No data found at URL '%s'." % url)
            return
        if data.startswith("ERROR"):
            log.error(data)
            return

        if container is None and self._default_container is not None:
            container = self._default_container

        try:
            if container == "pd":
                return topandas(data)
            if container == "nt":
                return tonamedtuples(stream.capitalize(), data, renamemap=renamemap)
        except ValueError:
            log.critical(
                "Unable to convert data to container type '{}'. "
                "Database response: {}".format(container, data)
            )
        else:
            return data


class JSONDS:
    """Access to the jsonds data stored in the KM3NeT database.

    Parameters
    ==========
    url: str (optional)
      The URL of the database web API

    """

    def __init__(self, url=None):
        self._db = km3db.core.DBManager(url=url)

    def get(self, url):
        "Get JSON-type content from the url"
        content = self._db.get("jsonds/" + url)
        try:
            json_content = json.loads(content.decode())
        except AttributeError:
            json_content = json.loads(content)
        if json_content.get("Comment") is not None:
            log.warning(json_content["Comment"])
        if json_content["Result"] != "OK":
            log.critical("Error from DB: %s", json_content.get("Data"))
            raise ValueError("Error while retrieving the parameter list.")
        return json_content["Data"]


class CLBMap:
    renamemap = dict(
        DETOID="det_oid",
        UPI="upi",
        DOMID="dom_id",
        DUID="du",
        SERIALNUMBER="serial_number",
        FLOORID="floor",
    )

    def __init__(self, det_oid):
        # if isinstance(det_oid, numbers.Integral):
        #     db = km3db.core.DBManager()
        #     # det_oid and det_id chaos in the database
        #     # _det_oid = db.get_det_oid(det_oid)
        #     # if _det_oid is not None:
        #     #     det_oid = _det_oid
        self.det_oid = det_oid
        sds = StreamDS(container="nt")
        self._data = sds.get("clbmap", detoid=det_oid, renamemap=self.renamemap)
        self._by = {}

    def __len__(self):
        return len(self._data)

    @property
    def upis(self):
        """A dict of CLBs with UPI as key"""
        parameter = "upi"
        if parameter not in self._by:
            self._populate(by=parameter)
        return self._by[parameter]

    @property
    def dom_ids(self):
        """A dict of CLBs with DOM ID as key"""
        parameter = "dom_id"
        if parameter not in self._by:
            self._populate(by=parameter)
        return self._by[parameter]

    @property
    def omkeys(self):
        """A dict of CLBs with the OMKey tuple (DU, floor) as key"""
        parameter = "omkey"
        if parameter not in self._by:
            self._by[parameter] = {}
            for clb in self.upis.values():
                omkey = (clb.du, clb.floor)
                self._by[parameter][omkey] = clb
            pass
        return self._by[parameter]

    def base(self, du):
        """Return the base CLB for a given DU"""
        parameter = "base"
        if parameter not in self._by:
            self._by[parameter] = {}
            for clb in self._data:
                if clb.floor == 0:
                    self._by[parameter][clb.du] = clb
        return self._by[parameter][du]

    def _populate(self, by):
        data = {}
        for clb in self._data:
            data[getattr(clb, by)] = clb
        self._by[by] = data


def lru_cache(func):
    """Poor mans lru_cache for compatiblity"""
    cache = {}

    @wraps(func)
    def wrapper(*args):
        key = tuple(args)
        if key not in cache:
            cache[key] = func(*args)
        return cache[key]

    return wrapper


@lru_cache
def clbupi2compassupi(clb_upi):
    """Return Compass UPI from CLB UPI."""
    sds = StreamDS(container="nt")
    upis = [i.content_upi for i in sds.integration(container_upi=clb_upi)]
    compass_upis = [upi for upi in upis if ("AHRS" in upi) or ("LSM303" in upi)]
    if len(compass_upis) > 1:
        log.warning(
            "Multiple compass UPIs found for CLB UPI {}. "
            "Using the first entry.".format(clb_upi)
        )
    return compass_upis[0]


@lru_cache
def todetoid(det_id):
    """Convert det OID (e.g. D_ORCA006) to det ID (e.g. 49)

    If a det OID is provided it will simple be returned.
    """
    try:
        det_id = int(det_id)
    except ValueError:
        # assume it's an OID
        return det_id

    detectors = StreamDS(container="nt").get("detectors")
    for detector in detectors:
        if detector.serialnumber == det_id:
            return detector.oid
    log.error("No detector with det ID '{}' found to look up its OID".format(det_id))


@lru_cache
def todetid(det_oid):
    """Convert det ID (e.g. 49) to det OID (e.g. D_ORCA006)

    If a det OID is provided it will simple be returned.
    """
    if isinstance(det_oid, int):
        return det_oid
    detectors = StreamDS(container="nt").get("detectors")
    for detector in detectors:
        if detector.oid == det_oid:
            return detector.serialnumber
    log.error("Could not convert det OID '{}' to ID".format(det_oid))


def tonum(value):
    """Convert a value to a numerical one if possible"""
    for converter in (int, float):
        try:
            return converter(value)
        except (ValueError, TypeError):
            pass
    return value


def tonamedtuples(name, text, renamemap=None):
    """Creates a list of namedtuples from database output

    Parameters
    ----------
    name: str
      Name of the namedtuple
    text: str
      Raw output from the database (tab separated values
      and the first line being the header)
    renamemap: dict(str: str) or None (default)
      Rename the fields according to this map.
    """
    if renamemap is None:
        renamemap = {}
    lines = text.split("\n")
    cls = namedtuple(name, [renamemap.get(s, s.lower()) for s in lines.pop(0).split()])
    entries = []
    for line in lines:
        if not line:
            continue
        entries.append(cls(*map(tonum, line.split("\t"))))
    return entries


def topandas(text):
    """Create a DataFrame from database output"""
    return km3db.extras.pandas().read_csv(io.StringIO(text), sep="\t", dtype={'PROMISID': 'str'})


def df_to_sarray(df):
    """
    Convert a pandas DataFrame object to a numpy structured array.

    Parameters
    ----------
    df : Pandas.DataFrame
      the data frame to convert

    Returns
    -------
    A numpy structured array representation of df.
    """

    for dtype in df.dtypes:
        if dtype is np.dtype("O"):
            log.critical(
                "At least one column contains strings, "
                "which are currently not supported in the HDF5 backend. "
                "The CSV backend will work fine."
            )
            exit(1)

    cols = df.columns
    types = [(cols[i], df[k].dtype.type) for (i, k) in enumerate(cols)]
    v = df.values
    arr = np.zeros(v.shape[0], np.dtype(types))
    for idx, field in enumerate(arr.dtype.names):
        arr[field] = v[:, idx]
    return arr


def show_compass_calibration(clb_upi, version="3"):
    """Show compass calibration data for given `clb_upi`."""
    db = km3db.core.DBManager()
    compass_upi = clbupi2compassupi(clb_upi)
    compass_model = compass_upi.split("/")[1]
    print("Compass UPI: {}".format(compass_upi))
    print("Compass model: {}".format(compass_model))
    content = db.get(
        "show_product_test.htm?upi={}&"
        "testtype={}-CALIBRATION-v{}&n=1&out=xml".format(
            compass_upi, compass_model, version
        )
    ).replace("\n", "")

    import xml.etree.ElementTree as ET

    try:
        root = ET.parse(io.StringIO(content)).getroot()
    except ET.ParseError:
        print("No calibration data found")
    else:
        for child in root:
            print("{}: {}".format(child.tag, child.text))
        names = [c.text for c in root.findall(".//Name")]
        values = [[i.text for i in c] for c in root.findall(".//Values")]
        for name, value in zip(names, values):
            print("{}: {}".format(name, value))


def detx(det_id, pcal=0, rcal=0, tcal=0, acal=0, ccal=0, scal=0, version=5):
    """Retrieve the calibrated detector file for the given detector ID"""

    print(
        "Retrieving DETX for {} with: pcal={}, rcal={}, tcal={}, acal={}, ccal={}, scal={}".format(
            det_id, pcal, rcal, tcal, acal, ccal, scal
        )
    )

    url = (
        "detx/{det_id}?"
        "tcal={tcal}&pcal={pcal}&rcal={rcal}&"
        "acal={acal}&ccal={ccal}&scal={scal}&"
        "v={version}".format(
            det_id=det_id,
            tcal=tcal,
            pcal=pcal,
            rcal=rcal,
            acal=acal,
            ccal=ccal,
            scal=scal,
            version=version,
        )
    )

    return km3db.core.DBManager().get(url)


def detx_for_run(det_id, run, version=5):
    """Retrieve the calibrate detector file for given run"""
    api = APIv2()
    cals = api.RunCalibration(DetOId=todetoid(det_id), Run=run, Ranking=1)
    calibration_ids = dict()
    # type is e.g. "COMPASS_CALIBRATION" or "STATUS_CALIBRATION", corresponding to "ccal" or "scal"
    for cal in cals:
        calibration_ids[cal["CalibrationType"]] = cal["CalibrationId"]

    return detx(
        det_id,
        pcal=calibration_ids.get("DOM_POSITION_CALIBRATION", 0),
        rcal=calibration_ids.get("DOM_ROTATION_CALIBRATION", 0),
        tcal=calibration_ids.get("PMT_T0_CALIBRATION", 0),
        acal=calibration_ids.get("ACOUSTIC_T0_CALIBRATION", 0),
        ccal=calibration_ids.get("COMPASS_CALIBRATION", 0),
        scal=calibration_ids.get("STATUS_CALIBRATION", 0),
        version=version,
    )
