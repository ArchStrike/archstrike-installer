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

def format_partitions():
    sp.call("clear", shell=True)
    print "Step 5) Formatting partitions"
    time.sleep(3)
    print "Showing the current partition scheme of {0}".format(drive)
    sp.call("lsblk %s" % drive, shell=True)
    partitions = raw_input("> Enter all the partitions you created by seperating them with a comma: ").split(',')
    print "You sure these are the partitions?"
    print '\n'.join(partitions)
    sure = raw_input("> [Y/n]: ").lower() or 'yes'
    if sure in yes:
        print "Alright, starting to format."
        for i in partitions:
            print "Partition {0} will be formatted now".format(i)
            partition_type = raw_input("> Enter the partition type (linux, uefi, swap): ").lower()
            if partition_type == 'linux':
                sp.call("mkfs.ext4 {0}".format(i), shell=True)
            elif partition_type == 'uefi':
                sp.call("mkfs.fat -F32 {0}".format(i), shell=True)
            elif partition_type == 'swap':
                sp.call("mkswap {0}".format(i), shell=True)
                sp.call("swapon {0}".format(i), shell=True)
            else:
                print "Not sure what you're talking about."
                format_partitions()
        mount_partitions(partitions)
    else:
        format_partitions()

def mount_partitions(partitions):
    sp.call("clear", shell=True)
    print "Step 6) Mounting the partitions"
    time.sleep(3)
    ## get individual partition fs types so we can mount / in /mnt
    print '\n'.join(partitions)
    root = raw_input("Which one is your / mounted partition?: ")
    if root in partitions:
        print "Mounting {0} on /mnt".format(root)
        sp.call("mount {0} /mnt".format(root), shell=True)
    else:
        mount_partitions(partitions)
    if len(partitions) > 1:
        boot = raw_input("Which one is your /boot mounted partition?: ")
        if boot in partitions:
            print "Mounting %s on /mnt/boot" % boot
            sp.call("mkdir -p /mnt/boot", shell=True)
            sp.call("mount {0} /mnt/boot".format(boot), shell=True)
        else:
            mount_partitions(partitions)
    else:
        sp.call("mkdir -p /mnt/boot", shell=True)
    install_base()

def install_base():
    sp.call("clear", shell=True)
    print "Step 7) Installing the base system"
    print "Starting base install.."
    time.sleep(3)
    sp.call("pacstrap /mnt base base-devel", shell=True)
    genfstab()

def genfstab():
    sp.call("clear", shell=True)
    print "Step 8) Generating fstab"
    print "Starting now.."
    time.sleep(3)
    sp.call("genfstab -U /mnt >> /mnt/etc/fstab", shell=True)
    edit = raw_input("> Would you like to edit the generated fstab? [y/N]: ").lower() or 'no'
    if edit in yes:
        sp.call("nano /mnt/etc/fstab")
    locale_and_time()

def locale_and_time():
    sp.call("clear", shell=True)
    print "Step 9) Generating locale and setting timezone"
    print "Now you will edit the locale list."
    print "Remove the # in front of the locale your want."
    time.sleep(3)
    sp.call("nano /mnt/etc/locale.gen", shell=True)
    sp.call("arch-chroot /mnt locale-gen", shell=True) ## dont launch shell. just run a command
    print "Setting up keyboard layout, will take the current one."
    layout = sp.call("localectl | grep Locale | cut -d ':' -f 2", shell=True)
    sp.call("echo {0} >> /mnt/etc/vconsole.conf".format(layout), shell=True)
    print "Setting up timezone."
    sp.call("arch-chroot /mnt tzselect > /tmp/archstrike-timezone", shell=True)
    sp.call("arch-chroot /mnt ln -s /usr/share/zoneinfo/$(cat /tmp/archstrike-timezone) /etc/localtime", shell=True)
    sp.call("hwclock --systohc --utc", shell=True)
    gen_initramfs()

def gen_initramfs():
    sp.call("clear", shell=True)
    print "Step 10) Generate initramfs image"
    print "Starting now.."
    time.sleep(3)
    sp.call("arch-chroot /mnt mkinitcpio -p linux", shell=True)
    setup_bootloader()

