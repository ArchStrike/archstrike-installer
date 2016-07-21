#!/usr/bin/env python2
from getpass import getpass
import subprocess as sp
import logging
import signal
import select
import urllib2
import platform
import time
import sys
import os

pacmanconf = "/etc/pacman.conf"
archstrike_mirrorlist = "/etc/pacman.d/archstrike-mirrorlist"
log_file = '/tmp/archstrike-installer.log'

logger = logging.getLogger('ArchStrike-Installer')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler(log_file, mode='w')
formatter = logging.Formatter('%(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(console)

COLORS = {
    'HEADER' : '\033[95m',
    'OKBLUE' : '\033[94m',
    'OKGREEN' : '\033[92m',
    'WARNING' : '\033[93m',
    'FAIL' : '\033[91m',
    'ENDC' : '\033[0m',
    'BOLD' : '\033[1m',
    'UNDERLINE' : '\033[4m'
}


def print_error(msg):
    print('''{0}{1}{2}'''.format(COLORS['FAIL'],msg, COLORS['ENDC']))

def print_warning(msg):
    print('''{0}{1}{2}'''.format(COLORS['HEADER'],msg, COLORS['ENDC']))

def print_command(msg):
    print('''{0}{1}{2}'''.format(COLORS['OKBLUE'],msg, COLORS['ENDC']))

def print_title(msg):
    print('''{0}{1}{2}'''.format(COLORS['HEADER'],msg, COLORS['ENDC']))

def print_info(msg):
    print('''{0}{1}{2}'''.format(COLORS['OKGREEN'],msg, COLORS['ENDC']))

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "Y": True,
             "no": False, "n": False, "N": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write('{0}{1}{2}{3}'.format(COLORS['OKBLUE'],question,prompt,COLORS['ENDC']))
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("{0}Please respond with 'yes' or 'no' (or 'y' or 'n').\n{1}".format(COLORS['FAIL'],COLORS['ENDC']))

def signal_handler(signal, handler):
    sp.Popen("umount -R /mnt", stdout=FNULL, stderr=sp.STDOUT, shell=True)
    FNULL.close()
    print_info("\n\nGood Bye")
    sys.exit()

def system(command, chroot=False, **kwargs):

    if chroot:
        command = "arch-chroot /mnt {0}".format(command)

    # don't log clear or encryption passwd
    if command == 'clear' or command.find('printf') != -1 or command.find('passwd') != -1:
        return sp.call([command], shell=True)

    child = sp.Popen([command], stdout=sp.PIPE, stderr=sp.PIPE, shell=True, **kwargs)

    logger.log(logging.DEBUG, command)

    poll = select.poll()
    poll.register(child.stdout, select.POLLIN | select.POLLHUP)
    poll.register(child.stderr, select.POLLIN | select.POLLHUP)
    pollc = 2
    events = poll.poll()
    while pollc > 0 and len(events) > 0:
        for rfd, event in events:
            if event & select.POLLIN:
                if rfd == child.stdout.fileno():
                    line = child.stdout.readline()
                    if len(line) > 0:
                        print('{0}'.format(COLORS['BOLD']))
                        logger.log(logging.INFO, line[:-1])
                        print('{0}'.format(COLORS['ENDC']))
                if rfd == child.stderr.fileno():
                    line = child.stderr.readline()
                    if len(line) > 0:
                        print('{0}'.format(COLORS['FAIL']))
                        logger.log(logging.ERROR, line[:-1])
                        print('{0}'.format(COLORS['ENDC']))
            if event & select.POLLHUP:
                poll.unregister(rfd)
                pollc -= 1
            if pollc > 0:
                events = poll.poll()
    ret = child.wait()
    if ret != 0:
        raise Exception(command)
    return ret

def system_output(command):
    print('{0}'.format(COLORS['BOLD']))
    ret = sp.check_output([command], shell=True).rstrip()
    print('{0}'.format(COLORS['ENDC']))

    return ret

def main():
    logger.debug("Starting Installation")
    system("clear")
    print """{0}
                        _      _____ _        _ _
         /\            | |    / ____| |      (_) |
        /  \   _ __ ___| |__ | (___ | |_ _ __ _| | _____
       / /\ \ | '__/ __| '_ \ \___ \| __| '__| | |/ / _ \\
      / ____ \| | | (__| | | |____) | |_| |  | |   <  __/
     /_/    \_\_|  \___|_| |_|_____/ \__|_|  |_|_|\_\___|
    {1}
    Choose an option from below.

    1) Start the ArchStrike Installer (will install ArchStrike on your hard drive)

    99) Exit{2}
    """.format(COLORS['OKBLUE'], COLORS['OKGREEN'], COLORS['ENDC'])

    choice = raw_input("{0}> Enter the number of your choice: {1}".format(COLORS['OKBLUE'],COLORS['ENDC']))
    if choice == "1":
        start()
    elif choice == "99":
        print_info("Alright, see you later!")
        sys.exit()
    else:
        print_error("Not sure what you're talking about.")
        main()

def menu():
    if os.geteuid() != 0:
        exit("Run as root/sudo please.\nExiting now")

    print """
    Welcome. I am now going to list you all the steps, and you can choose whichever you wish to continue from.

    1) Checking UEFI Mode

    2) Setting your keymap

    3) Preparing hard drive to install ArchStrike

    4) Partitioning drive (careful here)

    5) Formatting partitions

    6) Mounting partitions

    7) Installing the base system

    8) Generating fstab

    9) Locale and timezone

    10) Generating initramfs image

    11) Installing GRUB Bootloader

    12) Setting Hostname

    13) Setting up internet utilities

    14) Choosing root password

    15) Installing ArchStrike repositories

    16) Add a New User

    17) Setting up video & window manager

    99) Exit

    NOTE: If you want to do anything partitioning related, it's suggested you start over from Step 3
    """
    step = raw_input("> Enter the number of the step you wish to skip to: ")
    if step == "1":
        check_uefi()
    elif step == "2":
        set_keymap()
    elif step == "3":
        identify_devices()
    elif step == "4":
        partition_devices(drive, partition_table)
    elif step == "5":
        format_partitions()
    elif step == "6":
        mount_partitions(partitions)
    elif step == "7":
        install_base()
    elif step == "8":
        genfstab()
    elif step == "9":
        locale_and_time()
    elif step == "10":
        gen_initramfs()
    elif step == "11":
        setup_bootloader()
    elif step == "12":
        set_hostname()
    elif step == "13":
        setup_internet()
    elif step == "14":
        set_root_pass()
    elif step == "15":
        install_archstrike()
    elif step == "16":
        add_user()
    elif step == "17":
        set_video_utils()
    elif step == "99":
        main()
    else:
        print "Not sure what you're talking about."
        main()

def start():
    logger.debug("Performing Checks")
    system("clear")
    print_info("Performing some checks before we continue..")
    time.sleep(3)
    if internet_on() == False:
        print_error("Looks like you're not connected to the internet. Exiting.")
        sys.exit()
        print "Checks done. The installation process will now begin."
    if os.geteuid() != 0:
        print_error("Run as root/sudo please.\nExiting now")
        sys.exit()
    ## update system clock
    system("timedatectl set-ntp true")
    check_uefi()

## internet check function
def internet_on():
    logger.debug("Checking Internet connection")
    try:
        response=urllib2.urlopen('https://google.com',timeout=5)
        logger.info("Connection Successful")
        return True
    except urllib2.URLError as err:
        logger.error("Internet Connection Failed")
    return False

## uefi check function
def check_uefi():
    global uefi

    logger.debug("Check UEFI")
    system("clear")

    try:
        os.listdir('/sys/firmware/efi/efivars')
        uefi = True
    except OSError:
        # Dir doesnt exist
        print_title("Your computer doesnt seem to be running a UEFI board. Continuing..")
        uefi = False
        set_keymap()

## keymap check function
def set_keymap():
    logger.debug("Set Keymap")
    system("clear")
    print_title("Step 1) Keymap Setup")
    time.sleep(3)
    print_info("Setting your keyboard layout now, default is US.")
    if query_yes_no("> Would you like to change the keyboard layout?", 'no'):
        system("ls /usr/share/kbd/keymaps/**/*.map.gz")
        layout = raw_input("> Enter your keyboard layout: ")
        system("loadkeys {0}".format(layout))
        weirdfont = raw_input("> Try typing in here to test. If some characters are coming up different, delete it all and type 'Y': ")
        if weirdfont in yes:
            system("setfont lat9w-16")
            print_info("Should be fixed now.")
            partition_menu()
        else:
            ## next step
            partition_menu()
    else:
        print_info("Going to the next step.")
        partition_menu()

def partition_menu():
    global part_type
    logger.debug("Partition Menu")

    while True:
        system("clear")
        print_title("Step 2) Partition Menu")
        print_info("""
        Select Your Partition Method

        1) Auto Partition Drive

        2) Auto Partition Encrypted LVM

        3) Manual Partition

        """)
        part = raw_input("{0}> Choice: {1}".format(COLORS['OKBLUE'],COLORS['ENDC']))
        try:
            if int(part) in range(1,4):
                part_type = int(part)
                break
        except:
            print_error("Invalid Option")
            time.sleep(1)

    identify_devices()

## function to identify devices for partitioning
def identify_devices():
    global drive
    global drive_size

    logger.debug("Identify Devices")
    system("clear")
    print_title("Step 3) HDD Preparation")
    system("swapoff -a")
    time.sleep(3)
    print_info("Current Devices")
    system(''' lsblk -p | grep "disk" | awk '{print $1" "$4}' ''')
    available_drives = system_output(''' lsblk -p | grep "disk" | awk '{print $1}' ''').split('\n')
    drive = raw_input("{0}> Please choose the drive you would like to install ArchStrike on (default: /dev/sda ): {1}".format(COLORS['OKBLUE'],COLORS['ENDC'])) or '/dev/sda'
    if drive not in available_drives:
        print "That drive does not exist"
        time.sleep(1)
        identify_devices()
    if not query_yes_no("{0}Are you sure want to use {1}? Choosing the wrong drive may have very bad consequences!".format(COLORS['WARNING'],drive), 'yes'):
        identify_devices()
    drive_size = system_output("lsblk -p | grep -w %s | awk '{print $4}' | grep -o '[0-9]*' | awk 'NR==1'" % (drive))

    if part_type == 3:
        manual_partition()
    else:
        partition_devices()

def partition_devices():
    global fs
    types = {
        1: 'ext4',
        2: 'ext3',
        3: 'ext2',
        4: 'btrfs',
        5: 'jfs',
        6: 'reiserfs'
    }
    logger.debug("Partition Devices")
    system("clear")
    print_title("Step 4) Selecting the Filesystem Type")
    time.sleep(3)
    print_info("""
    Select your filesystem type:

    1) ext4

    2) ext3

    3) ext2

    4) btrfs

    5) jfs

    6) reiserfs
    """)
    try:
        fsc = raw_input("{0}> Choice (Default is ext4): {1}".format(COLORS['OKBLUE'],COLORS['ENDC'])).strip() or 1
        if int(fsc) not in range(1,7):
            raise Exception("Invalid Option")
        fs = types[int(fsc)]
    except:
        print_error("Invalid Option")
        partition_devices()
    setup_swap()

def setup_swap():
    global swap_space
    if query_yes_no("> Step 5) Would you like to create a new swap space?", 'yes'):
        swap_space = raw_input("{0}> Enter your swap space size (default is 512M ): {1}".format(COLORS['OKBLUE'],COLORS['ENDC'])).rstrip() or '512M'
        size = swap_space[:-1]
        if swap_space[-1] == "M":
            if int(size) >= (int(drive_size)*1024 - 4096):
                print_error("Your swap space is too large")
                setup_swap()
        elif swap_space[-1] == "G":
            if int(size) >= (int(drive_size) - 4):
                print_error("Your swap space is too large")
                setup_swap()
        else:
            print_error("Swap space must be in M or G")
            setup_swap()
    else:
        swap_space = 'None'
    partitioner()

def partitioner():
    global gpt

    logger.debug("Partitioner")
    system("clear")
    gpt = False
    if not uefi:
        if query_yes_no("> Step 6) Would you like to use GUID Partition Table?", 'no'):
            gpt = True
    system("clear")
    print_info("""
    Device: %s
    Filesystem: %s
    Swap: %s
    """ % (drive, fs, swap_space))
    if query_yes_no("> Are you sure your partitions are set up correctly?", 'yes'):
        check_lvm()
    else:
        identify_devices()

def manual_partition():
    global partition_table

    system('clear')
    print_title("Step 4) Manual Partititon (careful in this step)")
    time.sleep(3)
    print_info("I'm now going to print the current partition scheme of your drive %s" % drive)
    print_info("But first let's confirm everything.")
    confirm_drive = raw_input("{0}> Please confirm the drive by typing {1}: {2}".format(COLORS['OKBLUE'],drive, COLORS['ENDC']))
    if confirm_drive != drive:
        print_error("That doesn't look right. Let's try identifying those again.")
        identify_devices()
    system("lsblk {0}".format(drive))
    partition_table = system_output("fdisk -l {0} | grep Disklabel | cut -d ' ' -f 3".format(drive))
    if partition_table == 'gpt':
        print_info("""
     For the GPT partition table, the suggested partition scheme looks like this:
     mountpoint        partition        partition type            boot flag        suggested size
     _________________________________________________________________________________________
     /boot              /dev/sdx1        EFI System Partition      Yes               260-512 MiB

     [SWAP]             /dev/sdx2        Linux swap                No                More than 512 MiB

     /                  /dev/sdx3        Linux (ext4)              No                Remainder of the device

    WARNING: If dual-booting with an existing installation of Windows on a UEFI/GPT system,
    avoid reformatting the UEFI partition, as this includes the Windows .efi file required to boot it.
        """)
    elif partition_table == 'dos':
        print_info("""
    For the MBR partition table, the suggested partition scheme looks like this:
    mountpoint        partition        partition type            boot flag        suggested size
    _________________________________________________________________________________________
    [SWAP]            /dev/sdx1        Linux swap                No                More than 512 MiB
    /                 /dev/sdx2        Linux (ext4)              Yes               Remainder of the device
    """)
    if query_yes_no("> I've read this and wish to continue to the partitioner.", 'yes'):
        sp.call("clear", shell=True)
        sp.call('cfdisk {0}'.format(drive), shell=True)
        sp.call("clear", shell=True)
        sp.call('lsblk {0}'.format(drive), shell=True)
        if query_yes_no("> Are you sure your partitions are set up correctly?", 'yes'):
            format_partitions()
        else:
            manual_partition()
    else:
        identify_devices()

def format_partitions():
    logger.debug("Format Partitions")
    system("clear")
    print_title("Step 5) Formatting partitions")
    time.sleep(3)
    print_info("Current partition scheme of {0}".format(drive))
    system("lsblk %s" % drive)
    partitions = raw_input("{0}> Enter all the partitions you created by seperating them with a comma (e.g. /dev/sda1,/dev/sda2): {1}".format(COLORS['OKBLUE'],COLORS['ENDC'])).split(',')
    print_info("You sure these are the partitions?\n{0}".format('\n'.join(partitions)))
    if query_yes_no("> ", 'yes'):
        print "Alright, starting to format."
        for i in partitions:
            print_warning("Partition {0} will be formatted now".format(i))
            partition_type = raw_input("{0}> Enter the partition type (linux, uefi, swap): {1}".format(COLORS['OKBLUE'],COLORS['ENDC'])).lower()
            if partition_type == 'linux':
                system("mkfs.ext4 {0}".format(i))
            elif partition_type == 'uefi':
                system("mkfs.fat -F32 {0}".format(i))
            elif partition_type == 'swap':
                system("mkswap {0}".format(i))
                system("swapon {0}".format(i))
            else:
                print_error("Not sure what you're talking about.")
                format_partitions()
        mount_partitions(partitions)
    else:
        format_partitions()

def mount_partitions(partitions):
    logger.debug("Mount Partitions")
    system("clear")
    print_title("Step 6) Mounting the partitions")
    time.sleep(3)
    ## get individual partition fs types so we can mount / in /mnt
    print_info('\n'.join(partitions))
    root = raw_input("{0}Which one is your / mounted partition? (e.g. /dev/sda1): {1}".format(COLORS['OKBLUE'],COLORS['ENDC']))
    if root in partitions:
        print_info("Mounting {0} on /mnt".format(root))
        system("mount {0} /mnt".format(root))
    else:
        mount_partitions(partitions)
    if partition_table == 'gpt':
        boot = raw_input("{0}Which one is your /boot mounted partition? (e.g. /dev/sda2): {1}".format(COLORS['OKBLUE'],COLORS['ENDC']))
        if boot in partitions:
            print_info("Mounting %s on /mnt/boot" % boot)
            system("mkdir -p /mnt/boot")
            system("mount {0} /mnt/boot".format(boot))
        else:
            mount_partitions(partitions)
    else:
        system("mkdir -p /mnt/boot")

    install_base()

def check_lvm():

    pvscan = system_output('pvscan')
    vgscan = system_output('vgscan')
    lvscan = system_output('lvscan')

    if lvscan:
        print_warning("WARNING: This will remove all LVM Partitions")
        if not query_yes_no("> Would you like to continue?: ", None):
            partition_menu()

        for entry in lvscan.rstrip().split('\n'):
            lvm_dir = entry.split("'")[1]
            system("echo -e 'y'|lvm lvremove {0}".format(lvm_dir))

    if part_type == 1:
        system("clear")
        if query_yes_no("{0}Automatic partitioning wipes your drive clean before proceeding. Are you sure you want to continue?".format(COLORS['WARNING']), 'no'):
            auto_partition()
        else:
            partition_menu()
    elif part_type == 2:
        system("clear")
        if query_yes_no("{0}Automatic partitioning wipes your drive clean before proceeding. Are you sure you want to continue?".format(COLORS['WARNING']), 'no'):
            auto_encrypt()
        else:
            partition_menu()

def auto_partition():
    global ROOT
    global BOOT
    global SWAP

    logger.debug("Format Partitions")
    system("clear")
    print_title("Step 6) Formatting Drive...")
    system("sgdisk --zap-all {0}".format(drive))
    if gpt:
        if uefi:
            if swap_space != 'None':
                system('echo -e "n\n\n\n512M\nef00\nn\n3\n\n+{0}\n8200\nn\n\n\n\n\nw\ny" | gdisk {1}'.format(swap_space, drive))
                SWAP = system_output("lsblk | grep %s | awk '{ if (NR==4) print substr ($1,3) }'" % (drive[-3:]))
                system("wipefs -afq /dev/{0}".format(SWAP))
                system("mkswap /dev/{0}".format(SWAP))
                system("swapon /dev/{0}".format(SWAP))
            else:
                system('echo -e "n\n\n\n512M\nef00\nn\n\n\n\n\nw\ny" | gdisk {0}'.format(drive))
            BOOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]))
            ROOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==3) print substr ($1,3) }' ''' % (drive[-3:]))
        else:
            if swap_space != 'None':
                system('echo -e "o\ny\nn\n1\n\n+100M\n\nn\n2\n\n+1M\nEF02\nn\n4\n\n+{0}\n8200\nn\n3\n\n\n\nw\ny" | gdisk {1}'.format(swap_space, drive))
                SWAP = system_output("lsblk | grep %s |  awk '{ if (NR==5) print substr ($1,3) }'" % (drive[-3:]), shell=True).rstrip()
                system("wipefs -afq /dev/{0}".format(SWAP))
                system("mkswap /dev/{0}".format(SWAP))
                system("swapon /dev/{0}".format(SWAP))
            else:
                system('echo -e "o\ny\nn\n1\n\n+100M\n\nn\n2\n\n+1M\nEF02\nn\n3\n\n\n\nw\ny" | gdisk {0}'.format(drive))
            BOOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]))
            ROOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==4) print substr ($1,3) }' ''' % (drive[-3:]))
    else:
        if swap_space != 'None':
            system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n3\n\n+{0}\nt\n\n82\nn\np\n2\n\n\nw" | fdisk {1}'.format(swap_space, drive))
            SWAP = system_output("lsblk | grep %s |  awk '{ if (NR==4) print substr ($1,3) }'" % (drive[-3:]))
            system("wipefs -afq /dev/{0}".format(SWAP))
            system("mkswap /dev/{0}".format(SWAP))
            system("swapon /dev/{0}".format(SWAP))
        else:
            system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n2\n\n\nw" | fdisk {0}'.format(drive))
        BOOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]))
        ROOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==3) print substr ($1,3) }' ''' % (drive[-3:]))
    # Create Boot Partition
    system("wipefs -afq /dev/{0}".format(BOOT))
    if uefi:
        system("mkfs.vfat -F32 /dev/{0}".format(BOOT))
    else:
        system("mkfs.ext4 /dev/{0}".format(BOOT))

    # Create Root Partition
    system("wipefs -afq /dev/{0}".format(ROOT))
    if fs == 'jfs' or fs == 'reiserfs':
        system('echo -e "y" | mkfs.{0} /dev/{1}'.format(fs, ROOT))
    else:
        system('mkfs.{0} /dev/{1}'.format(fs, ROOT))

    system("mount /dev/{0} /mnt".format(ROOT))
    system("mkdir -p /mnt/boot")
    system("mount /dev/{0} /mnt/boot".format(BOOT))

    install_base()

