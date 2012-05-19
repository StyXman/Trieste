###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from bsddb import hashopen
from threading import RLock
from errno import *
from os.path import dirname
from os import stat, makedirs, unlink

from Trieste.common.utils import csvPrettyPrint, csvParse
from Trieste.common.monitor import Monitor, CLock
from Trieste.common.object import Object
from Trieste.common import consts

class ViceData (Object):
  """
    holds three hashes: one for data, anoother for stat, the last for locks
    the first two are really bsddb's
    the data one contains three kinds on entries:
    * entries with key in the from "ino/chunkNo", which are for regular files.
      each file is broken in chunks of the same size.
    * entries with key in the from "ino/fileName", which are for directories.
      that entry means that the dir w/ inode number ino has a link to another ino with filename fileName.
      the value of such entry is the file's ino.
    * entries with key in the from "ino", which are also for directories.
      these ones contain a csv string of the filenames.
      this one is needed because we need to get the listing of the dir,
      and it's easier than to iterate over the keys of an bssdb.
  """
  def __init__ (self, master, path):
    Object.__init__ (self)
    self.master= master
    dir= dirname (path)
    try:
      stat (dir)
    except OSError:
      makedirs (dir)
    self.path= path
    self.data= None
    self.meta= None
    self.locks= None
    self.mkDB ()
    # master lock. global actions (like sync and emp) must acquire this one.
    self.masterLock= RLock ()

  def mkDB (self):
    path= self.path
    self.debug (1, "opening %s-data.bsddb" % path)
    self.data= Monitor (hashopen ("%s-data.bsddb" % path, 'c'), 'data')
    self.debug (1, "opening %s-metadata.bsddb" % path)
    self.meta= Monitor (hashopen ("%s-metadata.bsddb" % path, 'c'), 'meta')
    # per inode locks. any action over an inode must acquire
    self.locks= Monitor ({}, 'locks')

  def rmDB (self):
    self.data= None
    self.meta= None
    self.locks= None

    path= self.path
    unlink ("%s-data.bsddb" % path)
    unlink ("%s-metadata.bsddb" % path)

  def hasInode (self, ino):
    # self.debug (1, 'looking for inode %s' % ino)
    self.meta.acquire ()
    ans= self.meta.has_key (str(ino))
    self.meta.release ()
    return ans

  def stat (self, ino, stat=None):
    if stat:
      # self.debug (2, 'setting stat')
      self.meta[str(ino)]= str(stat)
    else:
      stat= eval (self.meta[str(ino)])
    # TODO: so bark if it's not right
    return stat

  def keys (self):
    self.meta.acquire ()
    l= map (lambda x: int(x), self.meta.keys ())
    self.meta.release ()
    return l

  def getValues (self, key):
    # needed for master.giveData()
    # this way a vice gives his url as the data (to be added [to the list that it's there])
    # but it's a very ugly generalization
    return [self.master.url ()]

  #########
  # file ops
  #########
  def size (self, ino, size=None):
    stat= self.stat (ino)
    if size is not None:
      stat[consts.statSize]= size
      self.stat (ino, stat)
    return stat[consts.statSize]

  def pages (self, ino):
    """
      How much pages does ino have allocated.
    """
    # for size==0 return 0
    # for sizes E (1..pageSize) return 1
    # and so forth
    size= self.size (ino)
    pages= (size+consts.pageSize-1)/consts.pageSize
    # self.debug (2, "pages: %d, size: %d" % (pages, size))
    return pages

  def read (self, ino, off=0, size=None):
    # profiling!
    # return "\0"*size
    # lot of things:
    # first, if data is spread in several pages, read them
    # second, what if @ eof? None
    if size is None:
      size= self.size (ino)

    # self.debug (2, "reading @ %d, size %d" % (off, size))
    data= ''
    bytesToRead= size
    # ugh
    bytesRead= size
    try:
      while bytesToRead and bytesRead:
        (page, start)= divmod (off, consts.pageSize)
        end= min (consts.pageSize, start+bytesToRead)

        pageData= self.data["%d/%d" % (ino, page)]
        readData= pageData[start:end]
        bytesRead= len (readData)
        # self.debug (2, "off: %d, chunk: %d, chunkOff(CO): %d, max: %d, bytesRead: %d, bytesTR: %d, pageSz-CO: %d, CO+bytesTR: %d" %
        #                # (off, page, start, end, bytesRead, bytesToRead, consts.pageSize-start, start+bytesToRead))
        data+= readData
        bytesToRead-= bytesRead
        off+= bytesRead
        # self.debug (2, "off: %d, chunk: %d, chunkOff(CO): %d, max: %d, bytesRead: %d, bytesTR: %d, pageSz-CO: %d, CO+bytesTR: %d\n" %
        #                (off, page, start, end, bytesRead, bytesToRead, consts.pageSize-start, start+bytesToRead))
    except KeyError:
      # means EOF?
      pass
    return data

  def trunc (self, ino, size=0, shrink=True):
    # self.debug (2, 'trunc\'ing', 2)
    fileSize= self.size (ino)
    if size==fileSize:
      # self.debug (2, 'already there (%d<->%d); bailing out' % (size, fileSize))
      return size

    # check if we need to create previous pages
    lastPage= self.pages (ino)
    (page, end)= divmod (size, consts.pageSize)
    if page>lastPage:
      # self.debug (1, 'expanding')
      # ... data  |
      # ... | lastPage | ... | page |
      #                          ^ end

      # first add '0's to last page
      try:
        pageData= self.data["%d/%d" % (ino, lastPage)]
      except KeyError:
        self.master.fblocks-= 1
        if self.master.fblocks==0:
          return -ENOSPC
        pageData= ''
        # decrease free count
      pageLen= len (pageData)
      if pageLen<consts.pageSize:
        # self.debug (1, 'filling up lastPage: %d-> %d' % (pageLen, consts.pageSize))
        pageData+= "\0"*(consts.pageSize-len (pageData))
        self.data["%d/%d" % (ino, lastPage)]= pageData
      # ... data  |0000|
      # ... | lastPage | ... | page |
      #                          ^ end

      # now fill the pages gap, starting from the next one to the last
      # till the previus one to the wanted page
      i= lastPage+1
      while i<page:
        self.master.fblocks-= 1
        if self.master.fblocks==0:
          return -ENOSPC
        # self.debug (1, 'added page %d' % i)
        self.data["%d/%d" % (ino, i)]= "\0"*consts.pageSize
        # decrease free count
        i+= 1
      # ... data  |000000...0|
      # ... | lastPage | ... | page |
      #                          ^ end
      # decrease free count
      self.master.fblocks-= 1
      # self.debug (1, 'filling up page: -> %d' % end)
      self.data["%d/%d" % (ino, page)]= "\0"*end
    elif page<=lastPage:
      # ...            data  |
      # ... | page | ... | lastPage |
      #           ^ end
      if shrink:
        # self.debug (1, 'shrinking')
        i= lastPage
        while i>page:
          try:
            del self.data["%d/%d" % (ino, i)]
            # self.debug (1, 'del\'ed page %d' % i)
          except KeyError:
            # self.debug (1, 'page %d not present for deletion' % i)
	    pass
          # increase free count
          self.master.fblocks+= 1
          i-= 1
        # self.debug (1, 'done sh\'k\'n')

      try:
        pageData= self.data["%d/%d" % (ino, page)]
      except KeyError:
        pageData= ''
        # decrease free count
        self.master.fblocks-= 1
      pageLen= len(pageData)
      if pageLen>end and shrink:
        # ...  data  |
        # ... | page | ... | lastPage |
        #           ^ end
        pageData= pageData[:end]
      else:
        # ... data |
        # ... | page | ... | lastPage |
        #           ^ end
        pageData+= "\0"*(end-pageLen)
      # self.debug (1, 'somehting\'ing page: %d-> %d' % (pageLen, end))
      self.data["%d/%d" % (ino, page)]= pageData
      # ...  data |
      # ... | page |
      #           ^ end

    # modify size
    if (shrink and size<fileSize) or size>fileSize:
      # self.debug (1, 'change size: %d-> %d' % (fileSize, size))
      self.size (ino, size)

    return size

  def write (self, ino, off, data):
    # profiling
    # return len(data)
    # self.debug (2, "writing in %d @ %d, size %d" % (ino, off, len(data)))
    bytesToWrite= len (data)
    totalBytesWrote= 0
    self.trunc (ino, off, False)
    while bytesToWrite:
      #   start   end
      #       |   |
      #       v   v
      # ... | page | ...
      (page, start)= divmod (off, consts.pageSize)
      end= min (consts.pageSize, start+bytesToWrite)

      # self.debug (2, "o %d; btw %d; p %d[%d..%d]" % (off, bytesToWrite, page, start, end))

      # get the page we'll be writing to
      try:
        pageData= self.data["%d/%d" % (ino, page)]
      except KeyError:
        # decrease free count
        self.master.fblocks-= 1
        if self.master.fblocks==0:
          return -ENOSPC
        # self.debug (2, 'new page %d' % page)
        pageData= ''
      pageLen= len(pageData)

      # write
      bytesWrote= end-start
      # self.debug (2, ">%s<" % pageData)
      # self.debug (2, "page: %d, start: %d, bytesToWrite: %d, bytesWrote: %d, end: %d, page[->]: >%s<, data[-]: >%s<, page[<-]: >%s<" %
      #                  (page, start, bytesToWrite, bytesWrote, end, pageData[:start], data[:bytesWrote], pageData[start+bytesWrote:pageLen]))
      pageData= pageData[:start]+data[:bytesWrote]+pageData[start+bytesWrote:pageLen]
      # self.debug (2, ">%s<" % pageData)
      self.data["%d/%d" % (ino, page)]= pageData

      # adjust indexes and remaining data
      data= data[bytesWrote:]
      bytesToWrite-= bytesWrote
      totalBytesWrote+= bytesWrote
      off+= bytesWrote

      # update ino size
      fileSize= self.size (ino)
      if off>fileSize:
        fileSize= self.size (ino, off)
    # for equalization in tests w/ adversaries
    # self.data.sync ()
    # self.meta.sync ()
    return totalBytesWrote

  def lock (self, ino, creating=False):
    error= -ENOENT
    # self.locks.acquire ()
    # if not self.locks.has_key (ino):
      # create lock
      # self.locks[ino]= CLock ()
    # get lock on ino
    # self.locks[ino].acquire ()
    exists= self.hasInode (ino)
    if (exists and not creating) or (not exists and creating):
      error= 0
    else:
      if exists and creating:
        error= -EEXIST
      # else -ENOENT
      # self.unlock (ino)
    # self.locks.release ()
    return error

  def unlock (self, ino):
    error= -ENOENT
    if self.hasInode (ino):
      error= 0
      # self.locks.acquire ()
      # count= self.locks[ino].release ()
      # if not count:
        # del self.locks[ino]
      # self.locks.release ()
    return error

  def sync (self):
    self.masterLock.acquire ()
    self.debug (1, 'sync')

    self.data.acquire ()
    self.data.sync ()
    self.data.release ()

    self.meta.acquire ()
    self.meta.sync ()
    self.meta.release ()

    self.masterLock.release ()

  #############
  # dir methods
  #############
  def mkdir (self, ino, parent):
    # decrease free counts
    self.master.fblocks-= 1
    self.dirContents (ino, [])
    # completeness
    self.link (ino, '.', ino, True, False)
    # link already adds the name to the list above
    self.link (ino, '..', parent, True, False)

  def rmdir (self, ino):
    error= -ENOTEMPTY
    # delete both ino and all ino/child... in reverse order, obv.
    children= self.dirContents (ino)
    if len (children)==2:
      for child in children:
        key= "%d/%s" % (ino, child)
        del self.data[key]
      # now ino...
      del self.data["%d" % ino]
      # and metadata
      del self.meta["%d" % ino]
      # dec file count
      self.master.ufiles-= 1
      # inc free counts
      self.master.fblocks+= 1

  def link (self, dirIno, fileName, fileIno, inc, over):
    self.debug (1, 'linking %d:%s:%d' % (dirIno, fileName, fileIno))
    error= -EEXIST
    key= "%d/%s" % (dirIno, fileName)
    if not self.data.has_key (key) or over:
      # add it if it's no there
      list= self.dirContents (dirIno)
      list.append (fileName)
      self.dirContents (dirIno, list)
      self.data[key]= str(fileIno)

      if inc:
        # inc link count
        stat= self.stat (dirIno)
        stat[consts.statNlink]+= 1
        stat= self.stat (dirIno, stat)

      error= 0
    return error

  def unlink (self, dirIno, fileName, dec):
    error= -ENOENT
    key= "%d/%s" % (dirIno, fileName)
    if self.data.has_key (key):
      # bye bye
      del self.data[key]
      # and remove it from the list
      list= self.dirContents (dirIno)
      # no checks; the try catches it
      try:
        list.remove (fileName)
        self.dirContents (dirIno, list)

        if dec:
          # dec link count
          stat= self.stat (dirIno)
          stat[consts.statNlink]-= 1
          stat= self.stat (dirIno, stat)

        error= 0
      except:
        # ENOENT
        pass
    return error

  def lookup (self, dirIno, fileName):
    """
      if there's an entry w/ that name, return the inode
    """
    key= "%d/%s" % (dirIno, fileName)
    if self.data.has_key (key):
      ans= int(self.data[key])
    else:
      ans= None
    return ans

  def dirContents (self, ino, contents=None):
    if not contents==None:
      self.data["%d" % ino]= csvPrettyPrint (contents)
      ans= contents
    else:
      ans= csvParse (self.data["%d" % ino])
    return ans

  #######
  # misc
  #######
  def emp (self):
    self.masterLock.acquire ()

    self.data.close ()
    self.data.release ()
    self.meta.close ()
    self.meta.release ()
    self.rmDB ()

    self.mkDB ()
    self.data.acquire ()
    self.meta.acquire ()

    self.masterLock.release ()

  def fragments (self, ino):
    """
      How much pages does ino have allocated.
    """
    # for size==0 return 0
    # for sizes E (1..pageSize) return 1
    # and so forth
    size= self.size (ino)
    fragments= (size+consts.fragmentSize-1)/consts.fragmentSize
    self.debug (2, "fragments: %d, size: %d" % (fragments, size))
    return fragments

  def usedBlocksAndFiles (self):
    files= 0
    blocks= 0

    self.meta.acquire ()
    # sometimes I just hate exceptions...
    try:
      key= self.meta.first ()[0]
    except KeyError:
      key= None
    while key and not self.master._terminate:
      self.debug (1, 'found key %s' % key)
      files+= 1
      blocks+= self.fragments (key)

      try:
        key= key= self.meta.next ()[0]
      except KeyError:
        key= None
    self.meta.release ()

    return (blocks, files)
