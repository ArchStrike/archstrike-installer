
import sys
import time
from .utils import format_partition, mount
from ...utils import *
from ...config import usr_cfg, get_logger


logger = get_logger(__name__)


def partition():
    system('clear')
    print_title("Step 4) Manual Partititon (careful in this step)")
    time.sleep(1)

    confirm_drive = cinput('> Please confirm the drive by typing ' \
        + '{0}: '.format(usr_cfg['drive']), COLORS['OKBLUE'])
    if confirm_drive != usr_cfg['drive']:
        print_error("Mismatch in drives. Try again.")
        partition()
    system("lsblk {0}".format(usr_cfg['drive']))

    _table_cmd = "fdisk -l {0} | grep Disklabel | cut -d ' ' -f 3"
    partition_table = system_output(_table_cmd.format(usr_cfg['drive']))

    if partition_table == 'gpt':
        print_info("For the GPT partition table, the suggested partition " \
            + "scheme looks likethis:\nmountpoint        partition        " \
            + "partition type            boot flagsuggested size\n_________" \
            + "____________________________________________________________" \
            + "____________________\n/boot              /dev/sdx1        EFI" \
            + " System Partition      Yes     260-512 MiB\n\n[SWAP]         " \
            + "    /dev/sdx2        Linux swap                No      More " \
            + "than 512 MiB\n\n/                  /dev/sdx3        Linux " \
            + "(ext4)              No      Remainder of the device\n\nWARNING" \
            + ": If dual-booting with an existing installation of Windows on " \
            + "a UEFI/GPT system,\navoid reformatting the UEFI partition, as " \
            + "this includes the Windows .efifile required to boot it.")
    elif partition_table == 'dos':
        print_info("For the MBR partition table, the suggested partition " \
            + "scheme looks like this:\nmountpoint        partition        " \
            + "partition type            boot flag suggested size\n__________" \
            + "______________________________________________________________" \
            + "_________________\n[SWAP]            /dev/sdx1        Linux " \
            + "swap                No        More than 512 MiB\n\n/          " \
            + "       /dev/sdx2        Linux (ext4)              Yes       " \
            + "Remainder of the device")

    usr_cfg['manual_partition_table'] = partition_table

    if query_yes_no('''> I've read this and wish to continue to the partitioner.''', 'yes'):
        sp.call("clear", shell=True)
        sp.call('cfdisk {0}'.format(usr_cfg['drive']), shell=True)
        sp.call("clear", shell=True)
        sp.call('lsblk {0}'.format(usr_cfg['drive']), shell=True)
        if not query_yes_no('''> Are you sure your partitions are set up correctly?''', 'yes'):
            partition()
    else:
        sys.exit()

    format_partition()
    mount()
