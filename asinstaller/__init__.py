import signal
import json
from subprocess import Popen, STDOUT
from sys import exit
from .config import COLORS, CONFIG_FILE, FNULL, LOG_FILE, get_logger, init_logger_handles, usr_cfg
from .utils import Crash, check_uefi, internet_enabled, pacman_exists, print_error, print_info, query_yes_no, \
    save_crash_files, set_keymap, signal_handler, start_screen, system
from .partitions import devices, auto, manual
from os import geteuid
from . import install
from .irc import LogHandler


__version__ = '2.3.0'


def main():
    try:
        init_logger_handles()
        logger = get_logger(__name__)
        logger.debug(f'Version: {__version__}')
        # Pre-checks
        if not pacman_exists():
            print_error("Please install pacman")
            exit()
        if geteuid() != 0:
            print_error("Please run as root")
            exit()
        if not internet_enabled():
            print_error("You need an active Internet connection")
            exit()

        # TODO: If there is a cfg then the user has prev ran the installer
        if usr_cfg:
            pass  # Goto Menu

        # First time, ask the user if they want to proceed
        start_screen()

        # Let the installation begin
        logger.debug("Starting Installation")
        # Let the installation begin
        logger.debug("Starting Installation")

        check_uefi()
        system("timedatectl set-ntp true")

        set_keymap()

        devices.partition_menu()

        confirmed = True if usr_cfg['partition_type'] == '3' else False
        devices.identify()
        while not confirmed:

            devices.set_filesystem()

            devices.set_swap()

            devices.set_gpt()

            confirmed = devices.confirm_settings()

        if usr_cfg['partition_type'] in ['1', '2']:
            devices.check_lvm()
            auto.partition()
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
    except RuntimeError as e:
        # User-input prompted exit
        logger.exception('{0}{1}{2}'.format(COLORS['FAIL'], e, COLORS['ENDC']))
    except Exception as e:
        # Crash occurred prompted exit
        logger.exception('{0}{1}{2}'.format(COLORS['FAIL'], e, COLORS['ENDC']))
        # Write config file
        with open(CONFIG_FILE, 'w') as fw:
            json.dump(usr_cfg, fw)
        # Ask to report crash
        print_error('An error has occured, see /tmp/archstrike-installer.log for details.')
        report_yn = query_yes_no("> Would you like to send a crash report?", 'yes')
        crash = Crash(__version__)
        # only send when there is something new
        info_msg = "\n\nYour Report has successfully been submitted. "
        info_msg += "Your unique ID is {0}. Use this as a "
        info_msg += "reference when asking admins for assistance."
        if report_yn:
            if not crash.duplicate:
                info_msg = info_msg.format(crash.submission_id)
                log_files = [CONFIG_FILE, LOG_FILE]
                LogHandler(crash.submission_id, save_crash_files(crash.submission_id, log_files))
                crash.log_as_reported()
            else:
                info_msg = info_msg.format(crash.submission_id)
            print_info(info_msg)
    finally:
        # Cleanup stuff
        Popen("umount -R /mnt", stdout=FNULL, stderr=STDOUT, shell=True)
        FNULL.close()


signal.signal(signal.SIGINT, signal_handler)
