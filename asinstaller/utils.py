from __future__ import print_function
import subprocess as sp
import logging
import urllib2
import select
import random
import json
import time
import sys
import os

import menus
from config import *

logger = setup_logger(__name__)

def print_error(msg):
    print('''{0}{1}{2}'''.format(COLORS['FAIL'], msg, COLORS['ENDC']))


def print_warning(msg):
    print('''{0}{1}{2}'''.format(COLORS['HEADER'], msg, COLORS['ENDC']))


def print_command(msg):
    print('''{0}{1}{2}'''.format(COLORS['OKBLUE'], msg, COLORS['ENDC']))


def print_title(msg):
    print('''{0}{1}{2}'''.format(COLORS['HEADER'], msg, COLORS['ENDC']))


def print_info(msg):
    print('''{0}{1}{2}'''.format(COLORS['OKGREEN'], msg, COLORS['ENDC']))


def print_banner():
    directory = 'banners'
    filename = '{0}/{1}'.format(directory, random.choice(os.listdir(directory)))
    with open(filename) as fr:
        print_title(fr.read())


def cinput(msg, color):
    return raw_input('''{1}{0}{2}'''.format(msg, color, COLORS['ENDC'])).strip()


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
        sys.stdout.write('{0}{1}{2}{3}'.format(COLORS['OKBLUE'], question,
                                               prompt, COLORS['ENDC']))
        choice = raw_input().lower()
        logger.log(logging.INFO, '{0} : {1}'.format(question, choice))
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            msg = "{0}Please respond with 'yes'".format(COLORS['FAIL']) \
            + " or 'no' (or 'y' or 'n').\n{0}".format(COLORS['ENDC'])
            sys.stdout.write(msg)


def signal_handler(signal, handler):
    # Write Config File
    with open(CONFIG_FILE, 'w') as fw:
        json.dump(usr_cfg, fw)

    sp.Popen("umount -R /mnt", stdout=FNULL, stderr=sp.STDOUT, shell=True)
    FNULL.close()
    print_info("\n\nGood Bye")
    sys.exit()


def system(command, chroot=False, **kwargs):  # noqa

    if chroot:
        command = "arch-chroot /mnt {0}".format(command)

    # don't log clear or encryption passwd
    if (command == 'clear' or
            command.find('printf') != -1 or
            command.find('passwd') != -1):
        return sp.call([command], shell=True)

    child = sp.Popen([command], stdout=sp.PIPE, stderr=sp.PIPE,
                     shell=True, **kwargs)

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


def start_screen():
    logger.debug("Start Screen")
    while True:
        system("clear")
        print_banner()

        # Print start menu
        options = menus.start.keys()
        options.sort()
        for k in options:
            print_info('{0}) {1}'.format(k, menus.start[k]))

        choice = cinput('> Enter the number of your choice: ', COLORS['OKBLUE'])
        if choice == "1":
            break
        elif choice == "99":
            print_info("Alright, see you later!")
            exit()
        else:
            print_error("Invalid Option")


def internet_enabled():
    logger.debug("Checking Internet Connection")
    try:
        request = urllib2.Request('https://archstrike.org/keyfile.asc')
        request.add_header('User-Agent', 'ArchStrike Installer')
        opener = urllib2.build_opener()
        keyfile = opener.open(request, timeout=5)
        with open('keyfile.asc', 'wb') as fw:
            fw.write(keyfile.read())

        return True
    except urllib2.URLError as err:
        pass
    return False


def check_uefi():
    logger.debug("Checking UEFI")
    try:
        os.listdir('/sys/firmware/efi/efivars')
        usr_cfg['uefi'] = True
    except OSError:
        usr_cfg['uefi'] = False  # Dir doesnt exist


def set_keymap():
    logger.debug("Set keymap")
    system("clear")
    print_title("Step 1) Keymap Setup")
    print_info("Setting your keyboard layout now, default is US.")

    layout = 'us'
    if query_yes_no("> Would you like to change the keyboard layout? ", 'no'):
        print(system_output("find /usr/share/X11/xkb/symbols -type f | "\
                            + "awk -F '/' '{print $NF}' | sort | uniq"""))
        layout = raw_input("> Enter your keyboard layout: ")

        if query_yes_no('>Setting "{0}" as your keymap, '.format(layout) \
                        + 'is that correct? ', 'yes'):
            system("setxkbmap {0}".format(layout))


        if query_yes_no('> Try typing in here to test. \n'\
                        + "Input 'Y' if settings are incorrect"
                        + " and 'N' to save.:", 'no'):
            system("setfont lat9w-16")
    usr_cfg['keymap'] = layout