def setup_bootloader():
    sp.call("clear", shell=True)
    print "Step 11) Setting up GRUB bootloader"
    print "Starting GRUB install now."
    time.sleep(3)
    sp.call("arch-chroot /mnt pacman -S grub --noconfirm", shell=True)
    sp.call("arch-chroot /mnt grub-install {0}".format(drive), shell=True)
    sp.call("arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg ", shell=True)
    # TODO: systemd-bootloader and syslinux
    set_hostname()

def set_hostname():
    sp.call("clear", shell=True)
    print "Step 12) Set Hostname"
    print "Your hostname will be 'archstrike'. You can change it later if you wish."
    time.sleep(3)
    sp.call("arch-chroot /mnt echo archstrike > /etc/hostname", shell=True)
    setup_internet()

def setup_internet():
    sp.call("clear", shell=True)
    print "Step 13) Setup Internet"
    wireless = raw_input("> Do you want wireless utilities on your new install? [Y/n]: ").lower() or 'yes'
    if wireless in yes:
        print "Installing Wireless utilities"
        sp.call("arch-chroot /mnt pacman -S iw wpa_supplicant dialog --noconfirm", shell=True)
    dhcp = raw_input("> Would you like to enable DHCP? [Y/n]: ").lower() or 'yes'
    if dhcp in yes:
        print "Enabling DHCP"
        sp.call("arch-chroot /mnt systemctl enable dhcpcd", shell=True)
    set_root_pass()

def set_root_pass():
    sp.call("clear", shell=True)
    print "Step 14) Setting root password"
    print "You will be prompted to choose a root password now."
    time.sleep(3)
    sp.call("arch-chroot /mnt passwd", shell=True)
    install_archstrike()

def install_archstrike():
    sp.call("clear", shell=True)
    print "Step 15)"
    print "Now to install the ArchStrike repositories."
    print "Adding repositories.."
    time.sleep(3)
    sp.call("echo '[archstrike]' >> /mnt{0}".format(pacmanconf), shell=True)
    sp.call("echo 'Server = https://mirror.archstrike.org/$arch/$repo' >> /mnt{0}".format(pacmanconf), shell=True)
    print "Done. It's mandatory to enable multilib for x86_64. Do you want to enable multilib? (say no if it's already enabled)"
    bit = raw_input("> [Y/n]:").lower() or 'yes'
    if bit in yes:
        sp.call("""sed -i '/\[multilib]$/ {
			N
			/Include/s/#//g}' /mnt/%s
        """ % (pacmanconf), shell=True)
        sp.call('arch-chroot /mnt /bin/bash -c "yes|pacman -S gcc-multilib gcc-libs-multilib"', shell=True)
        print "Multilib has been enabled."
    else:
        print "Alright, looks like no. Continuing."
    print "I will now perform database updates, hang tight."
    sp.call("arch-chroot /mnt pacman -Syy", shell=True)
    print "Installing ArchStrike keyring and mirrorlist.."
    sp.call("arch-chroot /mnt pacman-key --init", shell=True)
    sp.call("arch-chroot /mnt dirmngr < /dev/null", shell=True)
    sp.call("arch-chroot /mnt pacman-key -r 7CBC0D51", shell=True)
    sp.call("arch-chroot /mnt pacman-key --lsign-key 7CBC0D51", shell=True)
    sp.call("arch-chroot /mnt pacman -S archstrike-keyring --noconfirm", shell=True)
    sp.call("arch-chroot /mnt pacman -S archstrike-mirrorlist --noconfirm", shell=True)
    print "Done. Editing your pacman config to use the new mirrorlist."
    sp.call("sed -i 's|Server = https://mirror.archstrike.org/$arch/$repo|Include = /etc/pacman.d/archstrike-mirrorlist|' /mnt{0}".format(pacmanconf), shell=True)
    testing = raw_input("> Do you want to add archstrike-testing as well? [Y/n]: ").lower() or 'yes'
    if testing in yes:
        sp.call("echo '[archstrike-testing]' >> /mnt{0}".format(pacmanconf), shell=True)
        sp.call("echo 'Include = /etc/pacman.d/archstrike-mirrorlist' >> /mnt{0}".format(pacmanconf), shell=True)
    else:
          print "Alright going forward."
    print "Performing database update once more to test mirrorlist"
    sp.call("arch-chroot /mnt pacman -Syy", shell=True)
    install_now = raw_input("> Do you want to go ahead and install all ArchStrike packages now? [Y/n]: ").lower() or 'yes'
    if install_now in yes:
        sp.call('arch-chroot /mnt /bin/bash -c "yes| pacman -S cryptsetup-nuke-keys"', shell=True)
        sp.call("arch-chroot /mnt pacman -S archstrike --noconfirm", shell=True)
    add_user()

