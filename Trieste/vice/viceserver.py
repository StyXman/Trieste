###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from errno import *

from Trieste.common.utils import csvPrettyPrint
from Trieste.common.server import Server
from Trieste.common import consts

class ViceServer (Server):
  """
    should store which fh the client has so we can close 'em when the client dies.
  """
  def __init__ (self, master, client):
    Server.__init__ (self, master, client)
    self.debug (1, "created and running viceserver[%d]" % self._socket.fileno ())
    self.setName (name=("ViceServer[%d]" % (self._socket.fileno ())))

  def write (self, what):
    Server.write (self, [self._master.stats (), what])

  def attend (self, what, args):
    finished= False

    #######################
    # don't look back in anger
    #######################
    if what=='quit':
      self.write (['bye'])
      self.close ()
      finished= True

    elif what=='terminate':
      self._master._terminate= True
      self.write (["i'm on that, bye"])

    else:
      # locking ops

      self._master._data.data.acquire ()
      self._master._data.meta.acquire ()

      ###############
      # inode stat ops
      ###############
      if what=='read inode':
        ino= args[0]
        error= self._master._data.lock (ino)
        if error==0:
          self.write (self._master._data.stat (ino))
          self._master._data.unlock (ino)
        else:
          self.write ([None, -ENOENT])

      elif what=='write inode':
        ino= args[0]
        stat= args[1]
        error= self._master._data.lock (ino)
        if error==0:
          self._master._data.stat (ino, stat)
          self.write ([True])
          self._master._data.unlock (ino)
        else:
          self.write ([False, error])

      elif what=='make inode':
        ino= args[0]
        stat= args[1]
        self.debug (1, 'making inode: stat is %s' % str (stat))
        error= self._master._data.lock (ino, creating=True)
        if error==0:
          # write it inconditionally
          self._master._data.stat (ino, stat)
          # bad place alone
          # increase file count
          self._master.ufiles+= 1
          self.write ([True, error])
          self._master._data.unlock (ino)
        else:
          self.write ([False, error])

      elif what=='del inode':
        ino= args[0]
        error= self._master._data.lock (ino)
        if error==0:
          self.debug (1, 'deleting inode')
          # del data
          error= self._master._data.trunc (ino)
          # del metadata
          self._master._data.masterLock.acquire ()
          del self._master._data.meta[ino]
          self._master._data.masterLock.release ()
          self.write ([True, error])
          self._master._data.unlock (ino)
        else:
          self.write ([False, error])

      elif what=='inc nlink':
        ino= args[0]
        error= self._master._data.lock (ino)
        if error==0:
          stat= self._master._data.stat (ino)
          stat[consts.statNlink]+= 1
          self._master._data.stat (ino, stat)
          self.write ([True, error])
          self._master._data.unlock (ino)
        else:
          self.write ([False, error])

      elif what=='dec nlink':
        ino= args[0]
        error= self._master._data.lock (ino)
        if error==0:
          stat= self._master._data.stat (ino)
          stat[consts.statNlink]-= 1
          self._master._data.stat (ino, stat)
          if stat[consts.statNlink]==0:
            # dropped to zero; delete the poor bastard
            # del data
            error= self._master._data.trunc (ino)
            # del metadata
            del self._master._data.meta["%d" % ino]
            # dec file count
            self._master.ufiles-=1
          self.write ([True, stat[consts.statNlink]])
          self._master._data.unlock (ino)
        else:
          self.write ([False, error])

      elif what=='setattr':
        ino= args[0]
        attrs= args[1]
        if self._master._data.hasInode (ino):
          stat= self._master._data.stat (ino)
          for key in attrs.keys ():
            const= 'stat'+key.capitalize ()
            self.debug (2, 'getting %s' % const)
            index= getattr (consts, const)
            stat[index]= attrs[key]
          self.write (self._master._data.stat (ino, stat))
        else:
          self.write ([None, -ENOENT])

      ########
      # 'file' ops
      ########
      elif what=='pin':
        ino= args[0]
        if self._master._data.hasInode (ino):
          self._master._data.pin (ino)
          self.write ([True])
        else:
          self.write ([None, -ENOENT])

      elif what=='read':
        ino= args[0]
        off= args[1]
        size= args[2]
        if self._master._data.hasInode (ino):
          data= self._master._data.read (ino, off, size)
          self.write ([len(data)])
          self.writeData (data)
        else:
          self.write ([None, -ENOENT])

      elif what=='write':
        ino= args[0]
        off= args[1]
        size= args[2]
        data= self.readData (size)
        if self._master._data.hasInode (ino):
          self.write ([self._master._data.write (ino, off, data)])
        else:
          self.write ([None, -ENOENT])

      elif what=='unpin':
        ino= args[0]
        if self._master._data.hasInode (ino):
          self._master._data.unpin (ino)
          self.write ([True])
        else:
          self.write ([None, -ENOENT])

      elif what=='read dir':
        ino= args[0]
        if self._master._data.hasInode (ino):
          dirlist= self._master._data.dirContents (ino)
          # dirlist= map (lambda name: (name, int(self._master._data["%d/%s" % (ino, name)])), dirlist)
          self.debug (1, 'reading dir: %s' % dirlist)
          self.write (dirlist)
        else:
          self.write ([None, -ENOENT])

      elif what=='sync':
        # please don't use it very often!
        self._master.sync ()
        self.write ([True])

      elif what=='lock':
        ino= args[0]
        bit= args[1]
        if self._master._data.hasInode (ino):
          self._master._data.lock (ino, bit)
          self.write ([True])
        else:
          self.write ([False, -ENOENT])

      elif what=='trunc':
        ino= args[0]
        size= args[1]
        if self._master._data.hasInode (ino):
          self._master._data.trunc (ino, size)
          self.write ([True])
        else:
          self.write ([False, -ENOENT])


      ###########
      # inode ops
      ###########
      elif what=='lookup':
        ino= args[0]
        fileName= args[1]
        if self._master._data.hasInode (ino):
          self.write ([self._master._data.lookup (ino, fileName)])
        else:
          self.write ([None, -ENOENT])

      elif what=='link':
        dirIno= args[0]
        fileName= args[1]
        fileIno= args[2]
        inc= args[3]
        over= args[4]
        if self._master._data.hasInode (dirIno):
          # lock is already acquired by the vfs
          # fs/namei.c:vfs_link ()
          ans= self._master._data.link (dirIno, fileName, fileIno, inc, over)
          self.write ([True, ans])
        else:
          self.write ([False, -ENOENT])

      elif what=='unlink':
        dirIno= args[0]
        fileName= args[1]
        dec= args[2]
        if self._master._data.hasInode (dirIno):
          # lock is already acquired by the vfs
          # fs/namei.c:vfs_unlink ()
          ino= self._master._data.lookup (dirIno, fileName)
          ans= self._master._data.unlink (dirIno, fileName, dec)
          self.write ([True, ans, ino])
        else:
          self.write ([False, -ENOENT])

      elif what=='make dir':
        ino= args[0]
        parent= args[1]
        ans= self._master._data.mkdir (ino, parent)
        self.write ([True, ans])

      elif what=='del dir':
        ino= args[0]
        if self._master._data.hasInode (ino):
          self._master._data.rmdir (ino)
        else:
          self.write ([False, -ENOENT])
        self.write ([True, 0])

      #######
      # mkfs
      #######
      elif what=='emp':
        self._master.emp ()
        self.write ([True])

      elif what=='make root dir':
        ino= self._master.mkRootDir ()
        self.write ([True, ino])

      ########
      # debug
      ########
      elif what=='inodes':
        self.write (self._master.keys ())

      elif what=='keys':
        self.write ([self._master._data.meta.keys (), self._master._data.data.keys ()])

      #######
      # misc
      #######
      elif what=='stat fs':
        self.write ([self._master.stats ()])

      else:
        # fallback
        self.debug (5, 'error: unknown message >%s<' % what)
        self.write (['error']);

      self._master._data.meta.release ()
      self._master._data.data.release ()

    return finished
