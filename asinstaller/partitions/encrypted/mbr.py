from asinstaller.utils import *
from asinstaller.config import usr_cfg, setup_logger

logger = setup_logger(__name__)

def format():
    system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n2\n\n\nw" | ' \
       + 'fdisk {0}'.format(usr_cfg['drive']))

    usr_cfg['boot'] = system_output("fdisk -l | " \
                + "grep {0} | ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==2) print substr ($1,6) }' ")
    usr_cfg['root'] = system_output("fdisk -l | " \
                + "grep {0} |  ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==3) print substr ($1,6) }' ")