def auto_encrypt():
    global ROOT
    global BOOT
    global SWAP

    print_warning("WARNING! This will encrypt {0}".format(drive))
    if not query_yes_no("> Continue?", 'no'):
        partition_menu()
    pass_set = False
    while not pass_set:
        passwd = getpass("> Please enter a new password for {0}: ".format(drive))
        passwd_chk = getpass("> New {0} password again: ".format(drive))
        if passwd == passwd_chk:
            pass_set = True
        else:
            print "Password do not Match."
    del passwd_chk
    if gpt:
        if uefi:
            system('echo -e "n\n\n\n512M\nef00\nn\n\n\n\n\nw\ny" | gdisk {0}'.format(drive))
            BOOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]))
            ROOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==3) print substr ($1,3) }' ''' % (drive[-3:]))
        else:
            system('echo -e "o\ny\nn\n1\n\n+100M\n\nn\n2\n\n+1M\nEF02\nn\n3\n\n\n\nw\ny" | gdisk {0}'.format(drive))
            BOOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==4) print substr ($1,3) }' ''' % (drive[-3:]))
            ROOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]))
    else:
        system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n2\n\n\nw" | fdisk {0}'.format(drive))
        BOOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]))
        ROOT = system_output(''' lsblk | grep %s |  awk '{ if (NR==3) print substr ($1,3) }' ''' % (drive[-3:]))

    system("wipefs -afq /dev/{0}".format(ROOT))
    system("wipefs -afq /dev/{0}".format(BOOT))

    system("lvm pvcreate /dev/{0}".format(ROOT))
    system("lvm vgcreate lvm /dev/{0}".format(ROOT))

    if swap_space != 'None':
        system("lvm lvcreate -L {0} -n swap lvm ".format(swap_space))

    system("lvm lvcreate -L 500M -n tmp lvm")
    system("lvm lvcreate -l 100%FREE -n lvroot lvm")

    system("printf {0} | cryptsetup luksFormat -c aes-xts-plain64 -s 512 /dev/lvm/lvroot -".format(passwd))
    system("printf {0} | cryptsetup open --type luks /dev/lvm/lvroot root -".format(passwd))
    del passwd
    system("wipefs -afq /dev/mapper/root")
    if fs == 'jfs' or fs == 'reiserfs':
        system('echo -e "y" | mkfs.{0} /dev/mapper/root'.format(fs))
    else:
        system('mkfs.{0} /dev/mapper/root'.format(fs))

    if uefi:
        system("mkfs.vfat -F32 /dev/".format(BOOT))
    else:
        system("wipefs -afq /dev/{0}".format(BOOT))
        system("mkfs.ext4 /dev/{0}".format(BOOT))

    system("mount /dev/mapper/root /mnt")
    system("mkdir -p /mnt/boot")
    system("mount /dev/{0} /mnt/boot".format(BOOT))

    install_base()