def add_user():
    global username
    username = ''

    sp.call("clear", shell=True)
    print "Step 16) Add new User"
    opt =  raw_input("> Would you like to add a new user? [Y/n]: ").lower() or 'yes'
    if opt in yes:
        while not username:
            username = raw_input("> Please enter a username: ")
        sp.call("arch-chroot /mnt useradd -m -g users -G audio,network,power,storage,optical {0}".format(username), shell=True)
        print "> Please enter the password for {0}: ".format(username)
        sp.call("arch-chroot /mnt passwd {0}".format(username), shell=True)
        admin = raw_input("> Would you like to give {0} admin privileges? [Y/n]: ".format(username)).lower() or 'yes'
        if admin in yes:
            sp.call("sed -i '/%wheel ALL=(ALL) ALL/s/^#//' /mnt/etc/sudoers", shell=True)
            sp.call("arch-chroot /mnt usermod -a -G wheel {0}".format(username), shell=True)
    set_video_utils(username)

def set_video_utils(user):
    gpus = {
        1:'mesa-libgl',
        2:'nvidia',
        3:'xf86-video-ati',
        4:'xf86-video-intel',
        5:'xf86-video-vesa'
    }
    sp.call("clear", shell=True)
    print "Step 17) Setting up video and desktop environment"
    choice = raw_input("> Would you like to set up video utilities? [Y/n]: ").lower() or 'yes'
    if choice in yes:
        print "Setting up video. I need to know your GPU."
        time.sleep(2)
        print """
        Here are some options, please choose one or leave empty for default.

        1) mesa-libgl

        2) nvidia

        3) xf86-video-ati

        4) xf86-video-intel
        """
        gpu = raw_input("> Choose an option or leave empty for default") or 5
        try:
            sel = gpus[gpu]
            sp.call("arch-chroot /mnt pacman -S xorg-server xorg-server-utils xorg-xinit xterm {0} --noconfirm".format(sel), shell=True)
        except IndexError:
            print "Not a valid option"
            set_video_utils()
    desktop = raw_input("> Would you like to install the OpenBox window manager with ArchStrike configs? [Y/n]: ") or 'yes'
    if desktop in yes:
        sp.call("arch-chroot /mnt pacman -S openbox --noconfirm", shell=True)
        if username:
            sp.call("echo 'exec openbox' > /mnt/home/{0}/.xinitrc".format(username), shell=True)
        sp.call("echo 'exec openbox' > /mnt/root/.xinitrc", shell=True)

    lm = raw_input("> Would you like to install a login manager? [Y/n]: ").lower() or 'yes'
    if lm in yes:
        sp.call("arch-chroot /mnt pacman -S lightdm lightdm-gtk-greeter --noconfirm", shell=True)
        sp.call("arch-chroot /mnt systemctl enable lightdm.service", shell=True)

    touchpad = raw_input("> Would you like to add touchpad support? [y/N]: ").lower() or 'no'
    if  touchpad in yes:
        sp.call("arch-chroot /mnt pacman -S xf86-input-synaptics --noconfirm", shell=True)

    bluetooth = raw_input("> Would you like to add bluetooth support? [y/N]: ").lower() or 'no'
    if bluetooth in yes:
        sp.call("arch-chroot /mnt pacman -S blueman --noconfirm", shell=True)

    finalize()


def finalize():
    sp.call("clear", shell=True)
    print "FINAL: Your system is set up! Rebooting now.."
    print "Thanks for installing ArchStrike!"
    time.sleep(3)
    sp.call("umount -R /mnt", shell=True)
    sp.call("reboot", shell=True)

if __name__ == '__main__':
    main()
