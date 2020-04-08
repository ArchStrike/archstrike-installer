# archstrike-installer
Full ArchStrike Installer for ArchStrike ISO

## Maintenance
For testing purposes, one may wish to use RAM disk to speed up the process.
```
# modprobe brd rd_size=18874368
```
To verify the previous command resulted in new devices, run `fdisk -l` as root.
When done, resources could be manually cleaned up by unmounting any residual RAM disk devices and removing `brd` with `modprobe`.
