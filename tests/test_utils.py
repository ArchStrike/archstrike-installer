from __future__ import absolute_import
from asinstaller import shandle
import logging
import unittest
import sys
from cStringIO import StringIO
from asinstaller.utils import system


class TestUtilsSystem(unittest.TestCase):

    def test_output(self):
        command = 'sudo pacman -Syy'
        system(command)
        self.assertTrue('downloading archstrike-testing.db...'in shandle.stream.getvalue())
