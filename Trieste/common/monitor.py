###########################################################################
#    Copyright (C) 2004 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from threading import RLock

from Trieste.common.object import Object

class NotLockedError (Exception):
  pass

class CLock (Object):
  def __init__ (self):
    self.lock= RLock ()
    self.locked= 0

  def acquire (self, blocking=True):
    ans= self.lock.acquire (blocking)
    if ans:
      self.locked+= 1
    return ans

  def release (self):
    self.locked-= 1
    self.lock.release ()
    return self.locked

class Monitor (CLock):
  def __init__ (self, data, name):
    CLock.__init__ (self)
    self.data= None
    self.name= name
    self.setData (data)

  def acquire (self, blocking=True):
    # self.debug (1, 'will lock %s' % self.name)
    ans= CLock.acquire (self, blocking)
    # self.debug (1, 'locked %s: depth %d' % (self.name, self.locked))
    return ans

  def release (self):
    # self.debug (1, 'releasing %s: depth %d' % (self.name, self.locked))
    ans= CLock.release (self)
    return ans

  def setData (self, data):
    self.acquire ()
    self.data= data
    self.release ()

  def __getattr__ (self, name):
    if not self.locked:
      raise NotLockedError
    return getattr (self.data, name)

  def __delattr__ (self, name):
    if not self.locked:
      raise NotLockedError
    delattr (self.data, name)

  def __getitem__ (self, key):
    if not self.locked:
      raise NotLockedError
    return self.data[key]

  def __setitem__ (self, key, value):
    if not self.locked:
      raise NotLockedError
    self.data[key]= value

  def __delitem__ (self, key):
    if not self.locked:
      raise NotLockedError
    del self.data[key]

class ImplicitMonitor (Monitor):

  def __getattr__ (self, name):
    self.acquire ()
    ans= getattr (self.data, name)
    self.release ()
    return ans

  def __delattr__ (self, name):
    self.acquire ()
    delattr (self.data, name)
    self.release ()

  def __getitem__ (self, key):
    self.acquire ()
    ans= self.data[key]
    self.release ()
    return ans

  def __setitem__ (self, key, value):
    self.acquire ()
    self.data[key]= value
    self.release ()

  def __delitem__ (self, key):
    self.acquire ()
    del self.data[key]
    self.release ()
