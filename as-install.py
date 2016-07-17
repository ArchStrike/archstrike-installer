#!/usr/bin/env python2
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


## Set some variables for being lazy later on
yes = ['y', 'ye', 'yes', 'Y', 'YE', 'YES']
no = ['n', 'no', 'N', 'NO']
pacmanconf = "/etc/pacman.conf"
archstrike_mirrorlist = "/etc/pacman.d/archstrike-mirrorlist"

def signal_handler(signal, handler):
    pass #ignore sigint


def system(command, chroot=False):
    if command == 'clear':
        sp.call(command, shell=True)
        return

    if chroot:
        command = "arch-chroot /mnt {0}".format(command)

    logger.debug(command)

    try:
        sp.call([command], shell=True)
    except:
        logger.error(stderr)

def main():
    logger.debug("Starting Installation")

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
    logger.debug("Check UEFI")
    system("clear")
    print "Step 1) UEFI Mode Check"
    time.sleep(3)
    uefi = raw_input("> Are you running a UEFI board? (y/N): ").lower() or 'no'
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
    logger.debug("Set Keymap")
    system("clear")
    print "Step 2) Keymap Setup"
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
    global partition_table

    logger.debug("Identify Devices")
    system("clear")
    print "Step 3) HDD Preparation"
    time.sleep(3)
    print "Current Partitions"
    system("lsblk")
    print "*NOTE: Results ending in 'rom', 'loop' or 'airoot' can be ignored."
    drive = raw_input("> Please choose the drive you would like to install ArchStrike on (default: /dev/sda ): ") or '/dev/sda'
    ## idiotproofing
    sure = raw_input("Are you sure want to use {0}? Choosing the wrong drive may have very bad consequences!: ".format(drive))
    if sure in no:
        identify_devices()
    print "Checking the partition table in {0}...".format(drive)
    partition_table = sp.check_output("fdisk -l {0} | grep Disklabel | cut -d ' ' -f 3".format(drive), shell=True).rstrip()
    print "{0} has a {1} partition table".format(drive, partition_table)
    partition_devices(drive, partition_table)

## let's actually partition now
def partition_devices(drive, partition_table):
    logger.debug("Partition Devices")
    system("clear")
    print "Step 4) Partitioning the devices (be careful during this step)"
    time.sleep(3)
    ## making it idiotproof
    confirm_drive = raw_input("> Please confirm your drive by typing {0}: ".format(drive))
    if confirm_drive != drive:
        print "That doesn't look right. Let's try identifying those again."
        identify_devices()
    if partition_table:
        confirm_table = raw_input("> Please confirm partition table of {1} by typing {0}: ".format(partition_table, drive))
        if confirm_table != partition_table:
            print "That doesn't look right. Let's try identifying those again."
            identify_devices()
    print "Looks like both are confirmed."
    system("lsblk {0}".format(drive))
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
    logger.debug("Partitioner")
    system("clear")
    system('cfdisk {0}'.format(drive))
    system("clear")
    system('lsblk {0}'.format(drive))
    check_sure = raw_input("> Are you sure your partitions are set up correctly? [Y/n]: ").lower() or 'yes'
    if check_sure in yes:
        format_partitions()
    else:
        partitioner(partition_table)

def format_partitions():
    logger.debug("Format Partitions")
    system("clear")
    print "Step 5) Formatting partitions"
    time.sleep(3)
    print "Current partition scheme of {0}".format(drive)
    system("lsblk %s" % drive)
    partitions = raw_input("> Enter all the partitions you created by seperating them with a comma (e.g. /dev/sda1,/dev/sda2): ").split(',')
    print "You sure these are the partitions?"
    print '\n'.join(partitions)
    sure = raw_input("> [Y/n]: ").lower() or 'yes'
    if sure in yes:
        print "Alright, starting to format."
        for i in partitions:
            print "Partition {0} will be formatted now".format(i)
            partition_type = raw_input("> Enter the partition type (linux, uefi, swap): ").lower()
            if partition_type == 'linux':
                system("mkfs.ext4 {0}".format(i))
            elif partition_type == 'uefi':
                system("mkfs.fat -F32 {0}".format(i))
            elif partition_type == 'swap':
                system("mkswap {0}".format(i))
                system("swapon {0}".format(i))
            else:
                print "Not sure what you're talking about."
                format_partitions()
        mount_partitions(partitions)
    else:
        format_partitions()

