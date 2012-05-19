###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

# this constants tell what kind of peer is this one
New=   -1 # has not issued an active (see joining.txt) command yet
Normal= 0 # noone special
Succ=   1
Pred=   2

rootDirIno= 1

kilo= 1024
mega= kilo*kilo
giga= mega*kilo

# stat indexes
statIno=   0
statMode=  1
statSize=  2
statNlink= 3
statCtime= 4
statAtime= 5
statMtime= 6
statUid=   7
statGid=   8

# seek flags
seekAbsolute= 0
seekRelative= 1
seekEnd=      2

# file modes for dirs and symlinks
S_DIR=  0x4000
S_LINK= 0xa000
S_REG=  0x8000

# static ports
chalPort=  9182
umbiePort= 5647
vicePort= 10293
# 'alias'
navelPort= umbiePort

# timeouts
shoutTimeOut= 3
periodicTimeOut= 60
periodicUTimeOut= 5

# max number of inodes
# maxIno= 2147483648
maxIno= mega
pageSizeBits= 12
pageSize= 2**pageSizeBits
fragmentSizeBits= 12
fragmentSize= 2**fragmentSizeBits