def install_base():
    logger.debug("Install Base")
    base = 1
    while True:
        system("clear")
        print_title("Step 7) Install System Base")
        print_info("""
        Select Your Base

        1) Arch-Linux-Base

        2) Arch-Linux-Base-Devel

        3) Arch-Linux-GrSec

        4) Arch-Linux-LTS-Base

        5) Arch-Linux-LTS-Base-Devel
        """)
        choice = raw_input("{0}> Choice (Default is Arch-Linux-Base): {1}".format(COLORS['OKBLUE'],COLORS['ENDC'])) or 1
        try:
            if int(choice) in range(1,6):
                base = int(choice)
                break
        except:
            print_error("Invalid Option")
            time.sleep(1)

    if base == 1:
        base_install = "sudo"
    elif base == 2:
        base_install = "base-devel"
    elif base == 3:
        base_install = "linux-grsec linux-grsec-headers sudo"
    elif base == 4:
        base_install = "linux-lts linux-lts-headers sudo"
    elif base == 5:
        base_install = "base-devel linux-lts linux-lts-headers sudo"

    if uefi:
        base_install += " efibootmgr"

    system("pacstrap /mnt base {0}".format(base_install))

    genfstab()

def genfstab():
    logger.debug("Genfstab")
    system("clear")
    print_title("Step 8) Generating fstab...")
    time.sleep(3)
    system("genfstab -U /mnt >> /mnt/etc/fstab")
    if query_yes_no("> Would you like to edit the generated fstab?", 'no'):
        system("nano /mnt/etc/fstab")
    locale_and_time()

