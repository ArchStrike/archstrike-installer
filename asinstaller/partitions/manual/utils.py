import time
from asinstaller.utils import *
from asinstaller.config import usr_cfg, setup_logger

logger = setup_logger(__name__)

def format_partition():
    system("clear")
    print_title("Step 5) Formatting partitions")
    time.sleep(1)

    system("lsblk %s".format(usr_cfg['drive']))
    partitions = cinput('> Enter all the partitions you created by ' \
        + 'seperating them with a comma (e.g. /dev/sda1,/dev/sda2): ' \
        , COLORS['OKBLUE']).split(',')

    logger.log(logging.INFO, "System Partitions: {0}".format(partitions))

    if query_yes_no("> Are you sure these are correct?", 'yes'):
        for i in partitions:
            print_warning("Partition {0} will be formatted now".format(i))
            partition_type = cinput('> Enter the partition type ' \
                + '(linux, uefi, swap): ', COLORS['OKBLUE']).lower()
            logger.log(logging.INFO, 'Partition Type: ' \
                + '{0}'.format(partition_type))
            if partition_type == 'linux':
                system("mkfs.ext4 {0}".format(i))
            elif partition_type == 'uefi':
                system("mkfs.fat -F32 {0}".format(i))
            elif partition_type == 'swap':
                system("mkswap {0}".format(i))
                system("swapon {0}".format(i))
            else:
                print_error("Invalid Option")
                time.sleep(1)
                format_partition()
    else:
        format_partition()

    usr_cfg['manual_partitions'] = partitions

def mount():
    system("clear")
    print_title("Step 6) Mounting the partitions")
    time.sleep(1)

    print_info('\n'.join(usr_cfg['manual_partitions']))
    root = cinput('Which one is your / mounted partition? (e.g. /dev/sda1): ',
            COLORS['OKBLUE'])
    logger.log(logging.INFO, "/ is {0}".format(root))
    if root in usr_cfg['manual_partitions']:
        print_info("Mounting {0} on /mnt".format(usr_cfg['root']))
        system("mount {0} /mnt".format(usr_cfg['root']))
    else:
        mount()

    if usr_cfg['manual_partition_table'] == 'gpt':
        boot = cinput('Which one is your /boot mounted partition? ' \
            + '(e.g. /dev/sda2): ', COLORS['OKBLUE'])
        logger.log(logging.INFO, "/boot is {0}".format(boot))
        if boot in partitions:
            print_info("Mounting {0} on /mnt/boot".format(usr_cfg['boot']))
            system("mkdir -p /mnt/boot")
            system("mount {0} /mnt/boot".format(usr_cfg['boot']))
        else:
            mount()
    else:
        system("mkdir -p /mnt/boot")
