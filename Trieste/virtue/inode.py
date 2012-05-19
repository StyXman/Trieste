###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from errno import EIO
import sys
from traceback import print_exception

from Trieste.common.utils import UmbDead
from Trieste.common.object import Object
from Trieste.common import consts

def trackermethod (method):
  # TODO: add tracking capabilities
  def closure (self, *args, **kwargs):
    ans= -EIO
    vice= self.vice ()
    if vice:
      kwargs['vice']= vice
      try:
        ans= method (self, *args, **kwargs)
      # except UmbError:
      except UmbDead:
        # also forget the vice (not implemented)
        self._vice= None
      except:
        (e, v, tb)= sys.exc_info ()
        self.debug (5, 'exception %s caught with this args: %s, %s' % (e, args, kwargs))
        print_exception (e, v, tb)
    else:
      self.debug (1, 'no vice for %d' % self.ino)
    return ans
  return closure

class Inode (Object):
  def __init__ (self, ino, master, parent=None, vice=None, policy=None):
    """
      mb only a ring is needed
    """
    Object.__init__ (self)
    self.policy= policy
    self.ino= ino
    self.master= master
    self._vice= vice
    if not parent:
      self.parent= self
    else:
      self.parent= parent

  def __str__ (self):
    return "Inode #%d" % self.ino

  #######
  # misc
  #######
  def vice (self):
    if not self._vice or self.policy.migrates:
      self.debug (5, 'getvice')
      vices= self.master._ring.vicesForIno (self.ino)
      if len (vices)>0:
        self._vice= vices[0]
      self.debug (5, 'ecivteg')
    return self._vice

  def destroy (self, vice=None):
    return vice.delinode (self.ino)
  destroy= trackermethod (destroy)

  #####
  # sb
  #####
  def stat (self, stat=None, vice=None):
    stat= vice.stat (self.ino, stat)
    # HACK; FIX
    if stat[0] is None:
      stat= stat[1]
    return stat
  stat= trackermethod (stat)

  def setattr (self, attr, vice=None):
    stat= vice.setattr (self.ino, attr)
    self.debug (3, 'setattr: %s' % str (stat))
    if stat[0] is None:
      stat= stat[1]
    return stat
  setattr= trackermethod (setattr)

  #######
  # file
  #######
  def read (self, off=0, size=None, vice=None):
    return vice.read (self.ino, off, size)
  read= trackermethod (read)

  def write (self, off, data, vice=None):
    self.policy.write (self.master, self.ino)
    return vice.write (self.ino, off, data)
  write= trackermethod (write)

  def trunc (self, size=0, vice=None):
    # and wipe out data
    vice.trunc (self.ino, size)
    # more to come
    # what was coming?
    # wassit the times? no need...
  trunc= trackermethod (trunc)

  ########
  # inode
  ########
  def readdir (self, vice=None):
    return vice.readdir (self.ino)
  readdir= trackermethod (readdir)

  def link (self, name, ino, inc, over, vice=None):
    return vice.link (self.ino, name, ino, inc, over)
  link= trackermethod (link)

  def incNlink (self, vice=None):
    return vice.incNlink (self.ino)
  incNlink= trackermethod (incNlink)

  def unlink (self, name, dec, vice=None):
    return vice.unlink (self.ino, name, dec)
  unlink= trackermethod (unlink)

  def decNlink (self, vice=None):
    return vice.decNlink (self.ino)
  decNlink= trackermethod (decNlink)

  def lookup (self, fileName, vice=None):
    """
      no '/'s please!
    """
    ino= vice.lookup (self.ino, fileName)
    if ino:
      return self.master.getInode (ino)
    else:
      return None
  lookup= trackermethod (lookup)
