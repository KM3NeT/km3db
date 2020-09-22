#!/usr/bin/env python3

import unittest

from km3db import StreamDS


class TestStreamDS(unittest.TestCase):
    def test_init(self):
        StreamDS()

    def test_print_streams(self):
        sds = StreamDS()
        sds.print_streams()
