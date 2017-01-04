import time
from asinstaller.utils import *
from asinstaller.config import usr_cfg
from asinstaller import menus

logger = logging.getLogger(__name__)

def partition_menu():
    logger.debug("Partition Menu")
    while True:
        system("clear")
        print_title("Step 2) Partition Menu")

        options = menus.partition_methods.keys()
        options.sort()
        for k in options:
            print_info('{0}) {1}'.format(k, menus.partition_methods[k]))

        part = cinput("> Choice: ", COLORS['OKBLUE'])

        try:
            if menus.partition_methods[part]:
                usr_cfg['partition_type'] = part
                break
        except KeyError:
            print_error("Invalid Option")
            time.sleep(1)


def identify():
    logger.debug("Identifying Devices")
    while True:
        system("clear")
        print_title("Step 3) HDD Preparation")
        system("swapoff -a")
        print_info("Current Devices")
        system(''' lsblk -p | grep "disk" | awk '{print $1" "$4}' ''')
        available_drives = system_output('lsblk -p | grep "disk" | '\
                            + "awk '{print $1}' ").split('\n')
        drive = cinput('> Please choose the drive you would like to '\
                    + 'install ArchStrike on (default: /dev/sda ): ', \
                    COLORS['OKBLUE']) or '/dev/sda'

        if drive not in available_drives:
            print_error("That drive does not exist")
            time.sleep(1)
            continue

        if not query_yes_no('Are you sure want to use '\
            + '{1}?'.format(COLORS['WARNING'], drive),
            'yes'):
            continue
        break

    drive_size = system_output("lsblk -p | grep -w %s | ".format(drive) \
            + "awk '{print $4}' | grep -o '[0-9]*' | awk 'NR==1' ")

    usr_cfg['drive'] = drive
    usr_cfg['drive_size'] = drive_size


def set_filesystem():
    logger.debug("Setting Filesystem Type")
    while True:
        system("clear")
        print_title("Step 4) Selecting the Filesystem Type")

        options = menus.filesystems.keys()
        options.sort()
        for k in options:
            print_info('{0}) {1}'.format(k, menus.filesystems[k]))

        try:
            fsc = cinput('> Choice (Default is ext4):', COLORS['OKBLUE']) or '1'
            if menus.filesystems[fsc]:
                usr_cfg['filesystem'] = fsc
                logger.log(logging.INFO, "Filesystem type: {0}".format(fsc))
                break
        except KeyError:
            print_error("Invalid Option")
            time.sleep(1)


def set_swap():
    logger.debug("Setting Swap")
    while True:
        system("clear")
        if query_yes_no("> Step 5) Would you like to create a new swap space?",
                        'yes'):
            swap_space = cinput('> Enter your swap space size '\
                        + '(default is 512M): ', COLORS['OKBLUE']) or '512M'
            logger.log(logging.INFO, "Swap Size: {0}".format(swap_space))
            size = swap_space[:-1]
            if swap_space[-1] == "M":
                if int(size) >= (int(drive_size)*1024 - 4096):
                    print_error("Your swap space is too large")
                    time.sleep(1)
                break
            elif swap_space[-1] == "G":
                if int(size) >= (int(drive_size) - 4):
                    print_error("Your swap space is too large")
                    time.sleep(1)
                break
            else:
                print_error("Swap space must be in M or G")
                time.sleep(1)
        else:
            swap_space = None
            break
    usr_cfg['swap_space'] = swap_space


def set_gpt():
    logger.debug("Setting GPT")
    system("clear")
    if not usr_cfg['uefi']:
        if query_yes_no('> Step 6) Would you like to use GUID Partition '\
            + 'Table?', 'no'):
            usr_cfg['gpt'] = True
        else:
            usr_cfg['gpt'] = False


def confirm_settings():
    logger.debug("Confirm Settings")
    system("clear")
    print_info('Device: {0}\n'.format(usr_cfg['drvie']) \
               + 'Filesystem: {0}\n'.format(usr_cfg['filesystem']) \
               + 'Swap: {0}'.format(usr_cfg['swap_space']))

    if query_yes_no("> Are you sure your partitions are set up correctly?",
                    'yes'):
        return True
    else:
        return False


def check_lvm():
    logger.debug("Checking LVM")
    system_output('pvscan')
    system_output('vgscan')
    lvscan = system_output('lvscan')

    if lvscan:
        for entry in lvscan.rstrip().split('\n'):
            lvm_dir = entry.split("'")[1]
            system("echo -e 'y'|lvm lvremove {0}".format(lvm_dir))
