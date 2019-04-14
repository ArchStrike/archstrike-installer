from __future__ import absolute_import
import cStringIO
import inspect
import logging
import os

usr_cfg = {}

pacmanconf = "/etc/pacman.conf"
archstrike_mirrorlist = "/etc/pacman.d/archstrike-mirrorlist"
LOG_FILE = '/tmp/archstrike-installer.log'
CONFIG_FILE = '/tmp/as-config.json'
IRC_SERVER = 'irc.freenode.net'
IRC_PORT = 6697
IRC_BOT_NICK = 'xorbot'
COLORS = {
    'HEADER': '\033[95m',
    'OKBLUE': '\033[94m',
    'OKGREEN': '\033[92m',
    'WARNING': '\033[93m',
    'FAIL': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m'
}

localesdict = {'1': 'en_US.UTF-8', '2': 'en_AU.UTF-8', '3': 'en_CA.UTF-8',
               '4': 'es_ES.UTF-8', '5': 'fr_FR.UTF-8', '6': 'de_DE.UTF-8',
               '7': 'en_GB.UTF-8', '8': 'en_MX.UTF-8', '9': 'pt_PT.UTF-8',
               '10': 'ro_RO.UTF-8', '11': 'ru_RU.UTF-8',
               '12': 'sv_SE.UTF-8'}

FNULL = open(os.devnull, 'w')


TOPLEVEL_NAME = 'asinstaller'  # imports 
FHANDLE_NAME = 'Installer Log'
SHANDLE_NAME = 'Unit Test String Buffer'
# by default the root logger is created with a log level of warning; gotta catch 'em all, so set to NOTSET
root_logger = logging.getLogger()
root_logger.setLevel(logging.NOTSET)
# asinstaller is the top-level logger and all modules follow the period-separated hierarchical structure. So,
# for all loggers asinstaller is an ancestor. Given messages are propagated to ancestors and their handles,
# it is sufficient to configure asinstaller.
logger = logging.getLogger(TOPLEVEL_NAME)
if all([hndlr.name not in set([FHANDLE_NAME, SHANDLE_NAME]) for hndlr in logger.handlers]) or True:
    logger.setLevel(logging.DEBUG)  # NOTSET only traverses until another level is found, so DEBUG is preferred
    # add a file handle to LOG_FILE (fhandle), handle for standard io (stdio_handle), and a handle for unit testing (shandle)
    fhandle = logging.FileHandler(LOG_FILE, mode='a+')
    fhandle.name = FHANDLE_NAME
    fhandle.setLevel(logging.DEBUG)
    shandle = logging.StreamHandler(cStringIO.StringIO())
    shandle.name = SHANDLE_NAME
    shandle.setLevel(logging.DEBUG)
    stdio_handle = logging.StreamHandler()
    stdio_handle.setLevel(logging.INFO)
    fmt = logging.Formatter(fmt='%(levelname)s - %(message)s', datefmt='%m-%d %H:%M')
    fhandle.setFormatter(fmt)
    shandle.setFormatter(fmt)
    stdio_handle.setFormatter(fmt)
    logger.addHandler(fhandle)
    logger.addHandler(shandle)
    logger.addHandler(stdio_handle)


logger = logging.getLogger(__name__)


class WhitespaceRemovingFormatter(logging.Formatter):
    def format(self, record):
        record.msg = record.msg.strip()
        return super(WhitespaceRemovingFormatter, self).format(record)



def setup_logger(filename):
    return logging.getLogger(filename)
