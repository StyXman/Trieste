#! /bin/bash

# set -xe;

# Makefile:kmoduledir = /lib/modules/2.4.22
KDIR=`awk '/kmoduledir/ {print $3}' Makefile`;

# copy kernel module
mkdir -vp $KDIR/kernel/fs/fuse;
cp -v kernel/fuse.o $KDIR/kernel/fs/fuse;
depmod -ae;

# set perms to fusermount
chown -v root util/fusermount;
chmod -v u+s util/fusermount;
