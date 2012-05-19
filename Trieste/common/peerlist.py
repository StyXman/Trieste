###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from threading import RLock
from types import StringType

from Trieste.common.utils import random, next
from Trieste.common.stubnavel import StubNavel
from Trieste.common.consts import Normal
from Trieste.common.stubvice import StubVice
from Trieste.common.stubvirtue import StubVirtue
from Trieste.common.requestsocket import RequestSocket
from Trieste.common.url import URL, NoParse
from Trieste.common.object import Object

class PeerList (Object):
  def __init__ (self, master):
    Object.__init__ (self)
    self._peersLock= RLock ()
    self._navels= {}
    self._vices= {}
    self._virtues= {}
    self.__proto= {
      'umbie': self._navels,
      'vice': self._vices,
      'virtue': self._virtues,
    }
    self._master= master

  def acquire (self):
    self.debug (2, "locking peers", level=2, fast=False)
    self._peersLock.acquire ()
    self.debug (2, "done l")

  def release (self):
    self.debug (2, "unlocking peers", 2)
    self._peersLock.release ()

  def addPeer (self, url, key, kind=Normal):
    """
      adds a peer if it's not already there.
      the url should not be already parsed and the key should be in the proper format
      returns: naught
    """
    self.debug (2, 'adding peer %s' % url, 2)
    self.acquire ()
    purl= URL (url)
    proto= purl.proto ()
    if proto=='umbie':
      if not self._navels.has_key (key):
        self._navels[key]= StubNavel (self._master, url, key, kind)
      else:
        # change the kind
        self._navels[key].setKind (kind)
    elif proto=='vice' and not self._vices.has_key (key):
      self._vices[key]= StubVice (self._master, url, key)
    elif proto=='virtue' and not self._virtues.has_key (key):
      self._virtues[key]= StubVirtue (self._master, url, key)
    else:
      # bark!
      self.debug (2, 'bark! >%s<' % proto)
      pass
    self.release ()

  def delPeer (self, peer):
    url= URL (peer.url ())
    key= peer.key ()
    h=  self.__proto[url.proto ()]
    self.acquire ()
    if h.has_key (key):
      self.debug (2, '%s' % h, fast=False, level=5)
      self.debug (2, 'deleting %s: %s, %s' % (peer, url, key), fast=False, level=4)
      self.debug (1, 'deleting %s: %s, %s' % (peer, url, key))
      del h[key]
      self.debug (2, '%s' % h, fast=False, level=3)
    self.release ()

  def getNavel (self, url, key, kind=Normal):
    self.acquire ()
    if type(url)!=StringType:
      url= str(url)
    # addPeer already takes care of dupes
    self.addPeer (url, key, kind)
    peer= self._navels[key]
    self.release ()
    return peer

  def getVice (self, url):
    self.acquire ()
    # addPeer already takes care of dupes
    if type(url)!=StringType:
      url= str(url)
    self.addPeer (url, url)
    peer= self._vices[url]
    self.release ()
    return peer

  def getVirtue (self, url):
    self.acquire ()
    # addPeer already takes care of dupes
    if type(url)!=StringType:
      url= str(url)
    self.addPeer (url, url)
    peer= self._virtues[url]
    self.release ()
    return peer

  # 'client' in this context means a incoming call
  def addServer (self, client):
    # this server answers to that client
    peer= None
    server= None
    # this ReqSock will be thrown away.
    socket= RequestSocket (client)
    socket.write (['hit here'])

    args= socket.read ()
    self.debug (1, "args are: %s" % str(args))
    what= next (args)
    if what:
      if what=='i am':
        try:
          url= args[0]
          self.debug (1, "%s" % url.__class__)
          if not isinstance (url, URL):
            url= URL (url)
          proto= url.proto ()
          if proto=='umbie':
            key= int (args[1])
            peer= self.getNavel (str(url), key)
          elif proto=='vice':
            peer= self.getVice (str(url))
          elif proto=='virtue':
            peer= self.getVirtue (str(url))
          else:
            # bark!
            pass
        except NoParse:
          socket.write (['bye'])
          socket.close ()
      else:
        socket.write (['bye'])
        socket.close ()

    if peer:
      socket.write (['ok'])
      # create a Server of the correct class
      # as defined in serverType
      # TODO: I could pass the ReqSock() instead of the socket()
      server= self._master._serverType (self._master, client)
      # this server is the one answering to that client
      peer.setServer (server)
      server.start ()
    else:
      self.debug (1, 'no peer!')
    self.debug (1, 'server %s added' % peer)

  def delNavel (self, key):
    self.acquire ()
    try:
      # why break OO design?!?
      del self._navels[key]
    except KeyError:
      pass
    self.release ()

  def delServer (self, server):
    url= server.url ()
    key= server.key ()
    proto= url.proto ()
    if proto=='umbie':
      navel= self.getNavel (str(url), key)
      navel.delServer ()
    elif proto=='vice':
      pass
    elif proto=='virtue':
      pass
    else:
      # bark!
      pass

#   def delClient (self, key):
#     try:
#       peer= self._peers[key]
#       peer.createEmptyClient ()
#     except KeyError:
#       # the client didin't exist
#       pass

  def getAuthNavel (self, key):
    self.acquire ()

    keys= self._navels.keys ()
    keys.sort ()
    if keys:
      peer= self._navels[keys[-1]]
      # this could be done better w/ a while
      for k in keys:
        if k<=key:
          peer= self._navels[k]
    else:
      peer= None
      self.debug (1, 'no fscking navel!')

    self.release ()
    return peer

  def getSuccNavel (self, key):
    self.acquire ()

    keys= self._navels.keys ()
    keys.sort ()
    peer= self._navels[keys[-1]]
    # this could be done better w/ a while
    for k in keys:
      if k>key:
        peer= self._navels[k]
    # fuck
    if peer.key()==key:
      # no bigger guy, so let's take the first one
      peer= self._navels[keys[0]]

    self.release ()
    return peer

  def getRandomNavel (self):
    self.acquire ()
    keyList= self._navels.keys ()
    size= len (keyList)
    index= random(size)
    peer= self._navels[keyList[index]]
    self.release ()
    return peer

  def navels (self):
    self.acquire ()
    # assignmend only copies reference
    navels= self._navels.copy ()
    self.release ()
    return navels

  def vices (self):
    self.acquire ()
    # assignmend only copies reference
    self.debug (2, 'navels: %s' % str(self._navels))
    self.debug (2, 'vices: %s' % str(self._vices))
    vices= self._vices.copy ()
    self.release ()
    return vices

  def getRandomVice (self):
    self.acquire ()
    keyList= self._vices.keys ()
    size= len (keyList)
    index= random(size)
    peer= self._vices[keyList[index]]
    self.release ()
    return peer
