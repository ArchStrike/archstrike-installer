
from asinstaller import shandle
import os
import logging
import unittest
import sys
from io import StringIO
from asinstaller.config import CRASH_FILE, LOG_FILE
from asinstaller.utils import system, Crash


class TestUtilsSystem(unittest.TestCase):

    def test_output(self):
        command = 'sudo pacman -Syy'
        system(command)
        self.assertTrue('downloading community.db...'in shandle.stream.getvalue())


class TestUtilsGetCrashHistory(unittest.TestCase):

    def tearDown(self):
        for fname in [CRASH_FILE, LOG_FILE]:
            if os.path.exists(fname):
                os.remove(fname)

    def test_no_crash(self):
        version = '2.1.9'
        no_crash = Crash(version)
        self.assertFalse(bool(no_crash))

    def test_base_and_inductive_step(self):
        version = '2.1.9'
        try:
            raise Exception('woops!')
        except Exception:
            crash1 = Crash(version)
            crash1.log_as_reported()
            crash2 = Crash(version)
        # check submission id deduplicated
        self.assertTrue(crash1.submission_id == crash2.submission_id)
        # check xs_trace is same
        self.assertTrue(crash1 == crash2)
        try:
            raise Exception('woops 2!')
        except Exception:
            crash3 = Crash(version)
        self.assertTrue(crash1 != crash3)
        self.assertTrue(crash1.submission_id != crash3.submission_id)

    def test_invalid_input(self):
        version = '2.1.9'
        try:
            raise Exception('woops!')
        except Exception:
            crash_empty = Crash(version)
            crash1 = Crash(version)
