#
#    Copyright (C) 2001  Jeff Epler  <jepler@unpythonic.dhs.org>
#                  2004  Marcos DIone <mdione@grulic.org.ar>
#
#    This program can be distributed under the terms of the GNU GPL.
#    See the file COPYING.
#

from _fuse import main, DEBUG
import os
from errno import *

from Trieste.common.utils import debugPrint

class ErrnoWrapper:
  def __init__(self, func, name):
    self.func = func
    self.name= name

  def __call__(self, *args, **kw):
    try:
      ans= apply(self.func, args, kw)
      return ans
    except (IOError, OSError), detail:
      # Sometimes this is an int, sometimes an instance...
      if hasattr(detail, "errno"):
        detail = detail.errno
      return -detail

class Fuse:
  _attrs = ['getattr', 'readlink', 'getdir', 'mknod', 'mkdir',
      'unlink', 'rmdir', 'symlink', 'rename', 'link', 'chmod',
      'chown', 'truncate', 'utime', 'open', 'read', 'write',
      'lookup', 'statfs', 'setattr',
      ]

  flags = 0
  multithreaded = 0
  def main(self):
    d = {'flags': self.flags}
    d['multithreaded'] = self.multithreaded
    print 'adding',
    for a in self._attrs:
      if hasattr(self,a):
        print ' %s,' % a,
        d[a] = ErrnoWrapper(getattr(self, a), a)
    print
    apply (main, (), d)
