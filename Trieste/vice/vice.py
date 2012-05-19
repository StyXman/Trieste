###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################


from Trieste.common.utils import random, next
from Trieste.common.master import Master
from Trieste.common import consts

from Trieste.vice.vicedata import ViceData
from Trieste.vice.viceserver import ViceServer

class Vice (Master):
  def __init__ (self, url, column=0, path='data', space=None, fileName=None):
    Master.__init__ (self, None, url, column, fileName=fileName)
    self._data= ViceData (self, "%s/data" % (path))
    self._handles= {}
    self._serverType= ViceServer
    self._size= space

    # stat
    self.blocks= None
    self.fblocks= None
    self.ufiles= None

    self.initStat ()
    self.setUrl (url)

  def initStat (self):
    self.debug (5, 'start...')
    self.blocks= self._size*consts.mega/consts.fragmentSize
    self.debug (5, 'blocks and files...')
    (ublocks, self.ufiles)= self._data.usedBlocksAndFiles ()
    self.fblocks= self.blocks-ublocks
    self.debug (5, 'stop!')

  def init (self, net=None, url=None):
    Master.init (self)

    if net:
      peer= None
      finished= self._terminate
      while not finished:
        peer= self.discover (net)
        finished= self._terminate or peer

      if peer:
        self.gossip (peer)
        self.propalate ()
        return True
      else:
        return False

    if url:
      key= self.getNavelKey (url)
      peer= self._peers.getNavel (url, key)
      self.gossip (peer)
      self.propalate ()
      return True

    return False

  def ident (self):
    return ["i am", str(self.url ())]

  def propalate (self):
    navels= self._peers.navels ()
    keys= navels.keys ()
    keys.sort ()
    m= next (keys)
    # just in case there's no more than one navel
    n= m
    # just in case there is more than one navel
    first= m
    for n in keys:
      peer= navels[m]
      self.debug (1, "propalating to %s" % peer)
      self._ring.addData (self.giveData (m, n), n, peer)
      m= n

    # the last one is the one with the WAS.
    peer= navels[m]
    self.debug (1, "propalating to %s" % peer)
    self._ring.addData (self.giveData (m, first), first, peer)

  def keys (self):
    return self._data.keys ()

  def sync (self):
    self._data.sync ()

  #############
  def emp (self):
    self._data.emp ()
    self.initStat ()

  def mkRootDir (self):
    self._data.mkdir (consts.rootDirIno)
    return consts.rootDirIno

  def stats (self):
    # f_blocks, f_bavail, f_files
    return (self.blocks, self.fblocks, self.ufiles)

  def updateStats (self):
    # noop
    pass

  def periodic (self):
    # this one should shout its keys
    Master.periodic (self)
    if not self._terminate:
      # can't do it otherwise
      # self.sync ()
      pass
    else:
      self.debug (1, 'you might be pregnant...')

  def stop (self):
    self.sync ()
    Master.stop (self)