def mount_partitions(partitions):
    logger.debug("Mount Partitions")
    system("clear")
    print "Step 6) Mounting the partitions"
    time.sleep(3)
    ## get individual partition fs types so we can mount / in /mnt
    print '\n'.join(partitions)
    root = raw_input("Which one is your / mounted partition? (e.g. /dev/sda1): ")
    if root in partitions:
        print "Mounting {0} on /mnt".format(root)
        system("mount {0} /mnt".format(root))
    else:
        mount_partitions(partitions)
    if partition_table == 'gpt':
        boot = raw_input("Which one is your /boot mounted partition? (e.g. /dev/sda2): ")
        if boot in partitions:
            print "Mounting %s on /mnt/boot" % boot
            system("mkdir -p /mnt/boot")
            system("mount {0} /mnt/boot".format(boot))
        else:
            mount_partitions(partitions)
    else:
        system("mkdir -p /mnt/boot")
    install_base()

def install_base():
    logger.debug("Install Base")
    system("clear")
    print "Step 7) Installing the base system"
    print "Starting base install.."
    time.sleep(3)
    system("pacstrap /mnt base base-devel")
    genfstab()

def genfstab():
    logger.debug("Genfstab")
    system("clear")
    print "Step 8) Generating fstab"
    print "Starting now..."
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
    logger.debug("Gen Initramfs")
    system("clear")
    print "Step 10) Generate initramfs image"
    print "Starting now.."
    time.sleep(3)
    system("mkinitcpio -p linux", True)
    setup_bootloader()

def setup_bootloader():
    logger.debug("Setup Bootloader")
    system("clear")
    print "Step 11) Setting up GRUB bootloader"
    print "Starting GRUB install now."
    time.sleep(3)
    system("pacman -S grub --noconfirm", True)
    system("grub-install {0}".format(drive), True)
    system("grub-mkconfig -o /boot/grub/grub.cfg ", True)
    # TODO: systemd-bootloader and syslinux
    set_hostname()

def set_hostname():
    logger.debug("Set Hostname")
    system("clear")
    print "Step 12) Set Hostname"
    print "Your hostname will be 'archstrike'. You can change it later if you wish."
    time.sleep(3)
    system("echo archstrike > /etc/hostname", True)
    setup_internet()

def setup_internet():
    logger.debug("Setup Internet")
    system("clear")
    print "Step 13) Setup Internet"
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
    print "Step 14) Setting root password"
    print "You will be prompted to choose a root password now."
    time.sleep(3)
    system("passwd", True)
    install_archstrike()

def install_archstrike():
    logger.debug("Install ArchStrike")
    system("clear")
    print "Step 15)"
    print "Now to install the ArchStrike repositories."
    print "Adding repositories.."
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
        system('/bin/bash -c "yes|pacman -S gcc-multilib gcc-libs-multilib"', True)
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
    install_now = raw_input("> Do you want to go ahead and install all ArchStrike packages now? [Y/n]: ").lower() or 'yes'
    if install_now in yes:
        system('/bin/bash -c "yes| pacman -S cryptsetup-nuke-keys"', True)
        system("pacman -S archstrike --noconfirm", True)
    add_user()

def add_user():
    global username
    username = ''

    logger.debug("Add User")
    system("clear")
    print "Step 16) Add new User"
    opt =  raw_input("> Would you like to add a new user? [Y/n]: ").lower() or 'yes'
    if opt in yes:
        while not username:
            username = raw_input("> Please enter a username: ")
        system("useradd -m -g users -G audio,network,power,storage,optical {0}".format(username), True)
        print "> Please enter the password for {0}: ".format(username)
        system("passwd {0}".format(username), True)
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
    time.sleep(3)
    system("umount -R /mnt")
    system("reboot")

if __name__ == '__main__':
    try:
        signal.signal(signal.SIGINT, signal_handler)
        main()
    except Exception as e:
        logger.error(e)
        print "\n\nAn error has occured, see /tmp/archstrike-installer.log for details."
