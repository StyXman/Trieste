SRCFILES=*.py Makefile .cvsignore
CHECKER=PYTHONVER=2.2 pychecker

all:
	make -C fuse

config:
	( cd fuse; ./conf )

ChangeLog: $(SRCFILES)
	cvs2cl -r -S --no-wrap -w --accum > /dev/null || cvs2cl -r -S --no-wrap -w

clean:
	make -C fuse clean
	rm -f *.pyo *.pyc *.log *~ *.html

really-clean: clean
	make -C fuse clean

test:
	$(CHECKER) -t -v -a --changetypes *.py 2>&1 | less -S

check: test

fullcheck:
	$(CHECKER) -t -9 -v -a -8 --changetypes *.py 2>&1 | less -S

dist:
	./setup.py sdist

install:
	( cd fuse; ./root.sh )

.PHONY: all config dist install 
