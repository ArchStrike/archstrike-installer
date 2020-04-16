
from getpass import getpass
from . import gpt
from . import mbr
from ...utils import *
from ...config import usr_cfg, get_logger


logger = get_logger(__name__)


def partition():
    print_warning("WARNING! This will encrypt {0}".format(usr_cfg['drive']))
    if not query_yes_no("> Continue?", 'no'):
        return

    pass_set = False
    while not pass_set:
        passwd = getpass('> Please enter a new password for ' \
            '{0}: '.format(usr_cfg['drive']))
        passwd_chk = getpass("> Confirm password: ")
        if passwd == passwd_chk:
            pass_set = True
        else:
            print_error("Password do not Match.")
    del passwd_chk

    if usr_cfg['gpt']:
        if usr_cfg['uefi']:
            gpt.uefi()
        else:
            gpt.non_uefi()
    else:
        mbr.format()

    system("wipefs -afq /dev/{0}".format(usr_cfg['root']))
    system("wipefs -afq /dev/{0}".format(usr_cfg['boot']))

    system("lvm pvcreate /dev/{0}".format(usr_cfg['root']))
    system("lvm vgcreate lvm /dev/{0}".format(usr_cfg['root']))

    if usr_cfg['swap_space']:
        system("lvm lvcreate -L {0} -n swap lvm ".format(usr_cfg['swap_space']))

    system("lvm lvcreate -L 500M -n tmp lvm")
    system("echo -e 'y' | lvm lvcreate -l 100%FREE -n lvroot lvm")

    system('printf {0} | '.format(passwd) \
        + 'cryptsetup luksFormat -c aes-xts-plain64 -s 512 /dev/lvm/lvroot -')
    system('printf {0} | '.format(passwd) \
        + 'cryptsetup open --type luks /dev/lvm/lvroot root -')
    del passwd
    system("wipefs -afq /dev/mapper/root")
    if usr_cfg['filesystem'] == 'jfs' or usr_cfg['filesystem'] == 'reiserfs':
        system('echo -e "y" | mkfs.{0} '.format(usr_cfg['filesystem']) \
            + '/dev/mapper/root')
    else:
        system('mkfs.{0} /dev/mapper/root'.format(usr_cfg['filesystem']))

    if usr_cfg['uefi']:
        system("mkfs.vfat -F32 /dev/{0}".format(usr_cfg['boot']))
    else:
        system("wipefs -afq /dev/{0}".format(usr_cfg['boot']))
        system("mkfs.ext4 /dev/{0}".format(usr_cfg['boot']))

    system("mount /dev/mapper/root /mnt")
    system("mkdir -p /mnt/boot")
    system("mount /dev/{0} /mnt/boot".format(usr_cfg['boot']))
