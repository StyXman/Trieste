###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_LINGER
from select import select
from struct import pack

from Trieste.common.object import Object

class ServerLoop (Thread, Object):
  def __init__ (self, port, master):
    Thread.__init__ (self)
    Object.__init__ (self)
    self._master= master
    self._socket= socket (AF_INET, SOCK_STREAM)
    self._socket.setsockopt (SOL_SOCKET, SO_LINGER, pack ("ii", 1, 0))
    # sorry, but *nothing* should be done before the Thread.__init__ (???)
    # Thread.__init__ (self, "ServerLoop in %d" % self._socket.fileno ())
    # '' means INADDR_ANY
    self._socket.bind (('', port))
    self._socket.listen (10)
    self.debug (1, 'ServerLoop created')

  def run (self):
    self.debug (1, 'ServerLoop is running!')
    while not self._master._terminate:
      i= select ([self._socket],[],[], 5)[0]
      if len (i)>0:
        (client, name)= self._socket.accept ()
        self.debug (1, "incoming call from %s; please wait" % str(name))
        self._master._peers.addServer (client)
        # don't close the socket 'cause we're on threads, not forks...
        # but we can decrement de refcount erasing client
        client= None

    self._socket.close ()
    self.debug (1, 'finished')
