import unittest

from km3db import DBManager


class TestKM3DB(unittest.TestCase):
    def test_init(self):
        DBManager()
