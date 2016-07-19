#!/usr/bin/env python2
from getpass import getpass
import subprocess as sp
import logging
import signal
import urllib2
import time
import sys
import os

# Setup Logging
logging.basicConfig(filename='/tmp/archstrike-installer.log',
                    filemode='w',
                    level=logging.DEBUG,
                    format='%(levelname)s - %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger(__name__).addHandler(console)
logger = logging.getLogger(__name__)

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

## Set some variables for being lazy later on
yes = ['y', 'ye', 'yes', 'Y', 'YE', 'YES']
no = ['n', 'no', 'N', 'NO']
pacmanconf = "/etc/pacman.conf"
archstrike_mirrorlist = "/etc/pacman.d/archstrike-mirrorlist"

def signal_handler(signal, handler):
    sp.Popen("umount -R /mnt", stdout=FNULL, stderr=sp.STDOUT, shell=True)
    FNULL.close()
    print "\n\nGood Bye"
    sys.exit()

def system(command, chroot=False):
    # don't log clear or encryption passwd
    if command == 'clear' or command.find('printf') != -1:
        sp.call(command, shell=True)
        return

    if chroot:
        command = "arch-chroot /mnt {0}".format(command)

    logger.debug(command)

    try:
        return sp.call([command], shell=True)
    except:
        logger.error(stderr)


def main():
    logger.debug("Starting Installation")
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

    99) Exit
    """.format(COLORS['OKBLUE'], COLORS['ENDC'])
    time.sleep(3)

    choice = raw_input("> Enter the number of your choice: ")
    if choice == "1":
        start()
    elif choice == "99":
        print "Alright, see you later!"
        sys.exit()
    else:
        print "Not sure what you're talking about."
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
    print "Performing some checks before we continue.."
    time.sleep(3)
    if internet_on() == False:
        print "Looks like you're not connected to the internet. Exiting."
        sys.exit()
        print "Checks done. The installation process will now begin."
    if os.geteuid() != 0:
        exit("Run as root/sudo please.\nExiting now")
    ## update system clock
    system("timedatectl set-ntp true")
    check_uefi()

## internet check function
def internet_on():
    logger.debug("Checking Internet connection")
    try:
        response=urllib2.urlopen('http://google.com',timeout=1)
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
        print "Your computer doesnt seem to be running a UEFI board. Continuing.."
        uefi = False
        set_keymap()

## keymap check function
def set_keymap():
    logger.debug("Set Keymap")
    system("clear")
    print "Step 1) Keymap Setup"
    time.sleep(3)
    print "Setting your keyboard layout now, default is US."
    choice = raw_input("> Would you like to change the keyboard layout? [y/N]: ").lower() or 'no'
    if choice in yes:
        system("ls /usr/share/kbd/keymaps/**/*.map.gz")
        layout = raw_input("> Enter your keyboard layout: ")
        system("loadkeys {0}".format(layout))
        weirdfont = raw_input("> Try typing in here to test. If some characters are coming up different, delete it all and type 'Y': ")
        if weirdfont in yes:
            system("setfont lat9w-16")
            print "Should be fixed now."
            identify_devices()
        else:
            ## next step
            identify_devices()
    elif choice in no:
        print "Going to the next step."
        identify_devices()
    else:
        print "Not sure what you're talking about."
        set_keymap()

## function to identify devices for partitioning
def identify_devices():
    global drive
    global drive_size

    logger.debug("Identify Devices")
    system("clear")
    print "Step 2) HDD Preparation"
    system("swapoff -a")
    time.sleep(3)
    print "Current Devices"
    system(''' lsblk -p | grep "disk" | awk '{print $1" "$4}' ''')
    available_drives = sp.check_output(''' lsblk -p | grep "disk" | awk '{print $1}' ''', shell=True).split('\n')[:-1]
    drive = raw_input("> Please choose the drive you would like to install ArchStrike on (default: /dev/sda ): ") or '/dev/sda'
    if drive not in available_drives:
        print "That drive does not exist"
        time.sleep(1)
        identify_devices()
    sure = raw_input("Are you sure want to use {0}? Choosing the wrong drive may have very bad consequences!: ".format(drive))
    if sure in no:
        identify_devices()
    drive_size = sp.check_output("lsblk -p | grep -w %s | awk '{print $4}' | grep -o '[0-9]*' | awk 'NR==1'" % (drive), shell=True).rstrip()
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
    print "Step 3) Selecting the Filesystem Type"
    time.sleep(3)
    print """
    Select your filesystem type:

    1) ext4

    2) ext3

    3) ext2

    4) btrfs

    5) jfs

    6) reiserfs
    """
    try:
        fsc = raw_input("> Choice (Default is ext4): ").strip() or 1
        if int(fsc) not in range(1,7):
            raise Exception("Invalid Option")
        fs = types[int(fsc)]
    except:
        print "Invalid Option"
        partition_devices()
    setup_swap()

def setup_swap():
    global swap_space
    cswap = raw_input("> Step 4) Would you like to create a new swap space? [Y/n]: ").lower() or 'yes'
    if cswap in yes:
        swap_space = raw_input("> Enter your swap space size (default is 512M ): ".format(drive_size)).rstrip() or '512M'
        size = swap_space[:-1]
        if swap_space[-1] == "M":
            if int(size) >= (int(drive_size)*1024 - 4096):
                print "Your swap space is too large"
                setup_swap()
        elif swap_space[-1] == "G":
            if int(size) >= (int(drive_size) - 4):
                print "Your swap space is too large"
                setup_swap()
        else:
            print "Swap space must be in M or G"
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
        cgpt = raw_input("> Step 5) Would you like to use GUID Partition Table? [y/N]: ").lower() or 'no'
        if cgpt in yes:
            gpt = True
    system("clear")
    print """
    Device: %s
    Filesystem: %s
    Swap: %s
    """ % (drive, fs, swap_space)
    check_sure = raw_input("> Are you sure your partitions are set up correctly? [Y/n]: ").lower() or 'yes'
    if check_sure in yes:
        partition_menu()
    else:
        identify_devices()

def partition_menu():
    global part_type
    logger.debug("Partition Menu")

    while True:
        system("clear")
        print "Step 6) Partition Menu"
        print """
        Select Your Partition Method

        1) Auto Partition Drive

        2) Auto Partition Encrypted LVM

        3) Manual Partition

        """
        part = raw_input("> Choice: ")
        try:
            if int(part) in range(1,4):
                part_type = int(part)
                break
        except:
            print "Invalid Option"
            time.sleep(1)

    if part_type == 1:
        auto_partition()
    elif part_type == 2:
        auto_encrypt()
    elif part_type == 3:
        manual_partition()

def check_lvm():

    pvscan = sp.check_output('pvscan', shell=True)
    vgscan = sp.check_output('vgscan', shell=True)
    lvscan = sp.check_output('lvscan', shell=True)

    if lvscan:
        for entry in lvscan.rstrip().split('\n'):
            lvm_dir = entry.split("'")[1]
            system("lvm lvremove {0}".format(lvm_dir))

def manual_partition():
     system('clear')
     print "Step 4) Manual Partititon (careful in this step)"
     time.sleep(3)
     print "I'm now going to print the current partition scheme of your drive %s" % drive
     print "But first let's confirm everything."
     confirm_drive = raw_input("> Please confirm that {0} is the drive you chose: ".format(drive))
     if confirm_drive not in yes:
        print "That doesn't look right. Let's try identifying those again."
        identify_devices()
     confirm_table = raw_input("> Please confirm that {0} is the partition table of {1}: ".format(partition_table, drive))
     if confirm_table not in partition_table:
        print "That doesn't look right. Let's try identifying those again."
        identify_devices()
     print "Looks like both are confirmed."
     sp.call("lsblk {0}".format(drive), shell=True)
     if partition_table == 'gpt':
        print """
     For the GPT partition table, the suggested partition scheme looks like this:
     mountpoint        partition        partition type            boot flag        suggested size
     _________________________________________________________________________________________
     /boot              /dev/sdx1        EFI System Partition      Yes               260-512 MiB
                                                                                                                                             
     [SWAP]             /dev/sdx2        Linux swap                No                More than 512 MiB
                                                                                                                                                     
     /                  /dev/sdx3        Linux (ext4)              No                Remainder of the device
                                                                                                                                                             
                                                                                                                                                                    WARNING: If dual-booting with an existing installation of Windows on a UEFI/GPT system,
    avoid reformatting the UEFI partition, as this includes the Windows .efi file required to boot it.
        """
     elif partition_table == 'dos':
        print """
    For the MBR partition table, the suggested partition scheme looks like this:
    mountpoint        partition        partition type            boot flag        suggested size
    _________________________________________________________________________________________
    [SWAP]            /dev/sdx1        Linux swap                No                More than 512 MiB
    /                 /dev/sdx2        Linux (ext4)              Yes               Remainder of the device
    """
     go_on = raw_input("> I've read this and wish to continue to the partitioner. [Y/n]: ").lower() or 'yes'
     if go_on in yes:
        partitioner(partition_table)
     else:
        partition_devices(partition_table)

def partitioner(partition_table):
    sp.call("clear", shell=True)
    sp.call('cfdisk {0}'.format(drive), shell=True)
    sp.call("clear", shell=True)
    sp.call('lsblk {0}'.format(drive), shell=True)
    check_sure = raw_input("> Are you sure your partitions are set up correctly? [Y/n]: ").lower() or 'yes'
    if check_sure in yes:
        format_partitions()
    else:
        partitioner(partition_table)

def auto_partition():
    global ROOT
    global BOOT
    global SWAP

    logger.debug("Format Partitions")
    system("clear")
    print "Step 6) Formatting Drive..."
    system("sgdisk --zap-all {0}".format(drive))
    if gpt:
        if uefi:
            if swap_space != 'None':
                system('echo -e "n\n\n\n512M\nef00\nn\n3\n\n+{0}\n8200\nn\n\n\n\n\nw\ny" | gdisk {1}'.format(swap_space, drive))
                SWAP = sp.check_output("lsblk | grep %s | awk '{ if (NR==4) print substr ($1,3) }'" % (drive[-3:]), shell=True).rstrip()
                system("wipefs -afq /dev/{0}".format(SWAP))
                system("mkswap /dev/{0}".format(SWAP))
                system("swapon /dev/{0}".format(SWAP))
            else:
                system('echo -e "n\n\n\n512M\nef00\nn\n\n\n\n\nw\ny" | gdisk {0}'.format(drive))
            BOOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()
            ROOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==3) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()
        else:
            if swap_space != 'None':
                system('echo -e "o\ny\nn\n1\n\n+100M\n\nn\n2\n\n+1M\nEF02\nn\n4\n\n+{0}\n8200\nn\n3\n\n\n\nw\ny" | gdisk {1}'.format(swap_space, drive))
                SWAP = sp.check_output("lsblk | grep %s |  awk '{ if (NR==5) print substr ($1,3) }'" % (drive[-3:]), shell=True).rstrip()
                system("wipefs -afq /dev/{0}".format(SWAP))
                system("mkswap /dev/{0}".format(SWAP))
                system("swapon /dev/{0}".format(SWAP))
            else:
                system('echo -e "o\ny\nn\n1\n\n+100M\n\nn\n2\n\n+1M\nEF02\nn\n3\n\n\n\nw\ny" | gdisk {0}'.format(drive))
            BOOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()
            ROOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==4) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()
    else:
        if swap_space != 'None':
            system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n3\n\n+{0}\nt\n\n82\nn\np\n2\n\n\nw" | fdisk {1}'.format(swap_space, drive))
            SWAP = sp.check_output("lsblk | grep %s |  awk '{ if (NR==4) print substr ($1,3) }'" % (drive[-3:]), shell=True).rstrip()
            system("wipefs -afq /dev/{0}".format(SWAP))
            system("mkswap /dev/{0}".format(SWAP))
            system("swapon /dev/{0}".format(SWAP))
        else:
            system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n2\n\n\nw" | fdisk {0}'.format(drive))
        BOOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()
        ROOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==3) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()
    # Create Boot Partition
    system("wipefs -afq /dev/{0}".format(BOOT))
    if uefi:
        ret = system("mkfs.vfat -F32 /dev/{0}".format(BOOT))
        if ret != 0:
            raise Exception("MKFS FAILURE")
    else:
        ret = system("mkfs.ext4 /dev/{0}".format(BOOT))
        if ret != 0:
            raise Exception("MKFS FAILURE")

    # Create Root Partition
    ret = system("wipefs -afq /dev/{0}".format(ROOT))
    if ret != 0:
        raise Exception("MKFS FAILURE")
    if fs == 'jfs' or fs == 'reiserfs':
        ret = system('echo -e "y" | mkfs.{0} /dev/{1}'.format(fs, ROOT))
        if ret != 0:
            raise Exception("MKFS FAILURE")
    else:
        ret = system('mkfs.{0} /dev/{1}'.format(fs, ROOT))
        if ret != 0:
            raise Exception("MKFS FAILURE")

    system("mount /dev/{0} /mnt".format(ROOT))
    system("mkdir -p /mnt/boot")
    system("mount /dev/{0} /mnt/boot".format(BOOT))

    install_base()

def auto_encrypt():
    global ROOT
    global BOOT
    global SWAP

    print "WARNING! This will encrypt {0}".format(drive)
    cont = raw_input("> Continue? [y/N]: ").lower() or 'no'
    if cont in no:
        partition_menu()
    pass_set = False
    while not pass_set:
        passwd = getpass("> Please enter a new password for {0}: ".format(drive))
        passwd_chk = getpass("> New {0} password again: ".format(drive))
        if passwd == passwd_chk:
            pass_set = True
        else:
            print "Password do not Match."

    if gpt:
        if uefi:
            system('echo -e "n\n\n\n512M\nef00\nn\n\n\n\n\nw\ny" | gdisk {0}'.format(drive))
            BOOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()
            ROOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==3) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()
        else:
            system('echo -e "o\ny\nn\n1\n\n+100M\n\nn\n2\n\n+1M\nEF02\nn\n3\n\n\n\nw\ny" | gdisk {0}'.format(drive))
            BOOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==4) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()
            ROOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()
    else:
        system('echo -e "o\nn\np\n1\n\n+100M\nn\np\n2\n\n\nw" | fdisk {0}'.format(drive))
        BOOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==2) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()
        ROOT = sp.check_output(''' lsblk | grep %s |  awk '{ if (NR==3) print substr ($1,3) }' ''' % (drive[-3:]), shell=True).rstrip()

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

    system("wipefs -afq /dev/mapper/root")
    if fs == 'jfs' or fs == 'reiserfs':
        ret = system('echo -e "y" | mkfs.{0} /dev/mapper/root'.format(fs))
        if ret != 0:
            raise Exception("MKFS FAILURE")
    else:
        ret = system('mkfs.{0} /dev/mapper/root'.format(fs))
        if ret != 0:
            raise Exception("MKFS FAILURE")

    if uefi:
        ret = system("mkfs.vfat -F32 /dev/".format(BOOT))
        if ret != 0:
            raise Exception("MKFS FAILURE")
    else:
        system("wipefs -afq /dev/{0}".format(BOOT))
        ret = system("mkfs.ext4 /dev/{0}".format(BOOT))
        if ret != 0:
            raise Exception("MKFS FAILURE")

    system("mount /dev/mapper/root /mnt")
    system("mkdir -p /mnt/boot")
    system("mount /dev/{0} /mnt/boot".format(BOOT))

    install_base()

def install_base():
    logger.debug("Install Base")
    base = 1
    while True:
        system("clear")
        print "Step 7) Install System Base"
        print """
        Select Your Base

        1) Arch-Linux-Base

        2) Arch-Linux-Base-Devel

        3) Arch-Linux-GrSec

        4) Arch-Linux-LTS-Base

        5) Arch-Linux-LTS-Base-Devel
        """
        choice = raw_input("> Choice (Default is Arch-Linux-Base): ") or 1
        try:
            if int(choice) in range(1,6):
                base = int(choice)
                break
        except:
            print "Invalid Option"
            time.sleep(1)

    if base == 1:
        base_install = "sudo"
    elif base == 2:
        base_install = "base-devel"
    elif base == 3:
        base_install = "linux-grsec sudo"
    elif base == 4:
        base_install = "linux-lts sudo"
    elif base == 5:
        base_install = "base-devel linux-lts"

    if uefi:
        base_install += " efibootmgr"

    system("pacstrap /mnt base {0}".format(base_install))

    genfstab()

def genfstab():
    logger.debug("Genfstab")
    system("clear")
    print "Step 8) Generating fstab..."
    time.sleep(3)
    system("genfstab -U /mnt >> /mnt/etc/fstab")
    edit = raw_input("> Would you like to edit the generated fstab? [y/N]: ").lower() or 'no'
    if edit in yes:
        system("nano /mnt/etc/fstab")
    locale_and_time()

def locale_and_time():
    logger.debug("Locale and Time")
    system("clear")
    print "Step 9) Generating locale and setting timezone"
    print "Now you will edit the locale list."
    print "Remove the # in front of the locale your want."
    time.sleep(3)
    system("nano /mnt/etc/locale.gen")
    system("locale-gen", True) ## dont launch shell. just run a command
    print "Setting up keyboard layout, will take the current one."
    layout = system("localectl | grep Locale | cut -d ':' -f 2")
    system("echo {0} >> /mnt/etc/vconsole.conf".format(layout))
    print "Setting up timezone."
    system("tzselect > /tmp/archstrike-timezone", True)
    system("ln -s /usr/share/zoneinfo/$(cat /tmp/archstrike-timezone) /etc/localtime", True)
    system("hwclock --systohc --utc")
    gen_initramfs()

def gen_initramfs():
    if part_type !=2 and not uefi:
        logger.debug("Gen Initramfs")
        system("clear")
        print "Step 10) Generate initramfs image..."
        time.sleep(3)
        system("mkinitcpio -p linux", True)

    setup_bootloader()

# TODO: systemd-bootloader and syslinux
def setup_bootloader():
    logger.debug("Setup Bootloader")
    system("clear")
    print "Setting up GRUB bootloader"
    time.sleep(3)

    system("pacman -S grub --noconfirm", True)

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
    print "Configuring System"
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
    print "Step 11) Setting Hostname"
    print "Your hostname will be 'archstrike'. You can change it later if you wish."
    time.sleep(3)
    system("echo archstrike > /etc/hostname", True)
    setup_internet()

def setup_internet():
    logger.debug("Setup Internet")
    system("clear")
    print "Step 12) Setup Internet"
    wireless = raw_input("> Do you want wireless utilities on your new install? [Y/n]: ").lower() or 'yes'
    if wireless in yes:
        print "Installing Wireless utilities"
        system("pacman -S iw wpa_supplicant dialog --noconfirm", True)
    dhcp = raw_input("> Would you like to enable DHCP? [Y/n]: ").lower() or 'yes'
    if dhcp in yes:
        print "Enabling DHCP"
        system("systemctl enable dhcpcd", True)
    set_root_pass()

def set_root_pass():
    logger.debug("Set root Pass")
    system("clear")
    print "Step 13) Setting root password"
    ret = -1
    while ret != 0:
        ret = system("passwd", True)
    install_archstrike()

def install_archstrike():
    logger.debug("Install ArchStrike")
    system("clear")
    print "Step 14) Installing the ArchStrike repositories..."
    time.sleep(3)
    system("echo '[archstrike]' >> /mnt{0}".format(pacmanconf))
    system("echo 'Server = https://mirror.archstrike.org/$arch/$repo' >> /mnt{0}".format(pacmanconf))
    print "Done. It's mandatory to enable multilib for x86_64. Do you want to enable multilib? (say no if it's already enabled)"
    bit = raw_input("> [Y/n]:").lower() or 'yes'
    if bit in yes:
        system("""sed -i '/\[multilib]$/ {
			N
			/Include/s/#//g}' /mnt/%s
        """ % (pacmanconf))
        system('''/bin/bash -c " echo -e 'y\ny\n' |pacman -S gcc-multilib"''', True)
        print "Multilib has been enabled."
    else:
        print "Alright, looks like no. Continuing."
    print "I will now perform database updates, hang tight."
    system("pacman -Syy", True)
    print "Installing ArchStrike keyring and mirrorlist.."
    system("pacman-key --init", True)
    system("dirmngr < /dev/null", True)
    system("pacman-key -r 7CBC0D51", True)
    system("pacman-key --lsign-key 7CBC0D51", True)
    system("pacman -S archstrike-keyring --noconfirm", True)
    system("pacman -S archstrike-mirrorlist --noconfirm", True)
    print "Done. Editing your pacman config to use the new mirrorlist."
    system("sed -i 's|Server = https://mirror.archstrike.org/$arch/$repo|Include = /etc/pacman.d/archstrike-mirrorlist|' /mnt{0}".format(pacmanconf))
    testing = raw_input("> Do you want to add archstrike-testing as well? [Y/n]: ").lower() or 'yes'
    if testing in yes:
        system("echo '[archstrike-testing]' >> /mnt{0}".format(pacmanconf))
        system("echo 'Include = /etc/pacman.d/archstrike-mirrorlist' >> /mnt{0}".format(pacmanconf))
    else:
          print "Alright going forward."
    print "Performing database update once more to test mirrorlist"
    system("pacman -Syy", True)
    install_now = raw_input("> Do you want to go ahead and install all ArchStrike packages now? [y/N]: ").lower() or 'no'
    if install_now in yes:
        system('''/bin/bash -c " echo -e 'y\n'| pacman -S cryptsetup-nuke-keys"''', True)
        system("pacman -S archstrike linux-headers --noconfirm", True)
    add_user()

def add_user():
    global username
    username = ''

    logger.debug("Add User")
    system("clear")
    print "Step 15) Add new User"
    opt =  raw_input("> Would you like to add a new user? [Y/n]: ").lower() or 'yes'
    if opt in yes:
        while not username:
            username = raw_input("> Please enter a username: ")
        system("useradd -m -g users -G audio,network,power,storage,optical {0}".format(username), True)
        print "> Please enter the password for {0}: ".format(username)
        ret = -1
        while ret != 0:
            ret = system("passwd {0}".format(username), True)
        admin = raw_input("> Would you like to give {0} admin privileges? [Y/n]: ".format(username)).lower() or 'yes'
        if admin in yes:
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
    print "Step 16) Setting up video and desktop environment"
    choice = raw_input("> Would you like to set up video utilities? [Y/n]: ").lower() or 'yes'
    if choice in yes:
        print "To setup video utilities select your GPU. (Leave empty if unsure)"
        print """

        1) mesa-libgl

        2) nvidia

        3) xf86-video-ati

        4) xf86-video-intel
        """
        gpu = raw_input("> Choose an option or leave empty for default: ") or '5'
        try:
            sel = gpus[gpu]
            system("pacman -S xorg-server xorg-server-utils xorg-xinit xterm {0} --noconfirm".format(sel), True)
        except KeyError:
            print "Not a valid option"
            set_video_utils(username)

    desktop = raw_input("> Would you like to install a Desktop Environment or Window Manager? [Y/n]: ") or 'yes'
    if desktop in yes:
        opt = ''
        while not opt:
            print """
            Available Options:

            1) OpenBox

            2) Xfce

            3) i3wm

            4) All
            """
            opt = raw_input("> Choice: ")
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

    lm = raw_input("> Would you like to install a login manager? [Y/n]: ").lower() or 'yes'
    if lm in yes:
        system("pacman -S lightdm lightdm-gtk-greeter --noconfirm", True)
        system("systemctl enable lightdm.service", True)

    vb = raw_input("> Would you like to install virtualbox utils? [Y/n]: ").lower() or 'yes'
    if vb in yes:
        system("pacman -S virtualbox-guest-utils linux-headers mesa-libgl --noconfirm", True)

    touchpad = raw_input("> Would you like to add touchpad support? [y/N]: ").lower() or 'no'
    if  touchpad in yes:
        system("pacman -S xf86-input-synaptics --noconfirm", True)

    bluetooth = raw_input("> Would you like to add bluetooth support? [y/N]: ").lower() or 'no'
    if bluetooth in yes:
        system("pacman -S blueman --noconfirm", True)

    finalize()

def finalize():
    logger.debug("Finalize")
    system("clear")
    print "FINAL: Your system is set up! Rebooting now.."
    print "Thanks for installing ArchStrike!"
    system("umount -R /mnt")
    while True:
        reboot = raw_input("> Would you like to reboot now? (type yes or no): ").lower()
        if reboot == 'yes':
            system("reboot")
        elif reboot == 'no':
            break
        else:
            print "Please type yes or no"


if __name__ == '__main__':
    try:
        FNULL = open(os.devnull, 'w')
        signal.signal(signal.SIGINT, signal_handler)
        main()
    except Exception as e:
        logger.error(e)
        sp.Popen("umount -R /mnt", stdout=FNULL, stderr=sp.STDOUT, shell=True)
        print "\n\nAn error has occured, see /tmp/archstrike-installer.log for details."
        FNULL.close()
