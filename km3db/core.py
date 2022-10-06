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
import time

from km3db.logger import log
import km3db.compat

# Ignore invalid certificate error
ssl._create_default_https_context = ssl._create_unverified_context

BASE_URL = "https://km3netdbweb.in2p3.fr"
COOKIE_FILENAME = os.path.expanduser("~/.km3netdb_cookie")
SESSION_COOKIES = dict(
    lyon="_kmcprod_134.158_lyo7783844001343100343mcprod1223user",
    jupyter="_jupyter-km3net_131.188.161.143_d9fe89a1568a49a5ac03bdf15d93d799",
    gitlab="_gitlab-km3net_131.188_ce0e106433dd4923b522716b23c992c2",
)
UTC_TZ = pytz.timezone("UTC")

_cookie_sid_pattern = re.compile(r"_[a-z0-9-]+_(\d{1,3}.){1,3}\d{1,3}_[a-z0-9]+")


class AuthenticationError(Exception):
    pass


class DBManager:
    def __init__(self, url=None):
        self._db_url = BASE_URL if url is None else url
        self._login_url = self._db_url + "/home.htm"
        self._session_cookie = None
        self._opener = None

    def get(self, url, default=None, retries=10):
        "Get HTML content"
        target_url = self._db_url + "/" + km3db.compat.unquote(url)
        log.debug("Accessing %s", target_url)
        try:
            f = self.opener.open(target_url)
        except km3db.compat.HTTPError as e:
            if e.code == 403:
                if retries:
                    log.error(
                        "Access forbidden, your session has expired. "
                        "Deleting the cookie (%s) and retrying once.",
                        COOKIE_FILENAME,
                    )
                    retries -= 1
                else:
                    log.critical("Access forbidden. Giving up...")
                    return default
                time.sleep(1)
                self.reset()
                if os.path.exists(COOKIE_FILENAME):
                    os.remove(COOKIE_FILENAME)
                return self.get(url, default=default, retries=retries)
            log.error("HTTP error: %s\n" "Target URL: %s", e, target_url)
            return default
        except km3db.compat.URLError as e:
            if retries:
                retries -= 1
                log.error("URLError '%s', retrying in 30 seconds.", e)
                time.sleep(30)
                return self.get(url, default=default, retries=retries)
            else:
                log.error("Giving up... URLError: %s\n" "Target URL: %s", e, target_url)
                return default
        except km3db.compat.RemoteDisconnected as e:
            if retries:
                retries -= 1
                log.error("RemoteDisconnected '%s', retrying in 30 seconds.", e)
                time.sleep(30)
                return self.get(url, default=default, retries=retries)
            else:
                log.error(
                    "Giving up... RemoteDisconnected: %s\n" "Target URL: %s",
                    e,
                    target_url,
                )
                return default
        try:
            content = f.read()
        except km3db.compat.IncompleteRead as icread:
            log.error("Incomplete data received from the DB.")
            content = icread.partial
        log.debug("Got {0} bytes of data.".format(len(content)))

        return content.decode("utf-8")

    def reset(self):
        "Reset everything"
        self._opener = None
        self._session_cookie = None

    @property
    def session_cookie(self):
        if self._session_cookie is None:
            for host, session_cookie in SESSION_COOKIES.items():
                if on_whitelisted_host(host):
                    self._session_cookie = session_cookie
                    break
            else:
                self._session_cookie = self._request_session_cookie()
        return self._session_cookie

    def _request_session_cookie(self):
        """Request cookie for permanent session."""
        # Next, try the configuration file according to
        # the specification described here:
        # https://wiki.km3net.de/index.php/Database#Scripting_access
        if os.path.exists(COOKIE_FILENAME):
            log.info("Using cookie from %s", COOKIE_FILENAME)
            with open(COOKIE_FILENAME) as fobj:
                content = fobj.read()
            return content.split()[-1].strip()

        # The cookie can also be set via the environment
        cookie = os.getenv("KM3NET_DB_COOKIE")
        if cookie is not None:
            log.info("Using cookie from env ($KM3NET_DB_COOKIE)")
            return cookie

        username = os.getenv("KM3NET_DB_USERNAME")
        password = os.getenv("KM3NET_DB_PASSWORD")

        if username is None or password is None:
            # Last resort: we ask interactively
            username = km3db.compat.user_input("Please enter your KM3NeT DB username: ")
            password = getpass.getpass("Password: ")
        else:
            log.info(
                "Using credentials from env ($KM3NET_DB_USERNAME and "
                "$KM3NET_DB_PASSWORD)"
            )

        target_url = self._login_url + "?usr={0}&pwd={1}&persist=y".format(
            username, password
        )
        cookie = km3db.compat.urlopen(target_url).read()

        # Unicode madness
        try:
            cookie = str(cookie, "utf-8")  # Python 3
        except TypeError:
            cookie = str(cookie)  # Python 2

        cookie = cookie.split("sid=")[-1]

        if not _cookie_sid_pattern.match(cookie):
            message = "Wrong username or password."
            log.critical(message)
            raise AuthenticationError(message)

        log.info("Writing session cookie to %s", COOKIE_FILENAME)
        with open(COOKIE_FILENAME, "w") as fobj:
            fobj.write(".in2p3.fr\tTRUE\t/\tTRUE\t0\tsid\t{}".format(cookie))

        return cookie

    @property
    def opener(self):
        "A reusable connection manager"
        if self._opener is None:
            log.debug("Creating connection handler")
            opener = km3db.compat.build_opener()
            cookie = self.session_cookie
            if cookie is None:
                log.critical("Could not connect to database.")
                return
            opener.addheaders.append(("Cookie", "sid=" + cookie))
            log.debug("Using session cookie: sid=%s", cookie)
            self._opener = opener
        else:
            log.debug("Reusing connection manager")
        return self._opener


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
        return "GITLAB_CI" in os.environ
