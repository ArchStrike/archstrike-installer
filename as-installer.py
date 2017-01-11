#!/usr/bin/env python2
import json
from os import geteuid
from sys import exit

from asinstaller import *

logger = setup_logger(__name__)

def main():
    try:
        # Pre-checks
        if geteuid() != 0:
            print_error("Please run as root")
            exit()
        if not internet_enabled():
            print_error("You need an active Internet connection")
            exit()

        # TODO: If there is a cfg then the user has prev ran the installer
        if usr_cfg:
            pass # Goto Menu

        # First time, ask the user if they want to proceed
        start_screen()

        # Let the installation begin
        logger.debug("Starting Installation")

        check_uefi()
        system("timedatectl set-ntp true")

        set_keymap()

        devices.partition_menu()

        confirmed = True if usr_cfg['partition_type'] == '3' else False
        while not confirmed:
            devices.identify()

            devices.set_filesystem()

            devices.set_swap()

            devices.set_gpt()

            confirmed = devices.confirm_settings()

        if usr_cfg['partition_type'] == '1':
            devices.check_lvm()
            auto.partition()
        elif usr_cfg['partition_type'] == '2':
            devices.check_lvm()
            encrypted.partition()
        else:
            manual.partition()

        # Install Base
        install.base()
        # Genfstab
        install.genfstab()
        # locale and time
        install.locale_time()
        # initramfs
        install.initramfs()
        # Bootloader
        install.grub()
        # configurations
        install.configuration()
        # Set hostname
        install.hostname()
        # Setup Internet
        install.internet()
        # Set Password
        install.root_passwd()
        # Install AS
        install.archstrike()
        # Add user
        install.new_user()
        # Setup Video
        install.video_utils()
        # Setup DE/WM
        install.wm_de()
        # Steup Login Manager
        install.login_manager()
        # Additional Utils (virtualbox, bluetooth, touchpad)
        install.additional_utils()

        # Finalize
        system("clear")
        print_info("Your system is set up. Thanks for installing ArchStrike!")
        system("umount -R /mnt")
        if query_yes_no("> Would you like to reboot now?", None):
            system("reboot")

    except Exception as e:
        logger.error('{0}{1}{2}'.format(COLORS['FAIL'], e, COLORS['ENDC']))

        # Write Config File
        with open(CONFIG_FILE, 'w') as fw:
            json.dump(usr_cfg, fw)

        # Cleanup stuff
        sp.Popen("umount -R /mnt", stdout=FNULL, stderr=sp.STDOUT,shell=True)
        FNULL.close()

        print_error('An error has occured, see ' \
            + '/tmp/archstrike-installer.log for details.')
    finally:
        if query_yes_no("> Would you like to send a crash report?", 'yes'):
            unique_id = os.urandom(16).encode('hex')
            submit_crash_report(unique_id)
            print_info("\n\nYour Report has successfully been submitted." \
                + "Your unique ID is {0}. Use this as a ".format(unique_id) \
                + "reference when asking admins for assistance.")


if __name__ == '__main__':
    main()
