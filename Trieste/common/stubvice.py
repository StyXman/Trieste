###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from time import time
from stat import S_IRWXU, S_IRWXG, S_IRWXO
from errno import EIO

from Trieste.common.stub import Stub
from Trieste.common.viceclient import ViceClient
from Trieste.common.utils import csvParse
from Trieste.common import consts

class StubVice (Stub):
  def __init__ (self, master, url, key):
    Stub.__init__ (self, master, url, key)
    self.blocks= None
    self.fblocks= None
    self.files= None
    # self.updateStats ()

  def createEmptyClient (self):
    self._client= ViceClient (self._url, self._master, self)

  def urls (self, list):
    return map (lambda x: x.url (), list)

  def emp (self):
    what= ['emp']
    ans= self._client.ask (what)
    return ans

  def mkRootDir (self):
    now= int(time ())
    # [ino, mode, size, nlink, ctime, atime, mtime, uid, gid]
    self.mkinode (consts.rootDirIno, [consts.rootDirIno, consts.S_DIR|S_IRWXU|S_IRWXG|S_IRWXO, 0, 0, now, now, now, 0, 0])
    self.mkdir (consts.rootDirIno)
    return consts.rootDirIno

  def mkinode (self, ino, stat):
    try:
      what= ['make inode', ino, stat]
      ans= self._client.ask (what)[1]
    except:
      ans= -EIO
    return ans

  def delinode (self, ino):
    what= ['del inode', ino]
    ans= self._client.ask (what)

    return ans

  def incNlink (self, ino):
    what= ['inc nlink', ino]
    ans= self._client.ask (what)
    return ans[1]

  def decNlink (self, ino):
    what= ['dec nlink', ino]
    ans= self._client.ask (what)
    return ans[1]

  def stat (self, ino, stat=None):
    if stat is None:
      # read
      what= ['read inode', ino]
    else:
      # write
      what= ['write inode', ino, stat]
    return self._client.ask (what)

  def setattr (self, ino, attr):
    what= ['setattr', ino, attr]
    ans= self._client.ask (what)

    return ans

  def link (self, dirIno, fileName, ino, inc, over):
    what= ['link', dirIno, fileName, ino, inc, over]
    ans= self._client.ask (what)
    error= ans[1]

    return error

  def unlink (self, dirIno, fileName, dec):
    what= ['unlink', dirIno, fileName, dec]
    ans= self._client.ask (what)
    error= ans[1]
    ino= ans[2]

    return (error, ino)

  def lookup (self, dirIno, fileName):
    what= ['lookup', dirIno, fileName]
    ans= self._client.ask (what)

    # this might return None
    return ans[0]

  def mkdir (self, ino, parent=None):
    if parent==None:
      parent= ino
    what= ['make dir', ino, parent]
    ans= self._client.ask (what)
    error= ans[1]
    return error

  def rmdir (self, ino):
    what= ['del dir', ino]
    ans= self._client.ask (what)
    error= ans[1]
    return error

  def read (self, ino, off, size):
    # None means error
    block= None
    what= ['read', ino, off, size]
    ans= self._client.ask (what)

    if ans[0]>0:
      # read that qty
      block= self._client.readData (ans[0])
    return block

  def write (self, ino, off, block):
    what= ['write', ino, off, len (block)]
    ans= self._client.ask (what, block)
    return ans[0]

  def trunc (self, ino, size):
    what= ['trunc', ino, size]
    return self._client.ask (what)

  def readdir (self, ino):
    what= ['read dir', ino]
    ans= self._client.ask (what)
    return ans

  def statfs (self):
    if self.blocks==None:
      self.updateStats ()
    return [self.blocks, self.fblocks, self.files]

  def updateStats (self):
    what= ['stat fs']
    (self.blocks, self.fblocks, self.files)= self._client.ask (what)[0]

  def setStats (self, stats):
    (self.blocks, self.fblocks, self.files)= stats
