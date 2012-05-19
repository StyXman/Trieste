###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from __future__ import nested_scopes

from Trieste.common.consts import Normal
from Trieste.common.utils import chomp, debugPrint, UmbDead
from Trieste.common.object import Object

def destroyingmethod (method):
  def closure (self, *args, **kwargs):
    try:
      method (self, *args, **kwargs)
    except UmbDead:
      self.destroy ()

class Stub (Object):
  """
    This class should represent anything we might need from a peer,
  """
  def __init__ (self, master, url, key):
    Object.__init__ (self)
    self._key= key
    # stores the Server to where this peer
    # (the remote one that this object represents)
    # is connected
    self._server= None
    # and this stores the Client
    self._client= None
    self._master= master
    self.debug (1, "Stub: %s" % (url))
    self._url= url
    self._key= key
    self._kind= None

    # I can build a client, because I have the data,
    # it does not connect till it's needed,
    # and because I wanna :)
    self.createEmptyClient ()

  def destroy (self):
    self.debug (1, 'destroying %s' % self)
    if self._client:
      self._client.close ()
    if self._server:
      self._server.finished= True
    self._master.delPeer (self)

  def url (self):
    return self._url

  def key (self):
    # the key is inmutable
    return self._key

  def params (self):
    return (self.url (), self.key ())

  def close (self):
    self._client.close ()

  def __repr__ (self):
    return "Stub: %s:%s" % self.params ()

  def setServer (self, server):
    self._server= server

  def delServer (self):
    self._server= None

  def setClient (self, client):
    self._client= client

  def createEmptyClient (self):
    raise NotImplementedError

  def getKnownPeers (self):
    [navelList, viceList]= self._client.ask (['known peers'])
    if self._kind==Normal:
      # hang up 'cause this is random.
      self.close ()
    return (navelList, viceList)
