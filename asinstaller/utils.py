import json
import functools
import logging # noqa
import os
import random
import re
import subprocess as sp
import sys
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from threading import Thread, Lock
# installer modules
from . import menus
from .config import COLORS, get_logger, CONFIG_FILE, usr_cfg, FNULL, CRASH_FILE


logger = get_logger(__name__)


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
    banner = ['',
              '                        _      _____ _        _ _',
              '         /\\            | |    / ____| |      (_) |',
              '        /  \\   _ __ ___| |__ | (___ | |_ _ __ _| | _____',
              "       / /\\ \\ | '__/ __| '_ \\ \\___ \\| __| '__| | |/ / _ \\",
              '      / ____ \\| | | (__| | | |____) | |_| |  | |   <  __/',
              '     /_/    \\_\\_|  \\___|_| |_|_____/ \\__|_|  |_|_|\\_\\___|',
              '']
    print_title('\n'.join(banner))


def cinput(msg, color):
    response = input('''{1}{0}{2}'''.format(msg, color, COLORS['ENDC'])).strip()
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
        choice = cinput('{0}{1}'.format(question, prompt), COLORS['OKBLUE'])
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
        with open(filename) as fhandle:
            content = fhandle.read()
        data = urllib.parse.urlencode({
            'poster': userid,
            'expire_days': 31,
            'content': content
        })
        request = urllib.request.urlopen('http://dpaste.com/api/v2/', data.encode())
        content = request.read().rstrip() + b'.txt'
        urls.append(content.decode())
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
    log(line.decode().strip())
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


def system_or_exit(command, chroot=False, **kwargs):
    try:
        return system(command, chroot=False, **kwargs)
    except Exception:
        logger.exception("An host environment issue occurred")
        print_info("\n\nGood Bye")
        sys.exit()


def system_output(command):
    try:
        print('{0}'.format(COLORS['BOLD']), end='')
        ret = None
        ret = sp.check_output([command], stderr=sp.STDOUT, close_fds=True, shell=True).decode().rstrip()
    except sp.CalledProcessError as err:
        print(err.output.decode())
        raise
    finally:
        print('{0}'.format(COLORS['ENDC']), end='')
        return ret


def start_screen():
    logger.debug("Start Screen")
    while True:
        system("clear")
        print_banner()

        # Print start menu
        options = list(menus.start.keys())
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
        request = urllib.request.Request('https://archstrike.org/keyfile.asc')
        request.add_header('User-Agent', 'ArchStrike Installer')
        opener = urllib.request.build_opener()
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


def is_arch_linux():
    try:
        logger.debug(f"Checking that os release is Arch Linux")
        os_release_path = Path("/etc/os-release")
        with os_release_path.open() as fhandle:
            fcontent = fhandle.read()
        return 'Arch Linux' in fcontent
    except Exception:
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
        print(system_output("find /usr/share/X11/xkb/symbols -type f | awk -F '/' '{print $NF}' | sort | uniq"""))
        layout = input("> Enter your keyboard layout: ")

        if query_yes_no(f'>Setting "{layout}" as your keymap, is that correct? ', 'yes'):
            satisfy_dep("setxkbmap")
            system("setxkbmap {0}".format(layout))

        font_prompt = '> Try typing in here to test. \nInput \'Y\' if settings are incorrect and \'N\' to save.:'
        if query_yes_no(font_prompt, 'no'):
            system("setfont lat9w-16")
    usr_cfg['keymap'] = layout


def _pacman_fy_re():
    repos = ['testing', 'core', 'extra', 'community-testing', 'community', 'multilib-testing', 'multilib', 'archstrike']
    return re.compile(r'^(?:{})/(?P<pkgname>[^\s]+) '.format('|'.join(repos)), re.M)


PAC_FY_RE = _pacman_fy_re()


def satisfy_dep(command):
    output = system_output('pacman -Fy {}'.format(command))
    match = PAC_FY_RE.search(output)
    if match:
        pkg = match.group('pkgname')
        system_or_exit(f"command -v {command} > /dev/null || pacman -Sy --noconfirm {pkg}")
    else:
        raise Exception(f'Failed to locate "{command}" owning package')


class Crash(object):  # TODO: consider caching submission_id per host, since it is used as irc user
    """Creates a crash object from state and checks previous crash to deduplicate submissions"""
    def __init__(self, version=None, skip_deduplication=False):
        self.formatter = '{}:{}:version-{}'
        self.submission_id = 'as' + os.urandom(14).hex()
        self.affected_version = version
        self.xs_trace = None
        self.duplicate = False
        self.set_xs_trace()
        if skip_deduplication is False:
            self.deduplicate()

    def __bool__(self):
        return self.xs_trace == f'{None}:{None}:version-{None}'

    def __eq__(self, other_crash):
        return self.xs_trace == other_crash

    def __str__(self):
        return f'{self.xs_trace}@{self.submission_id}'

    def parse_exc_info(self):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        if exc_type is None or exc_tb is None:
            return None, None
        else:
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[-1]
            filename = filename.replace('.py', '')
            lineno = exc_tb.tb_lineno
            return filename, lineno

    def set_xs_trace(self):
        try:
            filename, lineno = self.parse_exc_info()
            self.xs_trace = self.formatter.format(filename, lineno, self.affected_version)
        except Exception:
            logger.exception("Failed to set xs_trace")

    @staticmethod
    def from_crash_file():
        if not os.path.exists(CRASH_FILE):
            return
        with open(CRASH_FILE) as fhandle:
            previous_crash = fhandle.read()
        # if the crash is the same as already reported, re-use hexid
        crash = Crash(skip_deduplication=True)
        crash.xs_trace, crash.submission_id = previous_crash.split('@')
        return crash

    def log_as_reported(self):
        """call to cache exceptions to CRASH_FILE which will be used in deduplication"""
        with open(CRASH_FILE, 'w') as fhandle:
            fhandle.write(self.__str__())

    def deduplicate(self):
        """when previous crash exists, check if trace is the same to de-duplicate"""
        try:
            previous_crash = Crash.from_crash_file()
            if isinstance(previous_crash, Crash) and self == previous_crash:
                self.duplicate = True
                self.submission_id = previous_crash.submission_id
        except Exception:
            logger.exception("Failed to decipher crash history...")
