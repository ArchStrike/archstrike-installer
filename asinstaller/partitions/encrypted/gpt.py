from ...utils import system, system_output
from ...config import usr_cfg, get_logger

__all__ = ["uefi", "non_uefi"]
logger = get_logger(__name__)


def uefi():
    system('echo -e "n\n\n\n512M\nef00\nn\n\n\n\n\nw\ny" | ' \
            + 'gdisk {0}'.format(usr_cfg['drive']))

    usr_cfg['boot'] = system_output("fdisk -l | " \
                + "grep {0} | ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==2) print substr ($1,6) }' ")
    usr_cfg['root'] = system_output("fdisk -l | " \
                + "grep {0} |  ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==3) print substr ($1,6) }' ")


def non_uefi():
    system('echo -e "o\ny\nn\n1\n\n+100M\n\nn\n2\n\n+1M\nEF02\nn' \
            + '\n3\n\n\n\nw\ny" | gdisk {0}'.format(usr_cfg['drive']))

    usr_cfg['boot'] = system_output("fdisk -l | " \
                + "grep {0} | ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==4) print substr ($1,6) }' ")
    usr_cfg['root'] = system_output("fdisk -l | " \
                + "grep {0} |  ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==2) print substr ($1,6) }' ")
