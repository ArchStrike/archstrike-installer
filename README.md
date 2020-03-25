# archstrike-installer
Full ArchStrike Installer for ArchStrike ISO

## Maintenance
For testing purposes, one may wish to use RAM disk to speed up the process.
```
modprobe brd rd_size=18874368
fdisk -l
```
To remove `/dev/ram0`, run `umount /dev/ram0; modprobe -r brd`.