def locale_and_time():
    logger.debug("Locale and Time")
    system("clear")
    print_title("Step 9) Generating locale and setting timezone")
    print_info("Now you'll see an output of the locale list.")
    print_info("""
    1) United States

    2) Australia

    3) Canada

    4) Spanish

    5) French

    6) German

    7) Great Britain

    8) Mexico

    9) Portugal

    10) Romanian

    11) Russian

    12) Swedish

    99) More

    Default is United States.

    """)
    choice = raw_input("{0}> Enter the number for your locale or leave empty for default: {1}".format(COLORS['OKBLUE'],COLORS['ENDC'])) or '1'
    localesdict = {'1': 'en_US.UTF-8', '2': 'en_AU.UTF-8', '3': 'en_CA.UTF-8', '4': 'es_ES.UTF-8', '5': 'fr_FR.UTF-8', '6': 'de_DE.UTF-8', '7': 'en_GB.UTF-8', '8': 'en_MX.UTF-8', '9': 'pt_PT.UTF-8', '10': 'ro_RO.UTF-8', '11': 'ru_RU.UTF-8', '12': 'sv_SE.UTF-8'}
    if choice in map(str, range(1,13)):
        locale = localesdict[str(choice)]
    elif choice == '99':
        print_info("A full list will be listed now.")
        print_info("Press 'q' to quit and 'Enter'/'Return' to scroll. Afterwards type in the locale you want to use.")
        time.sleep(3)
        system("cat /mnt/etc/locale.gen | more")
        locale = raw_input("{0}> Please type in the locale you want to use: {1}".format(COLORS['OKBLUE'],COLORS['ENDC']))
    else:
        locale_and_time()
    system("sed -i '/{0}/s/^#//g' /mnt/etc/locale.gen".format(locale))
    system("locale-gen", True)
    print_info("Setting up keyboard layout, will take the current one.")
    layout = system("localectl | grep Locale | cut -d ':' -f 2")
    system("echo {0} >> /mnt/etc/vconsole.conf".format(layout))
    print_info("Setting up timezone.")
    system("tzselect > /tmp/archstrike-timezone", True)
    system("ln -s /usr/share/zoneinfo/$(cat /tmp/archstrike-timezone) /etc/localtime", True)
    system("hwclock --systohc --utc")
    gen_initramfs()

