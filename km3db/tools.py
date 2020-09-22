#!/usr/bin/env python3
from collections import OrderedDict, namedtuple
import numbers

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

import km3db.core
import km3db.extras
import km3db.logger


try:
    # Python 3.5+
    from inspect import Signature, Parameter

    SKIP_SIGNATURE_HINTS = False
except ImportError:
    # Python 2.7
    SKIP_SIGNATURE_HINTS = True


def parse_streams(text):
    lines = text.split("\n")
    cls = namedtuple("Stream", [s.lower() for s in lines.pop(0).split()])
    streams = []
    for line in lines:
        if not line:
            continue
        streams.append(cls(*line.split("\t")))
    return sorted(streams, key=lambda s: s.stream)


def topandas(text):
    """Create a DataFrame from database output"""
    return km3db.extras.pandas().read_csv(StringIO(text), sep="\t")


class StreamDS:
    """Access to the streamds data stored in the KM3NeT database."""

    def __init__(self, url=None):
        self._db = km3db.core.DBManager(url=url)
        self._streams = None
        self._update_streams()

    @property
    def streams(self):
        return self._streams

    def _update_streams(self):
        """Update the list of available straems"""
        content = self._db.get("streamds")
        self._streams = OrderedDict()
        streams = parse_streams(content)
        for entry in parse_streams(content):
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
        for stream in self.streams.values():
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

    def get(self, stream, fmt="txt", library="raw", **kwargs):
        """Get the data for a given stream manually"""
        sel = "".join(["&{0}={1}".format(k, v) for (k, v) in kwargs.items()])
        url = "streamds/{0}.{1}?{2}".format(stream, fmt, sel[1:])
        data = self._db.get(url)
        if not data:
            log.error("No data found at URL '%s'." % url)
            return
        if data.startswith("ERROR"):
            log.error(data)
            return
        if library == "pd":
            return topandas(data)
        return data


class CLBMap:
    par_map = {"DETOID": "det_oid", "UPI": "upi", "DOMID": "dom_id"}

    def __init__(self, det_oid):
        if isinstance(det_oid, numbers.Integral):
            db = km3db.core.DBManager()
            # det_oid and det_id chaos in the database
            # _det_oid = db.get_det_oid(det_oid)
            # if _det_oid is not None:
            #     det_oid = _det_oid
        self.det_oid = det_oid
        sds = StreamDS()
        self._data = sds.clbmap(detoid=det_oid)
        self._by = {}

    def __len__(self):
        return len(self._data)

    @property
    def upis(self):
        """A dict of CLBs with UPI as key"""
        parameter = "UPI"
        if parameter not in self._by:
            self._populate(by=parameter)
        return self._by[parameter]

    @property
    def dom_ids(self):
        """A dict of CLBs with DOM ID as key"""
        parameter = "DOMID"
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
            for clb in self.upis.values():
                if clb.floor == 0:
                    self._by[parameter][clb.du] = clb
        return self._by[parameter][du]

    def _populate(self, by):
        data = {}
        for _, row in self._data.iterrows():
            data[row[by]] = CLB(
                det_oid=row["DETOID"],
                floor=row["FLOORID"],
                du=row["DUID"],
                serial_number=row["SERIALNUMBER"],
                upi=row["UPI"],
                dom_id=row["DOMID"],
            )
        self._by[by] = data


CLB = namedtuple("CLB", ["det_oid", "floor", "du", "serial_number", "upi", "dom_id"])
