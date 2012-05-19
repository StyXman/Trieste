###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from socket import socket, AF_INET, SOCK_STREAM, error, SOL_SOCKET, IPPROTO_TCP, TCP_NODELAY
from select import select
from time import sleep
from traceback import print_tb, print_stack
from types import *
from errno import *
import sys

from Trieste.common.utils import chomp, csvParse, csvPrettyPrint, UmbDead, debugLog
from Trieste.common.object import Object
from Trieste.common import consts

class RequestSocket (Object):
  def __init__ (self, sock=None, **options):
    Object.__init__ (self)
    if sock:
      self._socket= sock
    else:
      self._socket= socket (AF_INET, SOCK_STREAM)
    self._socket.setsockopt (IPPROTO_TCP, TCP_NODELAY, True)
    # set extra options as passed
    for option in options.keys():
      self.debug (1, 'setting option %d' % option)
      self._socket.setsockopt (option, options[option])
    self.debug (1, 'created ReqSock [%d, %s]' % (self.fileno (), str(self.getSockName()[1])))
    self._connected= False

  def __str__ (self):
    if self._connected:
      string= "%s:%d<-->%s:%d" % (self.getSockName()+self._socket.getpeername ())
    else:
      string= "unconnected ReqSock %d" % self.fileno ()
    return string

  def connect (self, params):
    self.debug (1, 'connecting w/ %s,%s' % params)
    self._socket.connect (params)
    self.debug (1, 'ReqSock %d connected thru port %s' % (self.fileno (), str(self.getSockName()[1])))
    self._connected= True

  def fileno (self):
    return self._socket.fileno ()

  def getSockName (self):
    return self._socket.getsockname ()

  def readPoll (self):
    """
      Tries to read a line from the file.
      If it timeouts, returns None.
      If it fails (EOF) return [].
      Otherwise, returns the data read once eval()'ed.
    """
    # self.debug (1, '[%d]<-- reading...' % self.fileno (), 2)
    args= None
    try:
      i= select ([self.fileno ()], [], [], 5)[0]
      # self.debug (1, '[%d]<-- selected...' % self.fileno (), 3)
      if len (i)>0:
        # self.debug (5, '[%d]<-- loading...' % self.fileno (), 4)
        # self.log ('[%d]<-- reading...' % self.fileno ())

        size= self.readData (8)
        # self.debug (2, 'about to read >%s< bytes' % size)
        size= int(size)
        line= self.readData (size)

        # line= self._file.readline ()
        # line= chomp (line)
        # self.log ('[%d]<-- read' % self.fileno ())
        if line:
          args= csvParse (line)
        else:
          # EOF
          args= []

        # using pickles (blej!)
        # args= load (self._file)
        # args= load (self._socket)

        # self.log ("[%d]<-- %s" % (self.fileno (), args))
        self.debug (1, "[%d]<-- %s" % (self.fileno (), args))
      else:
        # self.debug (2, 'timeout!')
        pass
    except Exception, e:
      raise UmbDead

    return args

  def read (self):
    """
      reads blockingly from the socket and parses the data into a list
      returns: args
        if args==None, nothing read, socket's dead or closed or something.
        else, args is a list with whatever came down the line.
        if that list is empty, then the other side closed.
    """
    args= None
    try:
      # self.log ('[%d]<-- loading...' % self._socket.fileno ())
      size= self.readData (8)
      if len (size)==8:
        size= int(size)
        line= self.readData (size)
        # self.log ('[%d]<-- read' % self.fileno ())
        args= csvParse (line)
      else:
        # EOF
        args= []

      # self.log ("[%d]<-- %s" % (self._socket.fileno (), args))
      self.debug (1, "[%d]<-- %s" % (self.fileno (), args))
    except Exception, e:
      # self.debug (5, 'exception %s' % e)
      # self.debug (5, '[%d] dead!' % (self._socket.fileno ()))
      raise UmbDead

    return args

  def readData (self, size):
    """
      raw data reading
    """
    # self.debug (2, '[%d]reading %d bytes of data...' % (self.fileno (), size))
    data= ''
    readBytes= 0

    recvd= None
    while size>0 and (recvd==None or len (recvd)>0):
      recvd= self._socket.recv (size)
      # self.debug (2, 'read %d' % len (recvd))
      data+= recvd
      readBytes+= len (recvd)
      size-= len (recvd)

    # self.debug (2, '[%d]done.' % self.fileno ())
    if len (recvd)==0:
      # closed
      # self.debug (1, 'may be short read: >%s<' % data)
      data= ''
    # self.debug (2, "[%d]<-- %d:>%s<" % (self.fileno (), len (data), data))
    # assert (size==0 or len (recvd)==0)
    return data

  def write (self, what, data=None):
    """
      what should already be the list
      self.debugs the text and writes it to the file, appending a newline at the end.
      returns: naught
    """
    # self.log ("[%d]--> writing" % (self._socket.fileno ()))
    # self.debug (1, "[%d]--> writing" % (self._socket.fileno ()))
    what= csvPrettyPrint (what)
    self.log ("[%d]--> %s" % (self._socket.fileno (), what))
    size= str(len (what)).rjust (8)
    # add it after, so the command len is right
    if data:
      what+= data
    self.writeData (size+what)
    # self.log ("[%d]--> dumped" % (self._socket.fileno ()))

  def writeData (self, data):
    """
      raw data writing
    """
    # self.debug (2, "[%d]--> %d:%s" % (self._socket.fileno (), len (data), data))
    # self.debug (2, '[%d]writing %d bytes of data...' % (self._socket.fileno (), len (data)), 3)
    size= len (data)
    wroteBytes= 0
    while size>0 and wroteBytes>=0 and wroteBytes<size:
      wrote= self._socket.send (data)
      # self.debug (2, 'wrote %d' % wrote, 2)
      data= data[wrote:]
      wroteBytes+= wrote
      size-= wrote
    # self.debug (2, "[%d]dumped" % (self._socket.fileno ()))

  def close (self):
    self.debug (1, 'reqsock: close!', fast=False, level=4)
    # print_tb (sys.exc_info()[2])
    # print_stack ()
    self._connected= False
    # kick some ass...
    try:
      # self._socket.shutdown (2)
      self._socket.close ()
    except:
      # WTF now?
      pass