def gen_initramfs():
    if part_type !=2 and not uefi:
        logger.debug("Gen Initramfs")
        system("clear")
        print_title("Step 10) Generate initramfs image...")
        time.sleep(3)
        system("mkinitcpio -p linux", True)

    setup_bootloader()

# TODO: systemd-bootloader and syslinux
def setup_bootloader():
    logger.debug("Setup Bootloader")
    system("clear")
    print_title("Setting up GRUB bootloader")
    time.sleep(3)

    system("pacman -S grub --noconfirm", True)
    intelornot = system_output("cat /proc/cpuinfo | grep -m1 vendor_id |awk '{print $NF}'")
    if intelornot == 'GenuineIntel':
        if query_yes_no('We have detected you have an Intel CPU. Is that correct?', 'yes'):
            system("pacman -S intel-ucode --noconfirm", True)

    #Encrypted
    if part_type == 2:
        system("sed -i 's!quiet!cryptdevice=/dev/lvm/lvroot:root root=/dev/mapper/root!' /mnt/etc/default/grub")
    else:
        system("sed -i 's/quiet//' /mnt/etc/default/grub")

    if uefi:
        system("grub-install --efi-directory=/boot --target=x86_64-efi --bootloader-id=boot", True)
        system("mv /mnt/boot/EFI/boot/grubx64.efi /mnt/boot/EFI/boot/bootx64.efi") #Check this

        if part_type != 2:
            system("mkinitcpio -p linux", True)
    else:
        system("grub-install {0}".format(drive), True)

    system("grub-mkconfig -o /boot/grub/grub.cfg ", True)

    configure_system()

