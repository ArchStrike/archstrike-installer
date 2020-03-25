
from .config import *
from .utils import *
from . import menus, resolve_packages
import time
import shutil
import os

logger = setup_logger(__name__)


def base():  # noqa
    logger.debug("Installing Base")
    base = 1
    while True:
        system("clear")
        print_title("Step 7) Install System Base")

        options = list(menus.base.keys())
        options.sort()
        for k in options:
            print_info('{0}) {1}'.format(k, menus.base[k]))

        choice = cinput('> Choice (Default is Arch-Linux-Base): ',
                        COLORS['OKBLUE']) or 1
        try:
            choice = int(choice)
            if choice in range(1, len(menus.base) + 1):
                base = choice
                break
        except:
            print_error("Invalid Option")
            time.sleep(1)

    if base == 1:
        base_install = "linux sudo"
        usr_cfg['kernel'] = 'linux'
    elif base == 2:
        base_install = "linux base-devel sudo"
        usr_cfg['kernel'] = 'linux'
    elif base == 3:
        base_install = "linux-hardened linux-hardened-headers sudo"
        usr_cfg['kernel'] = 'linux-hardened'
    elif base == 4:
        base_install = "linux-lts linux-lts-headers sudo"
        usr_cfg['kernel'] = 'linux-lts'
    elif base == 5:
        base_install = "base-devel linux-lts linux-lts-headers sudo"
        usr_cfg['kernel'] = 'linux-lts'
    if usr_cfg['uefi']:
        base_install += " efibootmgr"

    system("pacman -Syy")
    try:
        # Check if ntp command exists
        system("pacman -Qs ntp >/dev/null 2>&1")
    except:
        # Install ntp if command does not exists
        system("pacman -S ntp --noconfirm")
    else:
        # Verify ntp command is owned by ntp and not opentpd
        _conflict_check = '$(pacman -Qo /usr/bin/ntpd | grep -o "is owned by ntp ")'
        _err_msg = 'A package other than ntp owns /usr/bin/ntpd. Please install ntp manually.\n'
        _cmd = '[[ -z "{}" ]] && printf "{}" >&2'.format(_conflict_check, _err_msg)
        system(_cmd)
    # if not ntpd.service is inactive, then set time with ntpd. otherwise, pass so exits 0
    system("[[ ! -z $(systemctl status ntpd | grep 'Active: inactive') ]] &&  ntpd -qg >/dev/null 2>&1 || :")
    system("hwclock --systohc")
    # the following should be the same as pacman-key --refresh-keys --keyserver pgp.mit.edu
    # however, keyservers are too slow for my taste
    system("pacman -S archlinux-keyring --noconfirm >/dev/null")
    system("pacman -Su --noconfirm >/dev/null")
    try:
        # Check if pacstrap command exists
        system("pacman -Qo pacstrap >/dev/null")
    except:
        # Install arch-install-scripts if pacstrap does not exist
        system("pacman -S arch-install-scripts --noconfirm")
    system("pacstrap /mnt base {0}".format(base_install))


def genfstab():
    logger.debug("Genfstab")
    system("clear")
    print_title("Step 8) Generating fstab...")
    time.sleep(1)
    system("genfstab -U /mnt >> /mnt/etc/fstab")
    if query_yes_no("> Would you like to edit the generated fstab?", 'no'):
        system("nano /mnt/etc/fstab")


