
from asinstaller import shandle
import os
import logging
import unittest
import sys
from io import StringIO
from asinstaller.config import CRASH_FILE, LOG_FILE
from asinstaller.utils import system, get_crash_history


class TestUtilsSystem(unittest.TestCase):

    def test_output(self):
        command = 'sudo pacman -Syy'
        system(command)
        self.assertTrue('downloading archstrike-testing.db...'in shandle.stream.getvalue())


class TestUtilsCrash(unittest.TestCase):

    def tearDown(self):
        for fname in [CRASH_FILE, LOG_FILE]:
            if os.path.exists(fname):
                os.remove(fname)

    def test_get_crash_history(self):
        version = '2.1.9'
        crash_history_empty = get_crash_history(version)
        try:
            raise Exception('woops!')
        except Exception:
            crash_history1 = get_crash_history(version)
            crash_history2 = get_crash_history(version)
        try:
            raise Exception('woops 2!')
        except Exception:
            crash_history3 = get_crash_history(version)
        self.assertEqual(0, len(crash_history_empty))
        self.assertEqual(1, len(crash_history1))
        self.assertEqual(2, len(crash_history2))
        self.assertTrue(crash_history1[0] == crash_history1[-1])
        self.assertFalse(crash_history2[0] == crash_history2[-1])
        self.assertTrue(crash_history2[0].baseid == crash_history2[-1].baseid)
        self.assertTrue(crash_history1[0] == crash_history2[-1])
        # now check file overwritten on crash from different line no
        self.assertTrue(crash_history3[0] != crash_history2[0])
        self.assertTrue(crash_history3[1].baseid == crash_history2[0].baseid)
