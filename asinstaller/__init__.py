import platform
import logging
import signal
import json
import os

import install
from . import menus
from .config import *
from .utils import *
from .irc import LogHandler
from partitions import devices, auto, encrypted, manual

# Load Config
try:
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE) as fr:
            usr_cfg = json.loads(fr)
except:
    pass  # don't care about this

signal.signal(signal.SIGINT, signal_handler)
