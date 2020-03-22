
from . import gpt
from . import mbr
from ... import menus
from ...utils import system
from ...config import usr_cfg, setup_logger


logger = setup_logger(__name__)


def partition():
    system("sgdisk --zap-all {0}".format(usr_cfg['drive']))

    if usr_cfg['gpt']:
        if usr_cfg['uefi']:
            gpt.uefi()
        else:
            gpt.non_uefi()
    else:
        mbr.format()

    # Create Boot Partition
    system("wipefs -afq /dev/{0}".format(usr_cfg['boot']))
    if usr_cfg['uefi']:
        system("mkfs.vfat -F32 /dev/{0}".format(usr_cfg['boot']))
    else:
        system("mkfs.ext4 /dev/{0}".format(usr_cfg['boot']))

    # Create Root Partition
    system("wipefs -afq /dev/{0}".format(usr_cfg['root']))
    if usr_cfg['filesystem'] == 'jfs' or usr_cfg['filesystem'] == 'reiserfs':
        system('echo -e "y" | mkfs.{0} /dev/{1}'.format(usr_cfg['filesystem'],
            usr_cfg['root']))
    else:
        system('mkfs.{0} /dev/{1}'.format(usr_cfg['filesystem'],
            usr_cfg['root']))

    system("mount /dev/{0} /mnt".format(usr_cfg['root']))
    system("mkdir -p /mnt/boot")
    system("mount /dev/{0} /mnt/boot".format(usr_cfg['boot']))
