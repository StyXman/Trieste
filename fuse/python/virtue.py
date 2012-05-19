#! /usr/bin/python2.2
###########################################################################
#    Copyright (C) 2004 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from sys import argv
from types import IntType
from os import O_RDONLY, O_WRONLY, O_CREAT, O_EXCL, O_TRUNC, O_APPEND
from __future__ import nested_scopes
from time import time
from types import IntType
from errno import *
from stat import *

from fuse import Fuse
from utils import debugPrint, Option, parseOpts, UmbDead
from inode import Inode
from master import Master
import consts
import fuseconsts
import policies

class Virtue (Fuse, Master):
  def __init__ (self, url=None, net=None, fileName=None):
    # Fuse.__init__ (self)
    Master.__init__ (self, fileName=fileName)
    self.debug (1, 'v: logging in %s' % fileName)
    self.inodes= {}
    self.policy= policies.WeightedUniform ()

    navel= None
    if url:
      key= self.getNavelKey (url)
      navel= self._peers.getNavel (url, key)
    else:
      while not navel:
        navel= self.discover (net)
    self.gossip (navel)

  ##############
  # inode cache
  ##############
  def getInode (self, ino, vice=None):
    if self.inodes.has_key (ino):
      inode= self.inodes[ino]
    else:
      self.debug (1, "not found ino %d" % (ino), 2)
      inode= Inode (ino, self, vice=vice, policy=self.policy)
      self.inodes[ino]= inode
    return inode

  def delInode (self, ino):
    try:
      del self.inodes[ino]
    except KeyError:
      pass

  def stat2attr (self, stat):
    # st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime
    # [ino, mode, size, nlink, ctime, atime, mtime, uid, gid]
    mapping= [1, 0, 3, 7, 8, 2, 5, 6, 4]
    # self.debug (1, "converting %s" % stat)
    ans= map (lambda i: stat[i], mapping)
    # fake dev
    ans.insert (2, 0)
    return tuple(ans)

  def mkinode (self, parent, name, mode):
    self.log ("mkinode!")
    # inc parent link count if this is a dir
    incParent= S_ISDIR (mode)
    incTarget= not incParent
    (ino, navel)= self.policy.newIno (self)
    now= int(time ())

    (vice, backups)= self.policy.vicesForNewFile (self)
    # [ino, mode, size, nlink, ctime, atime, mtime, uid, gid]
    error= vice.mkinode (ino, [ino, mode, 0, 0, now, now, now, 0, 0])

    if error==0:
      # bind now, so link() works
      self._ring.addData ({ ino: [ vice.url () ] }, ino)
      error= self.link (parent.ino, name, ino, incParent=incParent, incTarget=incTarget)

      if error<0:
        vice.delinode (ino)
        # unbind in ring
        self._ring.delKey (ino)
        # forget inode
        self.delInode (ino)
        inode= error
      else:
        inode= self.getInode (ino, vice=vice)
    else:
      inode= error

    self.log ("edonikm!L %s" % str (inode))
    return inode

  ###########
  # fuse ops
  ###########
  def getattr (self, ino):
    self.log ("getattr!")
    inode= self.getInode (ino)
    stat= inode.stat ()
    if not type(stat) is IntType:
      stat= self.stat2attr (stat)

    self.log ("rttateg!")
    return stat

  def setattr (self, ino, mask, iattr):
    self.log ("setattr; mask: %d; %s!" % (mask, iattr))
    attr= {}
    for i, j in (('size', 2), ('mode', 3), ('uid', 4), ('gid', 5), ('atime', 0), ('mtime', 1)):
      if mask & getattr (fuseconsts, i):
        self.debug (3, 'setting attr %s to %d' % (i, iattr[j]))
        attr[i]= iattr[j]

    inode= self.getInode (ino)
    stat= inode.setattr (attr)
    if not type(stat) is IntType:
      stat= self.stat2attr (stat)

    self.log ("rttates!")
    return stat

  def mknod (self, ino, name, mode):
    self.log ("mknod!")

    parent= self.getInode (ino)
    # we could move this to the policiy,
    # so a self.self.policy that implementes 'child in the same vice than his parent'
    error= self.mkinode (parent, name, mode).ino
    if not type(error) is IntType:
      # got an Inode, so OK
      error= error.ino

    self.log ("donkm!")
    return error

  def open (self, ino, flags):
    self.log ("open %d!" % ino)

    inode= self.getInode (ino)
    self.policy.open (self, inode.ino)
    error= 0

    self.log ("nepo!")
    return error

  def read (self, ino, size, off):
    # self.debug (2, "reading @ %d, size %d" % (off, size))
    # self.log ("read!")
    # self.log (time ())

    inode= self.getInode (ino)
    error= inode.read (off, size)

    # self.log ("daer!")
    # self.log (time ())
    # self.nextLog ()
    return error

  def write (self, ino, buf, off):
    # self.debug (2, "writing @ %d, size %d" % (off, len(buf)))
    # self.log ("write!")
    # self.log (time ())

    inode= self.getInode (ino)
    data= inode.write (off, buf)

    # self.log ("etirw!")
    # self.log (time ())
    # self.nextLog ()
    return data

  def getdir (self, ino):
    self.log ("getdir!")

    inode= self.getInode (ino)
    names= inode.readdir ()

    self.log ("ridteg!")
    return map (lambda x: (x,0), names)

  def lookup (self, ino, name):
    self.log ("lookup!")

    error= -ENOENT
    parent= self.getInode (ino)
    inode= parent.lookup (name)
    if inode:
      error= inode.stat ()
      if not type(error) is IntType:
        error= self.stat2attr (error)

    self.log ("pukool!")
    return error

  def link (self, ino, name, target, incParent=False, incTarget=True, overwrite=False):
    self.log ("link! %d, %d" % (incParent, incTarget))

    parent= self.getInode (ino)
    error= parent.link (name, target, incParent, overwrite)
    if error==0 and incTarget:
      inode= self.getInode (target)
      error= inode.incNlink ()
      if error:
        parent.unlink (name, incParent)

    self.log ("knil! %d" % error)
    return error

  def unlink (self, ino, name, decParent=False, decTwice=False):
    self.log ("unlink!")

    parent= self.getInode (ino)
    (error, ino)= parent.unlink (name, decParent)
    if error==0:
      inode= self.getInode (ino)
      nlink= inode.decNlink ()
      if nlink==1 and decTwice:
        self.log ('unlinking twice: seems to be a dir and this is the last link')
        # dirs get unlinked twice the last time
        nlink= inode.decNlink ()
      if nlink==0:
        # unbind in ring
        self._ring.delKey (ino)
        # forget inode
        self.delInode (ino)
      # check for error and rollback!

    self.log ("knilnu!")
    return error

  def mkdir (self, ino, name, mode):
    self.log ("mkdir!")

    parent= self.getInode (ino)
    # builds stat and links in parent
    inode= self.mkinode (parent, name, consts.S_DIR|mode)
    if not type(inode) is IntType:
      # got an Inode, so OK
      vice= inode.vice ()
      # builds the dir structs (liks to . and ..)
      vice.mkdir (inode.ino, ino)
      error= 0

    self.log ("ridkm!")
    return error

  def rmdir (self, ino, name):
    self.log ("rmdir!")

    parent= self.getInode (ino)
    # gotta know ino
    inode= parent.lookup (name)
    vice= inode.vice ()
    # destroys structures
    error= vice.rmdir (inode.ino)
    if error==0:
      # destroy stat and link in parent
      error= self.unlink (parent.ino, name, decParent=True, decTwice=True)

    self.log ("ridmr!")
    return error

  def symlink (self, ino, name, target):
    self.log ("symlink!")

    error= self.mknod (ino, name, consts.S_LINK|0777)
    if error>0:
      self.write (error, target, 0)
      error= 0

    self.log ("knilmys!")
    return error

  def readlink(self, ino):
    self.log ("readlink!")

    inode= self.getInode (ino)
    error= inode.read ()

    self.log ("knildaer!")
    return error

  def rename (self, ino, name, nino, nname):
    self.log ("rename!")

    # oldp, oldn, newp, newn
    # there's a special case when ino and nino are the same
    error= -ENOENT
    oldParent= self.getInode (ino)
    # here's right, cause we get the ino
    oldInode= oldParent.lookup (name)
    # gotta know if it's a dir or not for link count :(
    stat= oldInode.stat ()

    if oldInode:
      newParent= self.getInode (nino)
      # check if it's a dir!
      # error= newParent.link (nname, oldInode.ino)
      inc= stat[consts.statMode] & consts.S_DIR
      error= self.link (nino, nname, oldInode.ino, incParent=inc, overwrite=True)
      if error==0:
        # error= oldParent.unlink (name)
        error= self.unlink (oldParent.ino, name, decParent=inc)
      # rollback!

    self.log ("emaner!")
    return error

  def statfs (self):
    self.log ("statfs!")
    blocks= 0
    free= 0
    files= 0
    # done too rarely that can be done more accurately
    vices= self._peers.vices ()
    for key in vices.keys():
      try:
        fsstat= vices[key].statfs ()
        self.debug (1, "b: %d, a:%d, f: %d" % fsstat)
        blocks+= fsstat[0]
        free+= fsstat[1]
        files+= fsstat[2]
      except:
        # don't count it
        pass

    ffree= consts.maxIno-files
    # f_blocks, f_bfree, f_bavail, f_files, f_ffree, f_namemax
    self.log ("sftats!")
    return (consts.fragmentSize, blocks, free, consts.maxIno, ffree, 255)

if __name__ == '__main__':
  (opts, args)= parseOpts ([
    Option ('b', 'broadcast-to', True, default=''),
    Option ('c', 'connect-to', True),
    Option ('l', 'log-file', True, default='virtue.log'),
  ], argv[1:])
  debugPrint (1, 'parsed args: %s, left args: %s' % (
    ", ".join (
      map (
        lambda x: "%s: %s" % (x, opts[x].value),
        opts.keys ()
      ))
    , args))

  net= opts['b'].asString ()
  url= opts['c'].asString ()

  server= Virtue (url, net, fileName=opts['l'].asString ())
  server.flags= 0
  # server.multithreaded= 1;

  server.main ()
  server.saveLog ()
