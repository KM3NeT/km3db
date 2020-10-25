#!/usr/bin/env python3
from collections import OrderedDict, namedtuple
import json

import km3db.compat
import km3db.core
import km3db.extras
from km3db.logger import log


try:
    # Python 3.5+
    from inspect import Signature, Parameter

    SKIP_SIGNATURE_HINTS = False
except ImportError:
    # Python 2.7
    SKIP_SIGNATURE_HINTS = True


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

        if not SKIP_SIGNATURE_HINTS:
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
            self.log.warning(json_content["Comment"])
        if json_content["Result"] != "OK":
            self.log.critical("Error from DB: %s", json_content.get("Data"))
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


@km3db.compat.lru_cache
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


@km3db.compat.lru_cache
def todetoid(det_id):
    """Convert det OID (e.g. D_ORCA006) to det ID (e.g. 49)

    If a det OID is provided it will simple be returned.
    """
    if isinstance(det_id, str):
        return det_id
    detectors = StreamDS(container="nt").get("detectors")
    for detector in detectors:
        if detector.serialnumber == det_id:
            return detector.oid
    log.error("Could not convert det ID '{}' to OID".format(det_id))


@km3db.compat.lru_cache
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
    return km3db.extras.pandas().read_csv(km3db.compat.StringIO(text), sep="\t")


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
        root = ET.parse(km3db.compat.StringIO(content)).getroot()
    except ET.ParseError:
        print("No calibration data found")
    else:
        for child in root:
            print("{}: {}".format(child.tag, child.text))
        names = [c.text for c in root.findall(".//Name")]
        values = [[i.text for i in c] for c in root.findall(".//Values")]
        for name, value in zip(names, values):
            print("{}: {}".format(name, value))


def detx(det_id, t0set=None, calibration=None):
    """Retrieve the detector file for given detector ID"""
    url = "detx/{0}?".format(det_id)  # '?' for easy concat below

    if t0set is not None:
        url += "&t0set=" + str(t0set)
    if calibration is not None:
        url += "&calibrid=" + str(calibration)

    detx_content = km3db.core.DBManager().get(url)

    return detx_content


def detx_for_run(det_id, run):
    """Retrieve the calibrate detector file for given run"""
    run_table = StreamDS(container="nt").get("runs", detid=det_id)
    if run_table is None:
        log.error("No run table found for detector ID {}".format(det_id))
        return None

    for run_info in run_table:
        if run_info.run == run:
            break
    else:
        log.error("Run {} not found for detector {}".format(run, det_id))
        return None

    tcal = run_info.t0_calibsetid
    if str(tcal) == "nan":
        log.warning(
            "No time calibration found for run {} (detector {})".format(run, det_id)
        )
        tcal = 0

    try:
        pcal = int(run_info.pos_calibsetid)
    except ValueError:
        log.warning(
            "No position calibration found for run {} (detector {})".format(run, det_id)
        )
        pcal = 0

    try:
        rcal = int(run_info.rot_calibsetid)
    except ValueError:
        log.warning(
            "No rotation calibration found for run {} (detector {})".format(run, det_id)
        )
        rcal = 0

    url = "detx/{det_id}?tcal={tcal}&pcal={pcal}&rcal={rcal}".format(
        det_id=det_id, tcal=tcal, pcal=pcal, rcal=rcal
    )

    detx = km3db.core.DBManager().get(url)
    return detx
