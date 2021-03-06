from ...utils import system, system_output
from ...config import usr_cfg, get_logger

__all__ = ["format"]
logger = get_logger(__name__)


def format():
    if usr_cfg['swap_space']:
        system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n3\n\n'
               f'+{usr_cfg["swap_space"]}\nt\n\n82\nn\np\n2\n\n\nw"'
               f' | fdisk {usr_cfg["drive"]}')
        SWAP = system_output("fdisk -l | "
                             f" grep {usr_cfg['drive'][-3:]}"
                             " |  awk '{ if (NR==4) print substr ($1,6) }'")
        system(f"wipefs -afq /dev/{SWAP}")
        system(f"mkswap /dev/{SWAP}")
        system(f"swapon /dev/{SWAP}")
        usr_cfg['swap'] = SWAP
    else:
        system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n2\n\n\nw" | '
               f'fdisk {usr_cfg["drive"]}')

    usr_cfg['boot'] = system_output("fdisk -l | "
                                    f"grep {usr_cfg['drive'][-3:]} | "
                                    "awk '{ if (NR==2) print substr ($1,6) }' ")
    usr_cfg['root'] = system_output("fdisk -l | "
                                    f"grep {usr_cfg['drive'][-3:]} |  "
                                    "awk '{ if (NR==3) print substr ($1,6) }' ")
