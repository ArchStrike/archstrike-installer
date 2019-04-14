from __future__ import absolute_import, print_function
import json
import functools
import logging
import os
import random
import re
import subprocess as sp
import sys
import urllib2
import urllib
from threading import Thread, Lock
# installer modules
from . import menus
from .config import COLORS, setup_logger, CONFIG_FILE, usr_cfg, FNULL


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
    response = raw_input('''{1}{0}{2}'''.format(msg, color, COLORS['ENDC'])).strip()
    logger.debug('prompt: {}\n{}response: {}'.format(msg, ' ' * 8, response))
    return response


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
        # logger.log(logging.INFO, '{0} : {1}'.format(question, choice))
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            msg = "{0}Please respond with 'yes'".format(COLORS['FAIL']) \
                + " or 'no' (or 'y' or 'n').\n{0}".format(COLORS['ENDC'])
            sys.stdout.write(msg)


def save_crash_files(userid, filenames):
    urls = []
    for filename in filenames:
        data = urllib.urlencode({
            'poster': userid,
            'expire_days': 31,
            'content': open(filename).read()
        })
        request = urllib2.urlopen('http://dpaste.com/api/v2/', data)
        content = request.read().rstrip() + '.txt'
        urls.append(content)
    return urls


# Somehow recover from this
def signal_handler(signal, handler):

    # This will be caught in the main file
    raise RuntimeError('Captured CTRL+C')

    # Everything Below will not get executed

    # Write Config File
    with open(CONFIG_FILE, 'w') as fw:
        json.dump(usr_cfg, fw)

    sp.Popen("umount -R /mnt", stdout=FNULL, stderr=sp.STDOUT, shell=True)
    FNULL.close()
    print_info("\n\nGood Bye")
    sys.exit()


write_lock = Lock()


def _write(log, color, line):
    write_lock.acquire()
    print('{0}'.format(COLORS[color]), end='')
    log(line.strip())
    print('{0}'.format(COLORS['ENDC']), end='')
    write_lock.release()


def _read(write, pipe):
    for line in iter(pipe.readline, b''):
        if line:
            write(line)
    pipe.close()


def system(command, chroot=False, **kwargs):  # noqa
    if chroot:
        command = "arch-chroot /mnt {0}".format(command)

    # don't log clear or encryption passwd
    if command == 'clear' or command.find('printf') != -1 or command.find('passwd') != -1:
        return sp.call([command], shell=True)

    child = sp.Popen([command], stdout=sp.PIPE, stderr=sp.PIPE, close_fds=True, shell=True, **kwargs)
    # Process output from command
    write_out = functools.partial(_write, logger.info, 'BOLD')
    write_err = functools.partial(_write, logger.error, 'FAIL')
    stdout_thread = Thread(target=_read, args=(write_out, child.stdout))
    stderr_thread = Thread(target=_read, args=(write_err, child.stderr))
    for t in (stdout_thread, stderr_thread):
        t.daemon = True
        t.start()
    child.wait()
    [t.join() for t in (stdout_thread, stderr_thread)]  # make sure the output is done writing
    ret = child.returncode

    print()
    if ret != 0:
        raise Exception("Exit code {} for command: {}".format(ret, command))
    return ret


def system_output(command):
    print('{0}'.format(COLORS['BOLD']), end='')
    ret = sp.check_output([command], close_fds=True, shell=True).rstrip()
    print('{0}'.format(COLORS['ENDC']), end='')

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
            sys.exit()
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

    except Exception:
        print_warning("No Internet Connection Detected.")
        if query_yes_no("> Would you like to connect to WiFi?", "yes"):
            try:
                system_output("wifi-menu")
                python = sys.executable
                os.execl(python, python, *sys.argv)
            except Exception as e:
                system("clear")
                logger.error("WIFI: {0}".format(e))
            return internet_enabled()
        else:
            return False
    return True


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
        print(system_output("find /usr/share/X11/xkb/symbols -type f | "
                            + "awk -F '/' '{print $NF}' | sort | uniq"""))
        layout = raw_input("> Enter your keyboard layout: ")

        if query_yes_no('>Setting "{0}" as your keymap, '.format(layout)
                        + 'is that correct? ', 'yes'):
            system("setxkbmap {0}".format(layout))

        if query_yes_no('> Try typing in here to test. \n'
                        + "Input 'Y' if settings are incorrect"
                        + " and 'N' to save.:", 'no'):
            system("setfont lat9w-16")
    usr_cfg['keymap'] = layout


def _pacman_fs_re():
    repos = ['testing', 'core', 'extra', 'community-testing', 'community', 'multilib-testing', 'multilib',
             'archstrike', 'archstrike-testing']
    return re.compile(r'^(?:{})/(?P<pkgname>[^\s]+) '.format('|'.join(repos)), re.M)


PAC_FS_RE = _pacman_fs_re()


def satisfy_dep(command):
    output = system_output('pacman -Fs {}'.format(command))
    match = PAC_FS_RE.search(output)
    pkg = match.group('pkgname') if match else None
    if pkg:
        sys_cmd = "command -v {} > /dev/null || pacman -S --noconfirm {}"
        system(sys_cmd.format(command, pkg))
    else:
        logger.warning('Failed to locate "{}" owning package'.format(command))
