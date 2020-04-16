
from asinstaller.utils import *
from asinstaller.config import usr_cfg, get_logger

logger = get_logger(__name__)

def format():
    if usr_cfg['swap_space']:
        system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n3\n\n' \
            +'+{0}\nt\n\n82\nn\np\n2\n\n\nw"'.format(usr_cfg['swap_space']) \
            +' | fdisk {0}'.format(usr_cfg['drive']))
        SWAP = system_output("fdisk -l | " \
                    + " grep {0}".format(usr_cfg['drive'][-3:]) \
                    + " |  awk '{ if (NR==4) print substr ($1,6) }'")
        system("wipefs -afq /dev/{0}".format(SWAP))
        system("mkswap /dev/{0}".format(SWAP))
        system("swapon /dev/{0}".format(SWAP))
        usr_cfg['swap'] = SWAP
    else:
        system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n2\n\n\nw" | ' \
               + 'fdisk {0}'.format(usr_cfg['drive']))

    usr_cfg['boot'] = system_output("fdisk -l | " \
                + "grep {0} | ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==2) print substr ($1,6) }' ")
    usr_cfg['root'] = system_output("fdisk -l | " \
                + "grep {0} |  ".format(usr_cfg['drive'][-3:]) \
                + "awk '{ if (NR==3) print substr ($1,6) }' ")
