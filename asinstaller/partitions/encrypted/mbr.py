from ...utils import system, system_output
from ...config import usr_cfg, get_logger

__all__ = ["format"]
logger = get_logger(__name__)


def format():
    system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n2\n\n\nw" | '
           f'fdisk {usr_cfg["drive"]}')

    usr_cfg['boot'] = system_output("fdisk -l | "
                                    f"grep {usr_cfg['drive'][-3:]} | "
                                    "awk '{ if (NR==2) print substr ($1,6) }' ")
    usr_cfg['root'] = system_output("fdisk -l | "
                                    f"grep {usr_cfg['drive'][-3:]} |  "
                                    "awk '{ if (NR==3) print substr ($1,6) }' ")
