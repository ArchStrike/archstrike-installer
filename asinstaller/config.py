import io
import logging
import os
from pathlib import Path

__all__ = ["pacmanconf", "archstrike_mirrorlist", "CRASH_FILE", "LOG_FILE", "CONFIG_FILE", "IRC_SERVER", "IRC_PORT",
           "IRC_BOT_NICK", "COLORS", "localesdict", "FNULL", "TOPLEVEL_NAME", "usr_cfg", "WhitespaceRemovingFormatter",
           "init_logger_handles", "get_logger", "load_user_cfg", "dump_user_cfg"]



pacmanconf = "/etc/pacman.conf"
archstrike_mirrorlist = "/etc/pacman.d/archstrike-mirrorlist"
CRASH_FILE = '/tmp/archstrike-installer-crash-report.lock'
LOG_FILE = '/tmp/archstrike-installer.log'
CONFIG_FILE = Path('/tmp/as-config.json')
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


FNULL = open(os.devnull, 'w')  # TODO, oh my... resource acquisition and initialization please...
TOPLEVEL_NAME = 'asinstaller'

usr_cfg = {}


class WhitespaceRemovingFormatter(logging.Formatter):
    def format(self, record):
        record.msg = record.msg.strip()
        return super(WhitespaceRemovingFormatter, self).format(record)


def init_logger_handles():
    """scopes loggers by package.filename, scope collision is an accepted flaw"""
    FHANDLE_NAME = 'Installer Log'
    SHANDLE_NAME = 'Unit Test String Buffer'
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.NOTSET)
    top_logger = logging.getLogger(TOPLEVEL_NAME)
    if all([hndlr.name not in set([FHANDLE_NAME, SHANDLE_NAME]) for hndlr in top_logger.handlers]):
        top_logger.setLevel(logging.DEBUG)  # NOTSET only traverses until another level is found, so DEBUG is preferred
        # add a file handler to LOG_FILE, handle for standard io (stdio_handle), and a handle for units (shandle)
        fhandle = logging.FileHandler(LOG_FILE, mode='a+')
        fhandle.name = FHANDLE_NAME
        fhandle.setLevel(logging.DEBUG)
        shandle = logging.StreamHandler(io.StringIO())
        shandle.name = SHANDLE_NAME
        shandle.setLevel(logging.DEBUG)
        stdio_handle = logging.StreamHandler()
        stdio_handle.setLevel(logging.INFO)
        fmt = logging.Formatter(fmt='%(levelname)s - %(message)s', datefmt='%m-%d %H:%M')
        fhandle.setFormatter(fmt)
        shandle.setFormatter(fmt)
        stdio_handle.setFormatter(fmt)
        top_logger.addHandler(fhandle)
        top_logger.addHandler(shandle)
        top_logger.addHandler(stdio_handle)


def get_logger(filename):
    return logging.getLogger(f'{TOPLEVEL_NAME}.{filename}')


def load_user_cfg():
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as fr:
                usr_cfg = json.loads(fr)
    except json.decoder.JSONDecodeError:
        logger = get_logger(__file__)
        logger.warning(f"Found corrupt user config {CONFIG_FILE}")
        return {}
    except Exception:
        raise


def dump_user_cfg():
    try:
        logger = get_logger(__file__)
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as fr:
                usr_cfg = json.loads(fr)
    except TypeError as exc:
        import pdb; pdb.set_trace()
        logger.warning(f"User config ")
        return {}
    except Exception:
        raise
