###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from time import strftime, time, localtime
from zlib import compressobj
import sys
import gzip

from Trieste.common.utils import getCaller

class GzipFile (object):
  def __init__ (self, fileName, mode='r'):
    self.file= file (fileName+'.gz', mode)
    self.gzip= compressobj (9)

  def write (self, s):
    self.file.write (self.gzip.compress (s))

  def close (self):
    self.file.write (self.gzip.flush ())
    self.file.close ()

class Debugger (object):
  def __init__ (self, fileName=None, compressed=True):
    if fileName:
      if compressed:
        # self.__file= GzipFile (fileName, 'w+', 9)
        self.__file= gzip.open (fileName+'.gz', 'w+', 9)
      else:
        self.__file= file (fileName, 'w+')
    else:
      self.__file= None
    self.__log= []

  def __line (self, s):
    now= time ()
    return "%20.6f: %s\n" % (now, s)

  def log (self, s):
    # line= self.__line (s)
    # self.__log.append (line)
    # self.__file.write (line)
    self.debug (1, s)

  def debug (self, i, s, level=1, fast=True):
    if i==1 or i==5:
      now= time ()
      if fast:
        sys.stderr.write (self.__line (s))
      else:
        (theClass, theMethod, theFileName, theLineNo)= getCaller (level)
        methodStr= "%s.%s()" % (theClass, theMethod)
        sys.stderr.write ("%s [%3d] @ %s.%s: %s\n" % (
          methodStr.ljust (20),
          theLineNo,
          strftime ("%H:%M:%S", localtime (now)),
          str (round (now-int(now), 4))[2:].ljust (4),
          str(s),
        ))

  def saveLog (self):
    return
    if self.__file:
      self.debug (1, 'saving')
      for line in self.__log:
        self.__file.write (line)
      self.__file.close ()

class Object (object):
  debugger= None
  def __init__ (self, fileName=None, compressed=True):
    if not Object.debugger:
      Object.debugger= Debugger (fileName, compressed)
      self.debug (1, 'o: logging in %s' % fileName)
    else:
      # self.debug (1, 'debugger already there')
      pass

  def log (self, s):
    if self.debugger:
      self.debugger.log (s)

  def debug (self, i, s, level=1, fast=True):
    if self.debugger:
      self.debugger.debug (i, s, level, fast)

  def saveLog (self):
    if self.debugger:
      self.debugger.saveLog ()
