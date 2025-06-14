# Tools for GLFS v0 image creation/editing
_**g**ood **l**ittle **f**ile **s**ystem, version 0_

(affectionately _**g**ood **l**uck **f**ile **s**ystem, version 0_)

## Tools

| **Command** | **Purpose**                                          |
| ----------- | ---------------------------------------------------- |
| `glfs-mkfs` | create a new empty GLFS image                        |
| `glfs-add`  | add a file from your system into the GLFS image      |
| `glfs-cat`  | extract a file from the GLFS image to your system    |
| `glfs-ls`   | list all files in the GLFS image                     |



## Quickstart

Create a new GLFS image:
```
glfs-mkfs <disk image name>
```

Add a file:
```
glfs-add <disk image name> <file to add> <filename to use on disk>
```

Extract a file:
```
glfs-cat <disk image name> <file on disk> <file to write to>
```

List all files:
```
glfs-ls <disk image name>
```


## What is GLFS?

GLFS (Good Little File System (affectionately, Good Luck File System)) is an extremeley rudimentary sector-based file system.

- 512-byte sectors
- files stored contiguously
- no fancy metadata, no journals -- just a directory table and files after that
- designed for low-complexity systems (not with security in mind)


## License
0. Use responsibly.
Refer LICENSE for further terms.