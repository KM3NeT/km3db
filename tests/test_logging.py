import unittest
import logging
import km3db


class TestLogging(unittest.TestCase):
    def test_get_logger(self):
        log = km3db.logger.get_logger("km3db")

    def test_logs(self):
        log = km3db.logger.get_logger("km3db")
        log.debug("a debug message")
        log.info("an info message")
        log.warning("a warning")
        log.error("an error")
        log.critical("a critical error")

    def test_set_level(self):
        log = km3db.logger.get_logger("km3db")