def configure_system():
    print_title("Configuring System")
    time.sleep(1)

    if part_type == 2 and uefi:
        system('echo "/dev/{0}              /boot           vfat         rw,relatime,fmask=0022,dmask=0022,codepage=437,iocharset=iso8859-1,shortname=mixed,errors=remount-ro        0       2" > /mnt/etc/fstab'.format(BOOT))
    elif part_type == 2:
        system('echo "/dev/{0}              /boot           {1}         defaults        0       2" > /mnt/etc/fstab'.format(BOOT, fs))

    if part_type == 2:
        system('echo "/dev/mapper/root        /               {0}         defaults        0       1" >> /mnt/etc/fstab'.format(fs))
        system('echo "/dev/mapper/tmp         /tmp            tmpfs        defaults        0       0" >> /mnt/etc/fstab')
        system('echo "tmp	       /dev/lvm/tmp	       /dev/urandom	tmp,cipher=aes-xts-plain64,size=256" >> /mnt/etc/crypttab')
        if swap_space != 'None':
            system('echo "/dev/mapper/swap     none            swap          sw                    0       0" >> /mnt/etc/fstab')
            system('echo "swap	/dev/lvm/swap	/dev/urandom	swap,cipher=aes-xts-plain64,size=256" >> /mnt/etc/crypttab')
        system("sed -i 's/k filesystems k/k lvm2 encrypt filesystems k/' /mnt/etc/mkinitcpio.conf")
        system("mkinitcpio -p linux", True)

    set_hostname()

def set_hostname():
    logger.debug("Set Hostname")
    system("clear")
    print_title("Step 11) Setting Hostname")
    print_info("Your hostname will be 'archstrike'. You can change it later if you wish.")
    time.sleep(3)
    system("echo 'archstrike' > /mnt/etc/hostname")
    setup_internet()

