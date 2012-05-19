###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from threading import Thread
from traceback import print_exception
from socket import SO_LINGER
from struct import pack
import sys

from Trieste.common.utils import chomp, UmbDead, next
from Trieste.common.requestsocket import RequestSocket
from Trieste.common.object import Object

class Server (Thread, Object):
  """
    serves only one client, another Navel out there or a Virtue or a Vice.
  """
  def __init__ (self, master, client):
    Thread.__init__ (self)
    Object.__init__ (self)
    self._dead= False
    self._master= master
    # wrap the client (which is a socket())
    # in a RequestSocket.
    self._socket= RequestSocket (client)
    self._clientName= self._socket.getSockName ()
    self.finished= False
    self.setName (str (self))

  def __str__ (self):
    try:
      s= "[%d] %s:%s" % ((self.fileno (),)+self._clientName)
    except:
      s= "%s:%s (closed)" % self._clientName
    return s

  def url (self):
    return self._master.url ()

  def key (self):
    return self._master.key ()

  def fileno (self):
    return self._socket.fileno ()

  def read (self):
    return self._socket.readPoll ()

  def readData (self, size):
    return self._socket.readData (size)

  def write (self, what):
    self._socket.write (what)

  def writeData (self, data):
    self._socket.writeData (data)

  def close (self):
    self.debug (1, 'server: close!', fast=False, level=2)
    self._socket.close ()
    self.finished= True

  def run (self):
    """
      main loop that should take care of from-the-bottom termination.
      returns: once the client has quited.
    """
    try:
      args= self.read ()
      # main loop quited or EOF
      self.finished= self._master._terminate or args==[]
      while not self.finished:
        if args:
          # it might not read anything
          try:
            what= next (args)
            self.finished= self.attend (what, args)
          except:
            (e, v, tb)= sys.exc_info ()
            self.debug (5, 'exception caugh in server: %s' % e)
            print_exception (e, v, tb)
            self.debug (5, '---')
            self.write (['error'])
            self.finished= False

        if not self.finished:
          args= self.read ()
          # recalculate finished condition
          # main loop quited or EOF
          self.finished= self._master._terminate or args==[]

    except:
      self.debug (5, 'exception caugh out server: %s' % e)
      (e, v, tb)= sys.exc_info ()
      print_exception (e, v, tb)

    # he quited, or terminated by main loop, remove ourselves from the system
    self._dead= True
    self.close ()
    self.debug (1, "dying")
    self._master.delServer (self)

  def attend (self, what, args):
    """
      note: please reimplement in subclasses!
      should recognize the request and answer it.
      returns: True if (the client has quit/the socket is broken)
    """
    return True
