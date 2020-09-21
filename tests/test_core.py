import unittest

from km3db import DBManager
from km3db.core import on_whitelisted_host, SESSION_COOKIES


class TestKM3DB(unittest.TestCase):
    def test_init(self):
        DBManager()

    def test_whitelisted_hosts(self):
        for host, cookie in SESSION_COOKIES.items():
            if on_whitelisted_host(host):
                assert DBManager().session_cookie == cookie