def setup_internet():
    logger.debug("Setup Internet")
    system("clear")
    print_title("Step 12) Setup Internet")
    if query_yes_no("> Do you want wireless utilities on your new install?", 'yes'):
        print_info("Installing Wireless utilities")
        system("pacman -S iw wpa_supplicant dialog --noconfirm", True)
    if query_yes_no("> Would you like to enable DHCP?", 'yes'):
        print_info("Enabling DHCP")
        system("systemctl enable dhcpcd", True)
    set_root_pass()

def set_root_pass():
    logger.debug("Set root Pass")
    system("clear")
    print_title("Step 13) Setting root password")
    ret = -1
    while ret != 0:
        ret = system("passwd", True)
    install_archstrike()

def install_archstrike():
    logger.debug("Install ArchStrike")
    system("clear")
    print_title("Step 14) Installing the ArchStrike repositories...")
    time.sleep(3)
    system("echo '[archstrike]' >> /mnt{0}".format(pacmanconf))
    system("echo 'Server = https://mirror.archstrike.org/$arch/$repo' >> /mnt{0}".format(pacmanconf))
    cpubits = system_output('getconf LONG_BIT')
    if cpubits == '64':
        print_info("We have detected you are running x86_64. It is advised to enable multilib with the ArchStrike repo. Do you want to enable multilib? (say no if it's already enabled)")
        if query_yes_no(">", 'yes'):
            system("""sed -i '/\[multilib]$/ {
			    N
			    /Include/s/#//g}' /mnt/%s
            """ % (pacmanconf))
            system('''/bin/bash -c " echo -e 'y\ny\n' |pacman -S gcc-multilib"''', True)
            print_info("Multilib has been enabled.")
    else:
        print_info("Alright, looks like no. Continuing.")
    print_info("I will now perform database updates, hang tight.")
    system("pacman -Syy", True)
    print_info("Installing ArchStrike keyring and mirrorlist..")
    system("pacman-key --init", True)
    system("dirmngr < /dev/null", True)
    system("pacman-key -r 7CBC0D51", True)
    system("pacman-key --lsign-key 7CBC0D51", True)
    system("pacman -S archstrike-keyring --noconfirm", True)
    system("pacman -S archstrike-mirrorlist --noconfirm", True)
    print_info("Done. Editing your pacman config to use the new mirrorlist.")
    system("sed -i 's|Server = https://mirror.archstrike.org/$arch/$repo|Include = /etc/pacman.d/archstrike-mirrorlist|' /mnt{0}".format(pacmanconf))
    if query_yes_no("> Do you want to add archstrike-testing as well?", 'yes'):
        system("echo '[archstrike-testing]' >> /mnt{0}".format(pacmanconf))
        system("echo 'Include = /etc/pacman.d/archstrike-mirrorlist' >> /mnt{0}".format(pacmanconf))
    else:
          print_info("Alright going forward.")
    print "Performing database update once more to test mirrorlist"
    system("pacman -Syy", True)
    if query_yes_no("> Do you want to go ahead and install all ArchStrike packages now?", 'no'):
        system('''/bin/bash -c " echo -e 'y\n'| pacman -S cryptsetup-nuke-keys"''', True)
        system("pacman -S archstrike linux-headers --noconfirm", True)
    add_user()

def add_user():
    global username
    username = ''

    logger.debug("Add User")
    system("clear")
    print_title("Step 15) Add new User")
    if query_yes_no("> Would you like to add a new user?", 'yes'):
        while not username:
            username = raw_input("{0}> Please enter a username: {1}".format(COLORS['OKBLUE'],COLORS['ENDC']))
        system("useradd -m -g users -G audio,network,power,storage,optical {0}".format(username), True)
        print_command("> Please enter the password for {0}: ".format(username))
        ret = -1
        while ret != 0:
            ret = system("passwd {0}".format(username), True)
        if query_yes_no("> Would you like to give {0} admin privileges?".format(username), 'yes'):
            system("sed -i '/%wheel ALL=(ALL) ALL/s/^#//' /mnt/etc/sudoers")
            system("usermod -a -G wheel {0}".format(username), True)
    set_video_utils(username)

