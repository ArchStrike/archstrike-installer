import os
import io
import logging
import unittest
from asinstaller import __version__
from asinstaller.config import CRASH_FILE, LOG_FILE
from asinstaller.utils import system, Crash, satisfy_dep

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
shandle = logging.StreamHandler(io.StringIO())
shandle.name = 'Unit Test String Buffer'
shandle.setLevel(logging.DEBUG)
logger.addHandler(shandle)

version = __version__


class TestUtilsSystem(unittest.TestCase):

    def test_output(self):
        command = 'sudo pacman -Syy'
        system(command)
        self.assertTrue('downloading community.db...' in shandle.stream.getvalue())


class TestUtilsGetCrashHistory(unittest.TestCase):

    def tearDown(self):
        for fname in [CRASH_FILE, LOG_FILE]:
            if os.path.exists(fname):
                os.remove(fname)

    def test_0_no_crash(self):
        no_crash = Crash(version)
        self.assertFalse(bool(no_crash))

    def test_1_crash_file(self):
        try:
            raise Exception('woops!')
        except Exception:
            crash = Crash(version)
            crash.log_as_reported()
            fcrash = Crash.from_crash_file()
        self.assertTrue(crash == fcrash)
        self.assertTrue(crash.submission_id == fcrash.submission_id)

    def test_2_base_and_inductive_step(self):
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


@unittest.skipIf(os.geteuid() != 0, 'satisfy_dep invokes pacman -Fs, which requires root permissions. Hence, skip')
class TestSatisfyDep(unittest.TestCase):
    def test_failed_to_locate(self):
        with self.assertRaises(Exception):
            satisfy_dep('feefiefoefoobar')

    def test_successful_locate(self):
        self.assertTrue(satisfy_dep('bash') is None)
