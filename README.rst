This is Trieste, a Distributed File System. This project was developed as the 
Capstone Project for my Masters degree in Computer Science. Here's the abstract
of the resulting report:

Most network installations use centralized network filesystems, and some even use
peer-to-peer ones. Centralized filesystems don't use the resources in the client
machines, and peer-to-peer ones are not transparent enough and are not easy to
administrate. We designed and implemented a fault-tolerant, easy to administrate
distributed filesystem, which can add storage space easily. Trieste showed to be greatly
scalable, using disk bandwidth and space of each added computer. Its features makes it
suitable for clusters.

Here are some bare instrunctions on how to compile it:

* decompress (I think you already did that).
* edit ``fuse/conf``. modify the ``--prefix`` and ``--with-kernel`` options to your needs.
* $ ``make config``  # (this runs a configure script under the fuse dir).
* $ ``make``
* # ``make install``  # (run as root. installs the kernel and sets some permissions)

If you're running some debians and ubuintus (I think they' re sid and breezy),
that last command might fail miserably. try:

* ``make CC=gcc-3.3``

or any other gcc you might have installed (gcc-3.4 and gcc-4.0 seem to be the
problematic ones).

Unluckily, it runs only against linux-kernel-2.4. I' ll try to fix that ASAP. To
run this beast:

* edit ``config.sh``
* $ ``./run.sh <n>``

where n is the amount of storage namagers you want.

* $ ``PYTHONPATH=. ./utils/mkfs.py``

formats the root dir. now it's ready for mounting.

* $ ``./fuse/util/fusermount -c <mntpt> ./virtue.py -b <netaddr>``

where <mntpt> is the mount point and <netaddr> is the network address; or

* $ ``./fuse/util/fusermount -c <mntpt> ./virtue.py -c umbie://localhost:5647/``

Now you can enter into <mntpt> and do whatever you do with a filesystem!

Some things are not tested yet, but the `b' part does not refers to `beta´. This
is sill **alpha**.

Any questions, send mails to Marcos Dione <mdione@grulic.org.ar> at will.
