#!/usr/bin/env python3
"""
A single place where Python 2 vs Python 3 compatibility issues are dealt with.
"""

from functools import wraps

try:
    from urllib.parse import urlencode, unquote
    from urllib.request import (
        Request,
        build_opener,
        urlopen,
        HTTPCookieProcessor,
        HTTPHandler,
    )
    from urllib.error import URLError, HTTPError
    from io import StringIO
    from http.client import IncompleteRead

    user_input = input
except ImportError:
    from urllib import urlencode, unquote
    from urllib2 import (
        Request,
        build_opener,
        urlopen,
        HTTPCookieProcessor,
        HTTPHandler,
        URLError,
        HTTPError,
    )
    from StringIO import StringIO
    from httplib import IncompleteRead

    user_input = raw_input


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
