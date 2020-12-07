from asinstaller.utils import system, system_output
from asinstaller.config import usr_cfg, get_logger

__all__ = ["uefi", "non_uefi"]
logger = get_logger(__name__)

def uefi():
    if usr_cfg['swap_space']:
        system('echo -e "n\n\n\n512M\nef00\nn\n3\n\n' \
            + '+{0}\n8200\nn\n\n'.format(usr_cfg['swap_space']) \
            + '\n\n\nw\ny" | gdisk {0}'.format(usr_cfg['drive']))
        SWAP = system_output("fdisk -l | " \
                    + " grep {0}".format(usr_cfg['drive'][-3:]) \
                    + " |  awk '{ if (NR==4) print substr ($1,6) }'")
        system("wipefs -afq /dev/{0}".format(SWAP))
        system("mkswap /dev/{0}".format(SWAP))
        system("swapon /dev/{0}".format(SWAP))
        usr_cfg['swap'] = SWAP
    else:
        system('echo -e "n\n\n\n512M\nef00\nn\n\n\n\n\nw\ny" | ' \
            + 'gdisk {0}'.format(usr_cfg['drive']))

    usr_cfg['boot'] = system_output("fdisk -l | " \
                + "grep {0} | ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==2) print substr ($1,6) }' ")
    usr_cfg['root'] = system_output("fdisk -l | " \
                + "grep {0} |  ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==3) print substr ($1,6) }' ")


def non_uefi():
    if usr_cfg['swap_space']:
        system('echo -e "o\ny\nn\n1\n\n+100M\n\nn\n2\n\n+1M\nEF02\nn\n4\n\n' \
            + '+{0}\n8200\nn'.format(usr_cfg['swap_space']) \
            + '\n3\n\n\n\nw\ny" | gdisk {0}'.format(usr_cfg['drive']))
        SWAP = system_output("fdisk -l | " \
                    + " grep {0}".format(usr_cfg['drive'][-3:]) \
                    + " |  awk '{ if (NR==5) print substr ($1,6) }'")
        system("wipefs -afq /dev/{0}".format(SWAP))
        system("mkswap /dev/{0}".format(SWAP))
        system("swapon /dev/{0}".format(SWAP))
        usr_cfg['swap'] = SWAP
    else:
        system('echo -e "o\ny\nn\n1\n\n+100M\n\nn\n2\n\n+1M\nEF02\nn' \
            + '\n3\n\n\n\nw\ny" | gdisk {0}'.format(usr_cfg['drive']))

    usr_cfg['boot'] = system_output("fdisk -l | " \
                + "grep {0} | ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==2) print substr ($1,6) }' ")
    usr_cfg['root'] = system_output("fdisk -l | " \
                + "grep {0} |  ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==4) print substr ($1,6) }' ")