def locale_time():
    logger.debug("Setting locale and time")
    while True:
        system("clear")
        print_title("Step 9) Generating locale and setting timezone")

        options = list(menus.locale.keys())
        options.sort()
        for k in options:
            print_info('{0}) {1}'.format(k, menus.locale[k]))

        choice = cinput('> Enter the number for your locale or leave empty '
                        + 'for default: ', COLORS['OKBLUE']) or '1'

        if choice in list(map(str, list(range(1, len(menus.locale))))):
            locale = localesdict[str(choice)]
            break
        elif choice == '99':
            print_info("A full list will be listed now.")
            print_info("Press 'q' to quit and 'Enter'/'Return' to scroll. "
                       + "Afterwards type in the locale you want to use.")
            time.sleep(1)
            system("cat /mnt/etc/locale.gen | more")
            locale = cinput('> Please type in the locale you want to use: ',
                            COLORS['OKBLUE'])
            break

    system("sed -i '/{0}/s/^#//g' /mnt/etc/locale.gen".format(locale))
    system("locale-gen", True)
    print_info("Setting keyboard layout...")
    layout = system("localectl | grep Locale | cut -d ':' -f 2")
    system("echo {0} >> /mnt/etc/vconsole.conf".format(layout))
    print_info("Setting timezone...")
    tzcmd = "/bin/sh -c '(tzselect 3>&2 2>&1 1>&3) 2> /tmp/archstrike-timezone'"  # swap stdout/stderr so level is info
    system(tzcmd, True)
    system('ln -sf /usr/share/zoneinfo/$(cat /tmp/archstrike-timezone) '
           + '/etc/localtime', True)
    system("hwclock --systohc --utc")


def initramfs():
    logger.debug("initramfs")
    if usr_cfg['filesystem'] == 'btrfs':
        system("pacman -S --noconfirm btrfs-progs", True)
    if usr_cfg['partition_type'] != '2' and not usr_cfg['uefi']:
        system("clear")
        print_title("Step 10) Generate initramfs image...")
        time.sleep(1)
        system(f"mkinitcpio -p {usr_cfg['kernel']}", True)


def grub():
    logger.debug("Installing GRUB")
    system("clear")
    print_title("Setting up GRUB bootloader...")
    time.sleep(1)

    system("pacman -S grub --noconfirm", True)

    if system_output("cat /proc/cpuinfo | grep -m1 vendor_id |"
                     + "awk '{print $NF}'") == 'GenuineIntel':
        if query_yes_no('We have detected you have an Intel CPU. '
                        + 'Is that correct?', 'yes'):
            system("pacman -S intel-ucode --noconfirm", True)

    if usr_cfg['partition_type'] == '2':
        system("sed -i 's!quiet!cryptdevice=/dev/lvm/lvroot:root "
               + "root=/dev/mapper/root!' /mnt/etc/default/grub")
    else:
        system("sed -i 's/quiet//' /mnt/etc/default/grub")

    if usr_cfg['uefi']:
        system('grub-install --efi-directory=/boot --target=x86_64-efi '
               + '--bootloader-id=boot', True)
        system('mv /mnt/boot/EFI/boot/grubx64.efi '
               + '/mnt/boot/EFI/boot/bootx64.efi')

        if usr_cfg['partition_type'] != '2':
            system(f"mkinitcpio -p {usr_cfg['kernel']}", True)
    else:
        system("grub-install {0}".format(usr_cfg['drive']), True)

    system("grub-mkconfig -o /boot/grub/grub.cfg ", True)


# TODO: Implement
def syslinux():
    pass


