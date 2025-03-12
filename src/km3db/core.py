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
from urllib.error import URLError, HTTPError
from http.client import IncompleteRead, RemoteDisconnected
import socket
import pytz
import time
from urllib.parse import unquote
import urllib.request

from km3db.logger import log


BASE_URL = "https://km3netdbweb.in2p3.fr"
COOKIE_FILENAME = os.path.expanduser("~/.km3netdb_cookie")
SESSION_COOKIES = dict(
    gitlab="_gitlab-km3net_131.188_ce0e106433dd4923b522716b23c992c2",
)
UTC_TZ = pytz.timezone("UTC")

_cookie_sid_pattern = re.compile(r"_[a-z0-9-]+_(\d{1,3}.){1,3}\d{1,3}_[a-z0-9]+")

# Ignore invalid certificate error
ssl._create_default_https_context = ssl._create_unverified_context

original_getaddrinfo = socket.getaddrinfo


def ipv4_forced_getaddrinfo(*args, **kwargs):
    responses = original_getaddrinfo(*args, **kwargs)
    return [res for res in responses if res[0] == socket.AF_INET]


# Monkey patch to force IPv4
socket.getaddrinfo = ipv4_forced_getaddrinfo


class AuthenticationError(Exception):
    pass


class DBManager:
    """
    Handles login and session management to the KM3NeT DB.
    """

    def __init__(self, url=None, network_class=None):
        self._db_url = BASE_URL if url is None else url
        self._login_url = self._db_url + "/home.htm"
        self._network_class = network_class
        self._session_cookie = None
        self._opener = None
        self._username = None

    def get(self, url, default=None, retries=10, binary=False):
        "Get HTML content"
        target_url = self._db_url + "/" + unquote(url)
        log.debug("Accessing %s", target_url)
        try:
            f = self.opener.open(target_url)
        except HTTPError as e:
            if e.code in (401, 403):
                if retries:
                    log.error(
                        "Access forbidden (error %d), your session has expired. "
                        "Deleting the cookie (%s) and retrying once.",
                        e.code,
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
        except URLError as e:
            if retries:
                retries -= 1
                log.error("URLError '%s', retrying in 30 seconds.", e)
                time.sleep(30)
                return self.get(url, default=default, retries=retries)
            else:
                log.error("Giving up... URLError: %s\n" "Target URL: %s", e, target_url)
                return default
        except RemoteDisconnected as e:
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
        except IncompleteRead as icread:
            log.error("Incomplete data received from the DB.")
            content = icread.partial
        log.debug("Got {0} bytes of data.".format(len(content)))

        if binary:
            return content
        else:
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
        # The cookie can be specified via the environment
        cookie = os.getenv("KM3NET_DB_COOKIE")
        if cookie is not None:
            log.info("Using cookie from env ($KM3NET_DB_COOKIE)")
            # splitting and returning the last part, just in case
            # someone has the full string in the env var (not only the
            # sid value)
            return cookie.split()[-1].strip()

        # The cookie file can also be specified via the environment
        cookiefile = os.getenv("KM3NET_DB_COOKIE_FILE")
        if cookiefile is not None:
            log.info("Using cookie file from env ($KM3NET_DB_COOKIE_FILE)")
            with open(cookiefile) as fobj:
                content = fobj.read()
            return content.split()[-1].strip()

        # Next, try the configuration file according to
        # the specification described here:
        # https://wiki.km3net.de/index.php/Database#Scripting_access
        if os.path.exists(COOKIE_FILENAME):
            log.info("Using cookie from standard location %s", COOKIE_FILENAME)
            # TODO: code duplication, see above
            with open(COOKIE_FILENAME) as fobj:
                content = fobj.read()
            return content.split()[-1].strip()

        # If everything fails, ask the user for credentials to generate a cookie
        return self.request_session_cookie()

    def request_session_cookie(self):
        """Request a cookie using credentials"""
        username = os.getenv("KM3NET_DB_USERNAME")
        password = os.getenv("KM3NET_DB_PASSWORD")

        if username is None or password is None:
            # Last resort: we ask interactively
            username = input("Please enter your KM3NeT DB username: ")
            password = getpass.getpass("Password: ")
        else:
            log.info(
                "Using credentials from env ($KM3NET_DB_USERNAME and "
                "$KM3NET_DB_PASSWORD)"
            )

        suffix = ""
        if self._network_class is not None:
            if self._network_class == "B":
                suffix = "&freenetbits=16"
            elif self._network_class == "C":
                suffix = "&freenetbits=8"
            else:
                log.error("Unsupported network class '{}'".format(self._network_class))
        target_url = self._login_url + "?usr={0}&pwd={1}&persist=y{2}".format(
            username, password, suffix
        )
        cookie = urllib.request.urlopen(target_url).read()

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
            opener = urllib.request.build_opener()
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

    @property
    def username(self):
        if self._username is None:
            self._username = self.session_cookie.split("_")[1]
        return self._username


def on_whitelisted_host(name):
    """Check if we are on a whitelisted host"""
    if name == "gitlab":
        return "GITLAB_CI" in os.environ
