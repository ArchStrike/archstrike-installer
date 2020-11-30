from pathlib import Path
import logging
import time
from ...config import usr_cfg, get_logger, COLORS
from ...utils import print_error, print_warning, print_title, print_info,\
    cinput, query_yes_no, system, satisfy_dep


logger = get_logger(__name__)


def format_partition_type(i):
    print_warning("Partition {0} will be formatted now".format(i))
    partition_type = cinput('> Enter the partition type (linux, uefi, swap): ', COLORS['OKBLUE']).lower()
    logger.log(logging.INFO, 'Partition Type: {0}'.format(partition_type))
    if partition_type == 'linux':
        satisfy_dep("mkfs.ext4")
        usr_cfg['filesystem'] = 'ext4'
        system("mkfs.ext4 {0}".format(i))
    elif partition_type == 'uefi':
        satisfy_dep("mkfs.fat")
        system("mkfs.fat -F32 {0}".format(i))
    elif partition_type == 'swap':
        satisfy_dep("mkswap")  # mkswap and swapon have same owner
        system("mkswap {0}".format(i))
        system("swapon {0}".format(i))
    else:
        print_error("Invalid Option")
        time.sleep(1)
        format_partition_type(i)


def format_partition():
    system("clear")
    print_title("Step 5) Formatting partitions")
    time.sleep(1)

    system("lsblk {}".format(usr_cfg['drive']))
    _in_prompt = '> Enter all the partitions you created by seperating them with a comma (e.g. /dev/sda1,/dev/sda2): '
    user_input = ''
    partitions = None
    while not user_input:
        user_input = cinput(_in_prompt, COLORS['OKBLUE'])
        partitions = user_input.split(',')
        for p in partitions:
            if not Path(p).exists():
                logger.log(logging.ERROR, f"System Partition: {p} not found")
                user_input = ''

    logger.log(logging.INFO, "System Partitions: {0}".format(partitions))

    if query_yes_no("> Are you sure these are correct?", 'yes'):
        for i in partitions:
            format_partition_type(i)
    else:
        format_partition()

    usr_cfg['manual_partitions'] = partitions


def mount():
    system("clear")
    print_title("Step 6) Mounting the partitions")
    time.sleep(1)

    print_info('\n'.join(usr_cfg['manual_partitions']))
    usr_cfg['root'] = cinput('Which one is your / mounted partition? (e.g. /dev/sda1): ',
                             COLORS['OKBLUE'])

    logger.log(logging.INFO, "/ is {0}".format(usr_cfg['root']))
    if usr_cfg['root'] in usr_cfg['manual_partitions']:
        print_info("Mounting {0} on /mnt".format(usr_cfg['root']))
        system("mount {0} /mnt".format(usr_cfg['root']))
    else:
        mount()

    if usr_cfg['manual_partition_table'] == 'gpt':
        while usr_cfg.get('boot') not in usr_cfg['manual_partitions']:
            _in_prompt = 'Which one is your /boot mounted partition? (e.g. /dev/sda2): '
            usr_cfg['boot'] = cinput(_in_prompt, COLORS['OKBLUE'])
            if usr_cfg['boot'] in usr_cfg['manual_partitions']:
                print_info("Mounting {0} on /mnt/boot".format(usr_cfg['boot']))
                system("mkdir -p /mnt/boot")
                system("mount {0} /mnt/boot".format(usr_cfg['boot']))
            else:
                print_error(f"The partition {usr_cfg['boot']} is not in {usr_cfg['manual_partitions']}")
    else:
        system("mkdir -p /mnt/boot")
