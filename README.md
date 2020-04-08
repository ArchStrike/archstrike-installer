# archstrike-installer
Full ArchStrike Installer for ArchStrike ISO

## Maintenance
For testing purposes, one may wish to use RAM disk to speed up the process.
```
# modprobe brd rd_size=25165824
```
To verify the previous command resulted in new devices, run `fdisk -l` as root. 
```
$ sudo bash -c 'PYTHONPATH=.:$PYTHONPATH ./bin/archstrike-installer'
```