def configuration():
    logger.debug("Installing Configuration")
    system("clear")
    print_title("Configuring System...")
    time.sleep(1)

    if usr_cfg['partition_type'] == '2' and usr_cfg['uefi']:
        system('echo "/dev/{0}'.format(usr_cfg['boot'])
               + '              /boot           vfat         '
               + 'rw,relatime,fmask=0022,dmask=0022,codepage=437,'
               + 'iocharset=iso8859-1,shortname=mixed,errors=remount-ro        0'
               + '2" > /mnt/etc/fstab')
    elif usr_cfg['partition_type'] == 'Auto Partition Encrypted LVM':
        system('echo "/dev/{0}'.format(usr_cfg['boot'])
               + '              /boot           '
               + '{0}         '.format(usr_cfg['filesystem'])
               + 'defaults        0       2" > /mnt/etc/fstab')

    if usr_cfg['partition_type'] == '2':
        system('echo "/dev/mapper/root        /               '
               + '{0}         '.format(usr_cfg['filesystem'])
               + 'defaults        0       1" >> /mnt/etc/fstab')
        system('echo "/dev/mapper/tmp         /tmp            tmpfs        '
               + 'defaults        0       0" >> /mnt/etc/fstab')
        system('echo "tmp	       /dev/lvm/tmp	       /dev/urandom	tmp,'
               + 'cipher=aes-xts-plain64,size=256" >> /mnt/etc/crypttab')

        if usr_cfg['swap_space']:
            system('echo "/dev/mapper/swap     none            swap          '
                   + 'sw                    0       0" >> /mnt/etc/fstab')
            system('echo "swap	/dev/lvm/swap	/dev/urandom	swap,'
                   + 'cipher=aes-xts-plain64,size=256" >> /mnt/etc/crypttab')

        system("sed -i 's/k filesystems k/k lvm2 encrypt filesystems k/' "
               + "/mnt/etc/mkinitcpio.conf")

        system("pacman -S lvm2 --noconfirm", True)
        system(f"mkinitcpio -p {usr_cfg['kernel']}", True)


def hostname():
    logger.debug("Setting hostname")
    system("clear")
    print_title("Step 11) Setting Hostname")

    print_info("Your hostname will be 'archstrike'. "
               + "You can change it later if you wish.")
    time.sleep(1)

    system("echo 'archstrike' > /mnt/etc/hostname")


def internet():
    logger.debug("Enabling Internet")
    system("clear")
    print_title("Step 12) Setup Internet")

    if query_yes_no("> Do you want wireless utilities on your new install?",
                    'yes'):
        system("pacman -S iw wpa_supplicant dialog netctl --noconfirm", True)

    if query_yes_no("> Would you like DHCP enabled on your new install?", 'yes'):
        system("pacman -S dhcpcd --noconfirm", True)
        system("systemctl enable dhcpcd", True)


def root_passwd():
    logger.debug("Setting root password")
    system("clear")
    print_title("Step 13) Setting root password")

    ret = -1
    while ret != 0:
        ret = system("passwd", True)


def archstrike():
    logger.debug("Installing ArchStrike")
    system("clear")
    print_title("Step 14) Installing the ArchStrike repositories")
    time.sleep(1)

    system("echo '[archstrike]' >> /mnt{0}".format(pacmanconf))
    system("echo 'Server = https://mirror.archstrike.org/$arch/$repo' >> "
           + "/mnt{0}".format(pacmanconf))

    if system_output('getconf LONG_BIT') == '64':
        print_info("We have detected you are running x86_64. It is advised "
                   + "to enable multilib with the ArchStrike repo. Do you want to "
                   + "enable multilib?")

        if query_yes_no(">", 'yes'):
            system("""sed -i "/\[multilib\]/,/Include/"'s/^#//' """
                   + "/mnt/{0}".format(pacmanconf))
            print_info("I will now perform database updates, hang tight.")
            time.sleep(1)
            system("hwclock --systohc", True)
            system("pacman -Syy", True)
            system('''/bin/bash -c " echo -e 'y\ny\n' | '''
                   + 'pacman -S gcc-multilib"', True)
            print_info("Multilib has been enabled.")
        else:
            print_info("I will now perform database updates, hang tight.")
            time.sleep(1)
            system("hwclock --systohc", True)
            system("pacman -Syy", True)

    shutil.move('keyfile.asc', '/mnt/keyfile.asc')
    print_info("Installing ArchStrike keyring and mirrorlist...")
    system("pacman-key --init", True)
    system("dirmngr < /dev/null", True)
    system("pacman-key --add keyfile.asc", True)
    system("pacman-key --lsign-key 7CBC0D51", True)
    system("pacman -S archstrike-keyring --noconfirm", True)
    system("pacman -S archstrike-mirrorlist --noconfirm", True)
    print_info("Done. Editing your pacman config to use the new mirrorlist.")

    system("sed -i 's|Server = https://mirror.archstrike.org/$arch/$repo|"
           + "Include = /etc/pacman.d/archstrike-mirrorlist|' "
           + "/mnt{0}".format(pacmanconf))

    print_info("Performing database update once more to test mirrorlist")
    system("pacman -Syy", True)
    if query_yes_no('> Do you want to go ahead and install all ArchStrike '
                    + 'packages now?', 'no'):
        args = resolve_packages.get_args(['--package', 'archstrike'])
        archstrike_packages = resolve_packages.PackageArbiter(args).good_packages
        system(f"pacman -S {archstrike_packages} linux-headers --noconfirm", True)