def set_video_utils(user):
    gpus = {
        '1':'mesa-libgl',
        '2':'nvidia',
        '3':'xf86-video-ati',
        '4':'xf86-video-intel',
        '5':'xf86-video-vesa'
    }
    logger.debug("Set Video Utils")
    system("clear")
    print_title("Step 16) Setting up video and desktop environment")
    if query_yes_no("> Would you like to set up video utilities?", 'yes'):
        print_info("To setup video utilities select your GPU. (Leave empty if unsure)")
        print_info("""

        1) mesa-libgl

        2) nvidia

        3) xf86-video-ati

        4) xf86-video-intel
        """)
        gpu = raw_input("{0}> Choose an option or leave empty for default: {1}".format(COLORS['OKBLUE'],COLORS['ENDC'])) or '5'
        try:
            sel = gpus[gpu]
            system("pacman -S xorg-server xorg-server-utils xorg-xinit xterm {0} --noconfirm".format(sel), True)
        except KeyError:
            print_error("Not a valid option")
            set_video_utils(username)

    if query_yes_no("> Would you like to install a Desktop Environment or Window Manager?", 'yes'):
        opt = ''
        while not opt:
            print_info("""
            Available Options:

            1) OpenBox

            2) Xfce

            3) i3wm

            4) All
            """)
            opt = raw_input("{0}> Choice: {1}".format(COLORS['OKBLUE'],COLORS['ENDC']))
            if opt == '4':
                opt = '123'
            elif opt not in '1234':
                opt = ''

        if '1' in opt:
            system("pacman -S archstrike-openbox-config --noconfirm", True)
            if username:
                system("mkdir -p /mnt/home/{0}/.config".format(username))
                system("echo 'exec openbox-session' > /mnt/home/{0}/.xinitrc".format(username))
                system("cp -a /mnt/usr/share/archstrike-openbox-config/etc/* /mnt/home/{0}/.config/".format(username))
                system("chown {0}:users -R /home/{0}/.config /home/{0}/.xinitrc".format(username), True)
            system("echo 'exec openbox-session' > /mnt/root/.xinitrc")
            system("mkdir -p /mnt/root/.config")
            system("cp -a /mnt/usr/share/archstrike-openbox-config/etc/* /mnt/root/.config/")

        if '2' in opt:
            system("pacman -S xfce4 xfce4-goodies --noconfirm", True)
            system("pacman -S archstrike-xfce-config --noconfirm", True)
            if username:
                system("mkdir -p /mnt/home/{0}/.config".format(username))
                system("echo 'exec startxfce4' > /mnt/home/{0}/.xinitrc".format(username))
                system("cp -a /mnt/usr/share/archstrike-xfce-config/config/* /mnt/home/{0}/.config/".format(username))
                system("chown {0}:users -R /home/{0}/.config /home/{0}/.xinitrc".format(username), True)
            system("echo 'exec startxfce4' > /mnt/root/.xinitrc")
            system("mkdir -p /mnt/root/.config")
            system("cp -a /mnt/usr/share/archstrike-xfce-config/config/* /mnt/root/.config/")
            system("cp -a /mnt/usr/share/archstrike-xfce-config/icons/* /mnt/usr/share/pixmaps/")
            system("cp -a /mnt/usr/share/archstrike-xfce-config/wallpapers/* /mnt/usr/share/backgrounds/xfce/")

        if '3' in opt:
            system("pacman -S archstrike-i3-config --noconfirm", True)
            if username:
                system("mkdir -p /mnt/home/{0}/.config".format(username))
                system("echo 'exec i3' > /mnt/home/{0}/.xinitrc".format(username))
                system("cp -a /mnt/usr/share/archstrike-i3-config/config/* /mnt/home/{0}/.config/".format(username))
                system("cat /mnt/usr/share/archstrike-i3-config/Xresources >> /mnt/home/{0}/.Xresources".format(username))
                system("cp -a /mnt/usr/share/archstrike-i3-config/gtkrc-2.0 /mnt/home/{0}/.gtkrc-2.0".format(username))
                system("chown {0}:users -R /home/{0}/.config /home/{0}/.xinitrc /home/{0}/.Xresources /home/{0}/.gtkrc-2.0".format(username), True)
            system("echo 'exec i3' > /mnt/root/.xinitrc")
            system("mkdir -p /mnt/root/.config")
            system("cp -a /mnt/usr/share/archstrike-i3-config/config/* /mnt/root/.config/")
            system("cat /mnt/usr/share/archstrike-i3-config/Xresources >> /mnt/root/.Xresources")
            system("cp -a /mnt/usr/share/archstrike-i3-config/gtkrc-2.0 /mnt/root/.gtkrc-2.0")

        system("cp -a /home/archstrike/.config/terminator /mnt/home/{0}/.config".format(username))
        system("cp -a /home/archstrike/.config/terminator /mnt/root/.config/")

    if query_yes_no("> Would you like to install a login manager?", 'yes'):
        system("pacman -S lightdm lightdm-gtk-greeter --noconfirm", True)
        system("systemctl enable lightdm.service", True)

    if query_yes_no("> Would you like to install virtualbox utils?", 'yes'):
        system("pacman -S virtualbox-guest-utils linux-headers mesa-libgl --noconfirm", True)

    if query_yes_no("> Would you like to add touchpad support?", 'no'):
        system("pacman -S xf86-input-synaptics --noconfirm", True)

    if query_yes_no("> Would you like to add bluetooth support?", 'no'):
        system("pacman -S blueman --noconfirm", True)

    finalize()

def finalize():
    logger.debug("Finalize")
    system("clear")
    print_info("FINAL: Your system is set up! Rebooting now..")
    print_info("Thanks for installing ArchStrike!")
    system("umount -R /mnt")
    if query_yes_no("> Would you like to reboot now?", None):
        system("reboot")


if __name__ == '__main__':
    try:
        FNULL = open(os.devnull, 'w')
        signal.signal(signal.SIGINT, signal_handler)
        logger.info(platform.uname())
        main()
    except Exception as e:
        logger.error('{0}{1}{2}'.format(COLORS['FAIL'], e, COLORS['ENDC']))
        sp.Popen("umount -R /mnt", stdout=FNULL, stderr=sp.STDOUT, shell=True)
        print_error("\n\nAn error has occured, see /tmp/archstrike-installer.log for details.")
        FNULL.close()
