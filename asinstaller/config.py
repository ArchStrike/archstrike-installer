import os
import logging

usr_cfg = {}

pacmanconf = "/etc/pacman.conf"
archstrike_mirrorlist = "/etc/pacman.d/archstrike-mirrorlist"
LOG_FILE = '/tmp/archstrike-installer.log'

CONFIG_FILE = '/tmp/as-config.json'

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

class WhitespaceRemovingFormatter(logging.Formatter):
    def format(self, record):
        record.msg = record.msg.strip()
        return super(WhitespaceRemovingFormatter, self).format(record)

def setup_logger(filename):
    logger = logging.getLogger(filename)
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(LOG_FILE, mode='a+')
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(WhitespaceRemovingFormatter('%(message)s'))
    logger.addHandler(console)

    return logger