def new_user():
    logger.debug("Adding new user")
    system("clear")
    print_title("Step 15) Add new User")
    username = ''

    if query_yes_no("> Would you like to add a new user?", 'yes'):
        while not username:
            username = cinput('> Please enter a username: ', COLORS['OKBLUE'])

        system('useradd -m -g users -G audio,network,power,'
               + 'storage,optical {0}'.format(username), True)
        print_command("> Please enter the password for {0}: ".format(username))

        ret = -1
        while ret != 0:
            ret = system("passwd {0}".format(username), True)

        if query_yes_no('> Would you like to give {0} '.format(username)
                        + 'admin privileges?', 'yes'):
            system("sed -i '/%wheel ALL=(ALL) ALL/s/^#//' /mnt/etc/sudoers")
            system("usermod -a -G wheel {0}".format(username), True)

    usr_cfg['username'] = username


def video_utils():
    logger.debug("Installing video utils")
    system("clear")
    print_title("Step 16) Setting up video and desktop environment")

    if query_yes_no("> Would you like to set up video utilities?", 'yes'):
        while True:
            options = list(menus.gpus.keys())
            options.sort()
            for k in options:
                print_info('{0}) {1}'.format(k, menus.gpus[k]))

            gpu = cinput('> Choose an option or leave empty for default: ',
                         COLORS['OKBLUE']) or '5'

            try:
                sel = menus.gpus[gpu]
                system('pacman -S xorg-server xorg-apps xorg-xinit '
                       + 'xterm {0} --noconfirm'''.format(sel), True)
                break
            except KeyError:
                print_error("Invalid option")
                time.sleep(1)


