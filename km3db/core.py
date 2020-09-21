#!/usr/bin/env python3
# Filename: core.py
"""
Database utilities.

"""
from __future__ import absolute_import, print_function, division

import ssl
import getpass
import os
import re
import pytz
import socket
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

import logging
import coloredlogs

coloredlogs.installer(level="WARNING")

log = logging.getLogger("km3db")

# Ignore invalid certificate error
ssl._create_default_https_context = ssl._create_unverified_context

BASE_URL = "https://km3netdbweb.in2p3.fr"
COOKIE_FILENAME = os.path.expanduser("~/.km3netdb_cookie")
SESSION_COOKIES = dict(
    lyon="_kmcprod_134.158_lyo7783844001343100343mcprod1223user",
    jupyter="_jupyter-km3net_131.188.161.143_d9fe89a1568a49a5ac03bdf15d93d799",
    gitlab="_gitlab-km3net_131.188.161.155_f835d56ca6d946efb38324d59e040761",
)
UTC_TZ = pytz.timezone("UTC")

_cookie_sid_pattern = re.compile(r'_[a-z0-9-]+_(\d{1,3}.){1,3}\d{1,3}_[a-z0-9]+')


class DBManager:
    def __init__(self, url=None):
        self._db_url = BASE_URL if url is None else url
        self._login_url = os.path.join(self._db_url, 'home.htm')
        self._session_cookie = None

        for host, session_cookie in SESSION_COOKIES.items():
            if on_whitelisted_host(host):
                self._session_cookie = session_cookie

    @property
    def session_cookie(self):
        if self._session_cookie is None:
            # session_cookie = get_whitelist_cookie()
            session_cookie = None
            if session_cookie is None:
                session_cookie = self._request_session_cookie()
            self._session_cookie = session_cookie
        return self._session_cookie

    def _request_session_cookie(self):
        """Request cookie for permanent session."""
        # Environment variables have the highest precedence.
        username = os.getenv("KM3NET_DB_USERNAME")
        password = os.getenv("KM3NET_DB_PASSWORD")
        # Next, try the configuration file according to
        # the specification described here:
        # https://wiki.km3net.de/index.php/Database#Scripting_access
        if os.path.exists(COOKIE_FILENAME):
            with open(COOKIE_FILENAME) as fobj:
                content = fobj.read()
            return content.split("\t")[-1].strip()

        # Last resort: we ask interactively
        if username is None:
            username = input("Please enter your KM3NeT DB username: ")
        if password is None:
            password = getpass.getpass("Password: ")

        target_url = self._login_url + '?usr={0}&pwd={1}&persist=y'.format(
            username, password
        )
        cookie = urlopen(target_url).read()

        # Unicode madness
        try:
            cookie = str(cookie, 'utf-8')    # Python 3
        except TypeError:
            cookie = str(cookie)             # Python 2

        cookie = cookie.split("sid=")[-1]

        if not _cookie_sid_pattern.match(cookie):
            print("Wrong username or password.")
            return None

        return cookie



def on_whitelisted_host(name):
    """Check if we are on a whitelisted host"""
    if name == "lyon":
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            return False
        return ip.startswith("134.158.")
    if name == "jupyter":
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            return False
        return ip == socket.gethostbyname("jupyter.km3net.de")
    if name == "gitlab":
        external_ip = urlopen("https://ident.me").read().decode("utf8")
        return external_ip == "131.188.161.155"
