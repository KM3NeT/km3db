#!/usr/bin/env python3
# Filename: core.py
"""
Database utilities.

"""
from __future__ import absolute_import, print_function, division

from functools import lru_cache
from datetime import datetime
import numbers
import ssl
import io
import json
import re
import pytz
import socket
from collections import defaultdict, OrderedDict, namedtuple
try:
    from inspect import Signature, Parameter
    SKIP_SIGNATURE_HINTS = False
except ImportError:
    SKIP_SIGNATURE_HINTS = True
try:
    from urllib.parse import urlencode, unquote
    from urllib.request import (
        Request, build_opener, urlopen, HTTPCookieProcessor, HTTPHandler
    )
    from urllib.error import URLError, HTTPError
    from io import StringIO
    from http.client import IncompleteRead
except ImportError:
    from urllib import urlencode, unquote
    from urllib2 import (
        Request, build_opener, urlopen, HTTPCookieProcessor, HTTPHandler,
        URLError, HTTPError
    )
    from StringIO import StringIO
    from httplib import IncompleteRead
    input = raw_input


# Ignore invalid certificate error
ssl._create_default_https_context = ssl._create_unverified_context

BASE_URL = "https://km3netdbweb.in2p3.fr"
SESSION_COOKIES = dict(
    lyon="sid=_kmcprod_134.158_lyo7783844001343100343mcprod1223user",
    jupyterhub="sid=_jupyter-km3net_131.188.161.143_d9fe89a1568a49a5ac03bdf15d93d799",
    gitlab="sid=_gitlab-km3net_131.188.161.155_f835d56ca6d946efb38324d59e040761"
)
UTC_TZ = pytz.timezone("UTC")


class DBManager:
    def __init__(self, username=None, password=None, url=None):
        self._db_url = BASE_URL if url is None else url
        self._login_url = os.path.join(self._db_url, 'home.htm')

    @lru_cache
    def get_session_cookie(self):


def we_are_in_lyon():
    """Check if we are on a Lyon machine"""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        return False
    return ip.startswith("134.158.")


def we_are_on_jupyterhub():
    """Check if we are on the JupyterHub machine"""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        return False
    return ip == socket.gethostbyname("jupyter.km3net.de")


def we_are_on_km3net_gitlab_ci():
    """Check if we are on a GitLab CI runner server"""
    external_ip = urlopen("https://ident.me").read().decode("utf8")
    return external_ip == "131.188.161.155"
