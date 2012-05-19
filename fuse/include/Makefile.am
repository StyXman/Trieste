## Process this file with automake to produce Makefile.in

SUBDIRS = linux

include_HEADERS = fuse.h consts.h

all-local: consts.h

consts.h: ../../Trieste/common/consts.py mkconsts.py
	PYTHONPATH=../../ ./mkconsts.py
