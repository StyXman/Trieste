###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################


from Trieste.common.utils import debugPrint, random, next
from Trieste.common.object import Object

class Policy (Object):
  migrates= False
  def __init__ (self):
    Object.__init__ (self)

  def vicesForNewFile (self, master):
    raise NotImplementedError

  def newIno (self, master):
    raise NotImplementedError

  def open (self, master, ino):
    # the default is do nothing
    pass

  def read (self, master, ino):
    # the default is do nothing
    pass

  def write (self, master, ino):
    # the default is do nothing
    pass

  def close (self, master, ino):
    # the default is do nothing
    pass

class Random (Policy):
  """
    The policy that just selects ramdon things
  """
  def vicesForNewFile (self, master):
    """
      returns: a list of sm's where a new file will reside.
    """
    return (master.peers ().getRandomVice (), [])

  def newIno (self, master):
    firstNavel= master.peers ().getRandomNavel ()
    ino= firstNavel.free ()

    oldNavel= firstNavel
    (url, key)= firstNavel.succ ()
    navel= master.peers ().getNavel (url, key)

    while ino==None and navel!=firstNavel:
      (ino, navels, vices)= navel.free ()

      oldNavel= navel
      (url, key)= firstNavel.succ ()
      navel= master.peers ().getNavel (url, key)

    return (ino, oldNavel)

class WeightedUniform (Random):
  """
    The policy that just selects ramdon things
  """
  def vicesForNewFile (self, master):
    """
      returns: a list of sm's where a new file will reside.
    """
    totalFreeBlocks= 0
    index= 0
    statedVices= []

    vices= master.peers ().vices ()
    for key in vices.keys ():
      vice= vices[key]
      try:
        fsstat= vice.statfs ()
        blocks= fsstat[0]
        bfree= fsstat[1]

        totalFreeBlocks+= bfree

        self.debug (2, 'usage: %f' % ((1.0*bfree)/blocks))
        statedVices.append ((vice, totalFreeBlocks))
      except Exception, e:
        pass

    i= random (totalFreeBlocks)
    index= 0

    # now check where has it fell
    vice= None
    item= next (statedVices)
    if item:
      (vice, index)= item
      self.debug (2, 'i: %d; tfb: %d; index: %d' % (i, totalFreeBlocks, index))
    while item is not None and i>index:
      item= next (statedVices)
      if item:
        (vice, index)= item
        self.debug (2, 'i: %d; tfb: %d; index: %d' % (i, totalFreeBlocks, index))

    self.debug (1, 'vice: %s' % vice)
    return (vice, [])

# set the desired policy here
# policy= WeightedUniform ()
