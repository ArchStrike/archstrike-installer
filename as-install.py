#!/usr/bin/env python2
import subprocess as sp
import urllib2
import time
import sys
import os

## Set some variables for being lazy later on
yes = ['y', 'ye', 'yes', 'Y', 'YE', 'YES']
no = ['n', 'no', 'N', 'NO']
pacmanconf = "/etc/pacman.conf"
archstrike_mirrorlist = "/etc/pacman.d/archstrike-mirrorlist"

def main():
    print """
    Welcome to the ArchStrike Installer!
    This was coded by Wh1t3Fox and xorond for the ArchStrike Project
    """
    time.sleep(3)
    print """
    Now you can choose an option from below.

    1) Start the ArchStrike Installer (will install ArchStrike on your hard drive)

    2) Choose an individual step in the installation process

    99) Exit
    """
    choice = raw_input("> Enter the number of your choice: ")
    if choice == "1":
        start()
    elif choice == "2":
        menu()
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
    elif step == "99":
        main()
    else:
        print "Not sure what you're talking about."
        main()

def start():
    sp.call("clear", shell=True)
    print "Performing some checks before we continue.."
    time.sleep(3)
    if internet_on() == False:
        print "Looks like you're not connected to the internet. Exiting."
        sys.exit()
        print "Checks done. I will now start the installation process."
    if os.geteuid() != 0:
        exit("Run as root/sudo please.\nExiting now")
    ## update system clock
    sp.call("timedatectl set-ntp true", shell=True)
    check_uefi()

## internet check function
def internet_on():
    try:
        response=urllib2.urlopen('http://google.com',timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False

## uefi check function
def check_uefi():
    sp.call("clear", shell=True)
    print "Step 1) UEFI mode / No UEFI mode"
    time.sleep(3)
    uefi = raw_input("> Is your computer running a UEFI board? (y/N): ").lower() or 'no'
    if uefi in yes:
        try:
            os.listdir('/sys/firmware/efi/efivars')
        except OSError:
            # Dir doesnt exist
            print "Your computer doesnt seem to be running a UEFI board. Continuing.."
            set_keymap()
    elif uefi in no:
        print "Going to the next step."
        set_keymap()
    else:
        print "Not sure what you're talking about."
        check_uefi()

## keymap check function
def set_keymap():
    sp.call("clear", shell=True)
    print "Step 2) Setting your keymap"
    time.sleep(3)
    print "I'm setting your keyboard layout now, default is US."
    choice = raw_input("> Do you want to change the keyboard layout? [y/N]: ").lower() or 'no'
    if choice in yes:
        sp.call("ls /usr/share/kbd/keymaps/**/*.map.gz", shell=True)
        layout = raw_input("> Enter the keyboard layout you want: ")
        sp.call("loadkeys {0}".format(layout), shell=True)
        weirdfont = raw_input("> Try typing in here to test. If some characters are coming up different, delete it all and type 'Y': ")
        if weirdfont in yes:
            sp.call("setfont lat9w-16", shell=True)
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

    sp.call("clear", shell=True)
    print "Step 3) Preparing your hard drive to install ArchStrike"
    time.sleep(3)
    print "Listing your partitions now."
    sp.call("lsblk", shell=True)
    print "Results ending in 'rom', 'loop' or 'airoot' can be ignored."
    drive = raw_input("> Please choose the drive you want to install ArchStrike on (default: /dev/sda ): ") or '/dev/sda'
    ## idiotproofing
    sure = raw_input("You chose {0}. Are you sure about that? Choosing the wrong drive may have very bad consequences!: ".format(drive))
    if sure in no:
        identify_devices()
    print "I will now check the partition table in {0}.".format(drive)
    partition_table = sp.check_output("fdisk -l {0} | grep Disklabel | cut -d ' ' -f 3".format(drive), shell=True).rstrip()
    print "Looks like {0} has {1} partition table".format(drive, partition_table)
    partition_devices(drive, partition_table)

## let's actually partition now
def partition_devices(drive, partition_table):
    sp.call("clear", shell=True)
    print "Step 4) Partitioning the devices (be careful during this step)"
    time.sleep(3)
    print "I'm now going to print the current partition scheme of your drive %s" % drive
    print "But first let's confirm everything."
    ## making it idiotproof
    confirm_drive = raw_input("> Please confirm that {0} is the drive you chose by typing it again: ".format(drive))
    if confirm_drive != drive:
        print "That doesn't look right. Let's try identifying those again."
        identify_devices()
    confirm_table = raw_input("> Please confirm that {0} is the partition table of {1} by typing it again: ".format(partition_table, drive))
    if confirm_table != partition_table:
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

