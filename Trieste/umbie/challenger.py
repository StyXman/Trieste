###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from threading import Thread
from socket import socket, AF_INET, SOCK_DGRAM
from select import select

from Trieste.common.utils import debugPrint, csvPrettyPrint
from Trieste.common.object import Object
from Trieste.common import consts

class Challenger (Thread, Object):
  # TODO: openslp support?
  def __init__ (self, navel):
    Thread.__init__ (self)
    Object.__init__ (self)
    self.socket= socket (AF_INET, SOCK_DGRAM)
    self.socket.bind (('', consts.chalPort))
    self.navel= navel

  def run (self):
    while not self.navel._terminate:
      i= select ([self.socket],[],[], 5)[0]
      if len (i)>0:
        (data, client)= self.socket.recvfrom (1024)
        debugPrint (1, '%s shouted %s!' % (client, data))
        self.socket.sendto (csvPrettyPrint ([self.navel.params ()]), client)
      else:
        self.debug (5, 'chal timeout!')

    self.socket.close ()
    self.debug (1, 'finished')