def wm_de():
    logger.debug("Installing WM or DE")
    system("clear")

    if query_yes_no('> Would you like to install a Desktop Environment or '
                    + 'Window Manager?', 'yes'):
        while True:
            options = list(menus.wm_de.keys())
            options.sort()
            for k in options:
                print_info('{0}) {1}'.format(k, menus.wm_de[k]))

            choice = cinput("> Choice: ", COLORS['OKBLUE'])

            try:
                sel = menus.wm_de[choice]
                if sel == 'All':
                    choice = '123'

                username = usr_cfg['username']
                if '1' in choice:
                    system("pacman -S archstrike-openbox-config --noconfirm",
                           True)
                    if username:
                        system("mkdir -p /mnt/home/{0}/".format(username)
                               + ".config")
                        system("echo 'exec openbox-session' > "
                               + "/mnt/home/{0}/.xinitrc".format(username))
                        system('cp -a /mnt/usr/share/archstrike-openbox-config'
                               + '/etc/* /mnt/home/{0}/.config/'.format(username))
                        system('chown {0}:users -R /home/'.format(username)
                               + '{0}/.config '.format(username)
                               + '/home/{0}/.xinitrc'.format(username), True)
                    system("echo 'exec openbox-session' > /mnt/root/.xinitrc")
                    system("mkdir -p /mnt/root/.config")
                    system('cp -a /mnt/usr/share/archstrike-openbox-config'
                           + '/etc/*  /mnt/root/.config/''')

                if '2' in choice:
                    system("pacman -S xfce4 xfce4-goodies --noconfirm", True)
                    system("pacman -S archstrike-xfce-config --noconfirm", True)
                    if username:
                        system("mkdir -p /mnt/home/{0}/".format(username)
                               + ".config")
                        system("echo 'exec startxfce4' > "
                               + '/mnt/home/{0}/.xinitrc'.format(username))
                        system('cp -a /mnt/usr/share/archstrike-xfce-config/'
                               + 'config/* /mnt/home/{0}'.format(username)
                               + '/.config/')
                        system('chown {0}:users -R /home/{0}'.format(username)
                               + '/.config /home/'
                               + '{0}/.xinitrc'.format(username), True)
                    system("echo 'exec startxfce4' > /mnt/root/.xinitrc")
                    system("mkdir -p /mnt/root/.config")
                    system('cp -a /mnt/usr/share/archstrike-xfce-config'
                           + '/config/* /mnt/root/.config/')
                    system('cp -a /mnt/usr/share/archstrike-xfce-config'
                           + '/icons/* /mnt/usr/share/pixmaps/')
                    system('cp -a /mnt/usr/share/archstrike-xfce-config'
                           + '/wallpapers/* /mnt/usr/share/backgrounds/xfce/')

                if '3' in choice:
                    system("pacman -S archstrike-i3-config --noconfirm", True)
                    if username:
                        system("mkdir -p /mnt/home/{0}/".format(username)
                               + ".config")
                        system("echo 'exec i3' > "
                               + '/mnt/home/{0}/.xinitrc'.format(username))
                        system('cp -a /mnt/usr/share/archstrike-i3-config'
                               + '/config/* /mnt/home/{0}/'.format(username)
                               + '.config/')
                        system('cat /mnt/usr/share/archstrike-i3-config'
                               + '/Xresources >> /mnt/home/{0}/'.format(username)
                               + '.Xresources')
                        system('cp -a /mnt/usr/share/archstrike-i3-config'
                               + '/gtkrc-2.0 /mnt/home/{0}/'.format(username)
                               + '.gtkrc-2.0')
                        system('chown {0}:users -R /home/{0}'.format(username)
                               + '/.config '
                               + '/home/{0}/.xinitrc '.format(username)
                               + '/home/{0}/.Xresources '.format(username)
                               + '/home/{0}/.gtkrc-2.0'.format(username), True)
                    system("echo 'exec i3' > /mnt/root/.xinitrc")
                    system("mkdir -p /mnt/root/.config")
                    system('cp -a /mnt/usr/share/archstrike-i3-config'
                           + '/config/* /mnt/root/.config/')
                    system('cat /mnt/usr/share/archstrike-i3-config'
                           + '/Xresources >> /mnt/root/.Xresources')
                    system('cp -a /mnt/usr/share/archstrike-i3-config'
                           + '/gtkrc-2.0 /mnt/root/.gtkrc-2.0')

                if os.path.isdir('/home/archstrike/.config/terminator'):
                    if username:
                        system('cp -a /home/archstrike/.config/terminator '
                               + '/mnt/home/{0}/.config'.format(username))

                    system("cp -a /home/archstrike/.config/terminator "
                           + "/mnt/root/.config/")

                break
            except KeyError:
                print_error("Invalid option")
                time.sleep(1)


def login_manager():
    logger.debug("Install Login Manager")
    system("clear")

    if query_yes_no("> Would you like to install a login manager?", 'yes'):
        system("pacman -S lightdm lightdm-gtk-greeter --noconfirm", True)
        system("systemctl enable lightdm.service", True)


def additional_utils():
    logger.debug("Installing additional utils")
    system("clear")

    if query_yes_no("> Would you like to install virtualbox utils?", 'yes'):
        system('pacman -S virtualbox-guest-utils linux-headers mesa-libgl '
               + '--noconfirm', True)

    if query_yes_no("> Would you like to add touchpad support?", 'no'):
        system("pacman -S xf86-input-synaptics --noconfirm", True)

    if query_yes_no("> Would you like to add bluetooth support?", 'no'):
        system("pacman -S blueman --noconfirm", True)
