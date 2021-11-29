#!/usr/bin/env python3
"""
A single place where Python 2 vs Python 3 compatibility issues are dealt with.
"""

from functools import wraps
import socket

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
    from http.client import IncompleteRead, RemoteDisconnected

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
    from httplib import IncompleteRead, HTTPException as RemoteDisconnected

    user_input = raw_input


original_getaddrinfo = socket.getaddrinfo


def ipv4_forced_getaddrinfo(*args, **kwargs):
    responses = original_getaddrinfo(*args, **kwargs)
    return [res for res in responses if res[0] == socket.AF_INET]


# Monkey patch to force IPv4
socket.getaddrinfo = ipv4_forced_getaddrinfo


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
