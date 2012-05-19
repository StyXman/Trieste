###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from socket import error
from threading import RLock
from types import ListType
from traceback import print_stack

from Trieste.common.url import URL
from Trieste.common.utils import chomp, UmbDead
from Trieste.common.requestsocket import RequestSocket
from Trieste.common.object import Object

class Client (Object):
  """
    generic client
    it's blocking. 'not responding, still trying'?
  """
  def __init__ (self, url, master=None):
    Object.__init__ (self)
    self.debug (1, "Client: %s" % (url))
    self._url= URL (url)
    self._dead= False
    self._connected= False
    self._lock= RLock ()
    self._socket= None
    self._master= master

  def __del__ (self):
    try:
      self.close ()
    except:
      # just in case __init__ didn't run completely
      pass

  def url (self):
    return self._url

  def ident (self):
    data= self._socket.getSockName ()
    self.write (["i am", "virtue://%s:%d/" % data])
    ans= self.read ()

  def read (self):
    return self._socket.read ()

  def readData (self, size):
    return self._socket.readData (size)

  def write (self, what, data=None):
    self._socket.write (what, data)

  def writeData (self, data):
    return self._socket.writeData (data)

  def ask (self, what, data=None):
    """
      what should already be a list with message and params
    """
    self._lock.acquire ()
    try:
      if not self._connected:
        # TODO: move this to a method
        # stablish connecton
        self._socket= RequestSocket (None)
        self.debug (2, "urlParams: %s %s" % self._url.getParams ())
        self._socket.connect (self._url.getParams ())
        self.debug (1, "created Client socket w/ fd %d to %s" % (self._socket.fileno (), self._url))
        # throw away the greeting
        ans= self.read ()
        self._connected= True
        # identify ourselves so the server knows what are we.
        self.ident ()

      if not type (what)==ListType:
        self.debug (1, "what's not a list!: %s" % str (what))
      self.write (what, data)

      data= self.read ()
      self._lock.release ()

      if not data==None:
        return data
      else:
        self.debug (1, "dead!: closed")
        self._dead= True
        self.close ()
        raise UmbDead

    # other errors?
    except (ValueError, IOError, error), e:
      self.debug (1, "dead!: %s" % e)
      self._dead= True
      self._lock.release ()
      self.close ()
      raise UmbDead

  def close (self):
    if self._connected:
      try:
        self.write (['quit'])
        # throw away the greeting
        self._socket.read ()
        self.debug (1, "closing [%d]" % self._socket.fileno ())
        self._socket.close ()
      except:
        pass
      self._connected= False
