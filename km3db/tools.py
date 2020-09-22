#!/usr/bin/env python3
from collections import OrderedDict, namedtuple

from .core import DBManager
from .logger import log


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


class StreamDS(object):
    """Access to the streamds data stored in the KM3NeT database."""
    def __init__(self, url=None):
        self._db = DBManager(url=url)
        self.streams = None
        self._update_streams()

    def _update_streams(self):
        """Update the list of available straems"""
        content = self._db.get("streamds")
        streams = parse_streams(content)
        for stream in streams:
            setattr(self, stream, self.__getattr__(stream))
        self.streams = streams

    def __getattr__(self, attr):
        """Magic getter which optionally populates the function signatures"""
        if attr in self.streams:
            stream = attr
        else:
            raise AttributeError

        def func(**kwargs):
            return self.get(stream, **kwargs)

        func.__doc__ = self._stream_parameter(stream, "DESCRIPTION")

        if not SKIP_SIGNATURE_HINTS:
            sig_dict = OrderedDict()
            for sel in self.mandatory_selectors(stream):
                if sel == '-':
                    continue
                sig_dict[Parameter(sel,
                                   Parameter.POSITIONAL_OR_KEYWORD)] = None
            for sel in self.optional_selectors(stream):
                if sel == '-':
                    continue
                sig_dict[Parameter(sel, Parameter.KEYWORD_ONLY)] = None
            func.__signature__ = Signature(parameters=sig_dict)

        return func

    def _stream_parameter(self, stream, parameter):
        data = self._stream_df[self._stream_df.STREAM == stream]
        if 'SELECTORS' in parameter:
            return list(data[parameter].values[0].split(','))
        else:
            return data[parameter].values[0]

    def mandatory_selectors(self, stream):
        """A list of mandatory selectors for a given stream"""
        return self._stream_parameter(stream, 'MANDATORY_SELECTORS')

    def optional_selectors(self, stream):
        """A list of optional selectors for a given stream"""
        return self._stream_parameter(stream, 'OPTIONAL_SELECTORS')

    def help(self, stream):
        """Show the help for a given stream."""
        if stream not in self.streams:
            log.error("Stream '{}' not found in the database.".format(stream))
        params = self._stream_df[self._stream_df['STREAM'] == stream].values[0]
        self._print_stream_parameters(params)

    def print_streams(self):
        """Print a coloured list of streams and its parameters"""
        for row in self._stream_df.itertuples():
            self._print_stream_parameters(row[1:])

    def _print_stream_parameters(self, values):
        """Print a coloured help for a given tuple of stream parameters."""
        print("{0}".format(*values), "magenta", attrs=["bold"])
        print("{4}".format(*values))
        print("  available formats:   {1}".format(*values), "blue")
        print("  mandatory selectors: {2}".format(*values), "red")
        print("  optional selectors:  {3}".format(*values), "green")
        print()

    def get(self, stream, fmt='txt', **kwargs):
        """Get the data for a given stream manually"""
        sel = ''.join(["&{0}={1}".format(k, v) for (k, v) in kwargs.items()])
        url = "streamds/{0}.{1}?{2}".format(stream, fmt, sel[1:])
        data = self._db._get_content(url)
        if not data:
            log.error("No data found at URL '%s'." % url)
            return
        if (data.startswith("ERROR")):
            log.error(data)
            return
        if fmt == "txt":
            return read_csv(data)
        return data
