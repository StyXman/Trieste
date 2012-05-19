MNTDIR=mnt
QUIET=0

all: _fusemodule.so fuseconsts.py

_fusemodule.so: _fusemodule.c ../lib/libfuse.a
	gcc -g3 -I/usr/include/python2.3 -I../include -L../lib _fusemodule.c -Wl,-shared -o _fusemodule.so -Wimplicit -lfuse && python2.3 -c 'import _fuse'

mkfuseconsts.o: mkfuseconsts.c ../include/linux/fuse.h
	gcc -c -Wall -g3 -I../include -o mkfuseconsts.o mkfuseconsts.c

mkfuseconsts: mkfuseconsts.o
	gcc -o mkfuseconsts mkfuseconsts.o

fuseconsts.py: mkfuseconsts
	./mkfuseconsts > fuseconsts.py

clean:
	rm -f _fusemodule.so *.pyc *.pyo mkfuseconsts.o mkfuseconsts

check: all
	PYTHONPATH=../.. pychecker -t -9 -v -a -8 --changetypes virtue.py

mount: all
# 	home
# 	PYTHONPATH=../.. ../util/fusermount -c ${MNTDIR} ./virtue.py -c umbie://192.168.0.5:5647/ -l mount.log
# 	fvl
	PYTHONPATH=../.. ../util/fusermount -c ${MNTDIR} ./virtue.py -c umbie://tempest.fsl.org.ar:5647/ -l mount.log > _mount.log 2>&1

umount:
	sudo umount ${MNTDIR}

test: dd bonnie

benchmark: bm

bm: bonnie kernel

dd:
	dd bs=4096 count=4096 < /dev/zero > mnt/test

bonnie:
	date
	time /home/mdione/local/sbin/bonnie++ -d mnt -n 4 -r 8 -s 16 -f > bonnie-$(shell hostname).log 2>&1

ubonnie:
	date
	time /home/mdione/local/sbin/bonnie++ -d mnt -n 1 -r 2 -s 4 -f > bonnie-$(shell hostname).log 2>&1

Mbonnie:
	date
	time /home/mdione/local/sbin/bonnie++ -d /localNFSScratch/Trieste -r 128 -s 256 -f > bonnie-$(shell hostname).log 2>&1

kernel: kernel1 kernel2 kernel3 kernel4

kernel1:
	date
	( \
	  mkdir -p mnt/$(shell hostname); \
	  cd mnt/$(shell hostname); \
	  time tar xjvf /home/mdione/src/linux-2.0.40.tar.bz2; \
	) > /dev/null 2>kernel1-$(shell hostname).log

kernel2:
	date
	( \
	  cd mnt/$(shell hostname); \
	  cp /home/mdione/src/config-2.0.40 linux-2.0.40/.config; \
	  cd linux-2.0.40; \
	  time make oldconfig dep bzImage; \
	) > /dev/null 2>kernel2-$(shell hostname).log

kernel3:
	date
	( \
	  cd mnt/$(shell hostname); \
	  cd linux-2.0.40; \
	  time make modules; \
	) > /dev/null 2>kernel3-$(shell hostname).log

kernel4:
	date
	( \
	  cd mnt/$(shell hostname); \
	  time rm -rf linux-2.0.40; \
	) > /dev/null 2>kernel4.log

touch:
	find mnt -print0 | xargs -0 touch;

apache:
	date
	( \
	    mkdir -p mnt/$(shell hostname); \
	    cd mnt/$(shell hostname); \
	    time tar xzvf /home/mdione/src/httpd-2.0.49.tar.gz; \
	    cp /home/mdione/src/httpd-2.0.49/conf httpd-2.0.49; \
	    cd httpd-2.0.49; \
	    time ./conf; \
	    time make; \
	) > /dev/null 2>apache-$(shell hostname).log

barrow:
	( \
	    cd mnt; \
	    time /home/mdione/src/facultad/Tesis/Trieste/tests/barrow 100 200 4; \
	) > barrow-$(shell hostname).log 2>&1

nfsbarrow:
	( \
	    cd /localNFSScratch; \
	    time /home/mdione/src/facultad/Tesis/Trieste/tests/barrow 100 200 4; \
	) > barrow-$(shell hostname).log 2>&1

distclean:
	
