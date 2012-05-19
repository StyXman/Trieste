###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from threading import RLock

from Trieste.common.utils import random
from Trieste.common.object import Object
from Trieste.common import consts

class UmbData (Object):
  def __init__ (self, min, max):
    Object.__init__ (self)
    self._hashLock= RLock ()
    self._hash= {}
    self._max= max
    self._min= min
    self._full= False

  def acquire (self):
    self._hashLock.acquire ()

  def release (self):
    self._hashLock.release ()

  def addValue (self, key, value):
    self._hashLock.acquire ()
    # try to add it; if it fails, create a list
    # TODO: must not create duplicates. don't forget the master problem
    try:
      self._hash[key].append (value)
    except KeyError:
      self._hash[key]= [value]
    self._hashLock.release ()

  def addValues (self, key, values):
    """
      just like addValue, but in chunks
    """
    self._hashLock.acquire ()
    # try to add it; if it fails, create a list
    # TODO: must not create duplicates. don't forget the master problem
    # WHICH master problem? :-(
    try:
      self._hash[key].extend (values)
    except KeyError:
      self._hash[key]= values
    self._hashLock.release ()

  def setValue (self, key, value):
    self._hashLock.acquire ()
    self._hash[key]= [value]
    self._hashLock.release ()

  def setValues (self, key, values):
    """
      just like setValue, but in chunks
    """
    self._hashLock.acquire ()
    self._hash[key]= values
    self._hashLock.release ()

  def delValue (self, key, value):
    self._hashLock.acquire ()
    # try to del it; if it fails, ignore
    try:
      self._hash[key].remove (value)
    except IndexError:
      pass
    self._hashLock.release ()

#   def setValues (self, key, values):
#     for value in values:
#       self.setValue (key, value)

  def delKey (self, key):
    """
      lock sould be acquired
    """
    # sould be a way to test that!
    try:
      del self._hash[key]
    except KeyError:
      # ignore wrong keys
      pass
    self._full= False

  def delKeys (self, keys):
    self._hashLock.acquire ()
    for key in keys:
      self.delKey (key)
    self._hashLock.release ()

  def getValues (self, key):
    self._hashLock.acquire ()
    try:
      value= self._hash[key]
    except KeyError:
      value= []
    self._hashLock.release ()
    return value

  def keys (self):
    self._hashLock.acquire ()
    result= self._hash.keys ()
    self._hashLock.release ()
    return result

  def resizeFree (self, newMax):
    self._max= newMax-1

  def findFree (self):
    def randomKey ():
      # the '=' is for when the navel holds the whole key space
      # i.e., it's the only one in the ring
      if self._min>=self._max:
        if random (2):
          n= random (0, self._max)
        else:
          n= random (self._min, consts.maxIno)
      else:
        n= random (self._min, self._max)
      return n

    i= self._min
    j= randomKey ()
    k= self._max-1
    self.debug (2, "i: %d, j: %d, k: %d" % (i, j, k))
    while self._hash.has_key (j) and not (i==j or j==k):
      if random (2):
        k= j
        # check this property
        if i>j:
          # WAS
          j= ((i+j+consts.maxIno)/2) % consts.maxIno
        else:
          j= ((i+j)/2) % consts.maxIno
      else:
        i= j
        if j>k:
          # WAS
          j= ((j+k+consts.maxIno)/2) % consts.maxIno
        else:
          j= ((j+k)/2) % consts.maxIno
      self.debug (2, "i: %d, j: %d, k: %d" % (i, j, k))

    if (i==j or j==k):
      self.debug (2, 'no luck, try linearly')
      j= self._min
      while self._hash.has_key (j) and not j==self._max:
        j= (j+1) % consts.maxIno
      if j==self._max:
        # sorry, ugly; check again
        if self._hash.has_key (j):
          # no more no more
          self._full= True
          return None

    # mark as used; will need GC for asked but not used free ino's
    # WARNING: very similar to inode w/o a active vice!
    self._hash[j]= []
    return j

  def emp (self):
    self._hash= {}
