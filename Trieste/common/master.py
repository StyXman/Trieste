###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST
from select import select
from time import sleep
from signal import SIGTERM, signal

from Trieste.common.object import Object
from Trieste.common.utils import random, next, coBetween, UmbDead, csvParse
from Trieste.common.url import URL
from Trieste.common.peerlist import PeerList
from Trieste.common.serverloop import ServerLoop
from Trieste.common.navelclient import NavelClient
from Trieste.common.ring import Ring
from Trieste.common import consts

class Master (Object):
  """
    Warning: Abstract class.
    subclasses should at least define self._addClient hash (see run)
    and never reimplement periodic withiout calling this class' one
  """
  Set= 0
  Complement= 1

  def __init__ (self, url=None, key=None, column=None, fileName=None):
    Object.__init__ (self, fileName=fileName, compressed=False)
    self.debug (1, 'm: logging in %s' % fileName)
    self._key= key
    self._url= None
    self._loop= None

    self._peers= PeerList (self)
    self._terminate= False
    # the class of the individual servers.
    self._serverType= None
    self._ring= Ring (self)

    self._data= None
    self._timeout= None

    # gotta join the clients after our servers died
    # so I keep a list and join them in the periodic function
    self._threadsToJoin= []
    if url:
      self.setUrl (url)

  def setUrl (self, url):
    if url:
      self._url= URL (url)
      self.debug (1, 'url: %s' % self._url)
      self.debug (1, 'building server loop')
      self._loop= ServerLoop (self._url.port (), self)
      self._loop.start ()

  def init (self):
    # do not allow fast update
    self._timeout= random (consts.periodicTimeOut)+5
    self.debug (1, "timeout: %d" % (self._timeout))

  def url (self):
    return self._url

  def key (self):
    return self._key

  def peers (self):
    return self._peers

  def navels (self):
    navels= self._peers.navels ()
    return navels

  def vices (self):
    vices= self._peers.vices ()
    return vices

  def delServer (self, server):
    """
      Adds a finished server to the list of threads to join,
      and removes it from the known peers.
    """
    self.debug (1, "queuing to join %s" % server)
    # the client thread cannot join itself, so we do it later
    self._threadsToJoin.append (server)
    self.debug (2, "done q.")
    self._peers.delServer (server)
    # do other stuff that keeps _pred and _succ up-to-date

  def delPeer (self, peer):
    self.debug (1, 'deleting %s' % peer)
    self._peers.delPeer (peer)
    peer.close ()

  def discover (self, net, skip=None):
    """
      broadcasts messages for discovering the peers
      returns: the peer to which we should connect to.
    """
    shouter= socket (AF_INET, SOCK_DGRAM)
    # set socket option
    shouter.setsockopt (SOL_SOCKET, SO_BROADCAST, 1)
    server= None

    # we need to be root and a default gw here!
    # shouter.sendto ('any body there?', ('<broadcast>', consts.chalPort))
    # no if we broadcast the net only...
    self.debug (1, 'Ping %s' % net)
    shouter.sendto ('any body there?', (net, consts.chalPort))
    # wait for answers
    sleep (consts.shoutTimeOut)
    # now wait for at least one

    # but let things go on in the case the shout was not heard
    # nope, navels that doesn't find others should start their own ring

    # but vices should wait till they find one,
    # so navels and vices do different things

    i= select ([shouter],[],[], 0.1)[0]
    # collect *any* answer
    while len(i)>0:
      ans= csvParse (shouter.recv (1024))
      self.debug (1, 'found %s' % ans)
      (url, key)= ans[0]
      new= self._peers.getNavel (url, key)
      if skip:
        if new!=skip:
          server= new
      else:
        server= new
      i= select ([shouter],[],[], 0.1)[0]

    self.debug (1, 'returning %s' % server)
    return server

  def gossip (self, peer):
    try:
      (navels, vices)= peer.getKnownPeers ()
      self.debug (1, "from %s got peer list : %s" % (peer, navels))

      self.updatePeers (navels, vices)
      for viceUrl in vices:
        try:
          vice= self._peers.getVice (viceUrl)
          vice.updateStats ()
        except:
          self.delPeer (vice)
    except:
      self.delPeer (peer)

  def updatePeers (self, navels, vices):
    for navelUrl, navelKey in navels:
      self._peers.addPeer (navelUrl, navelKey)
    for viceUrl in vices:
      # for testing now
      vice= self._peers.getVice (viceUrl)

  def getNavelKey (self, url):
    # create a temp client and ask for the key...
    server= NavelClient (url, self)
    key= None
    while not key:
      try:
        key= server.key ()
        server.close ()
      except UmbDead:
        # a connection refused
        sleep (5)
        # should we 'timeout' and create our own ring?

    return key

  def giveData (self, m, n, what=Set):
    """
      returns: a hash
    """
    self.debug (1, "giveData called", 2)

    keys= self._data.keys ()
    keys.sort ()
    self.debug (1, 'my know keys are: %s' % keys)
    h= {}

    nextKey= next (keys)
    while not nextKey==None:
      self.debug (2, "m: %d, k: %d, n: %d" % (m, nextKey, n))
      if (what==self.Set and coBetween (m, nextKey, n)) or (what==self.Complement and coBetween (n, nextKey, m)):
        h[nextKey]= self._data.getValues (nextKey)

      nextKey= next (keys)

    if what==self.Set:
      self.debug (1, 'giving Set %d:%d %s' % (m, n, h.keys ()))
    else:
      self.debug (1, 'giving Complement %d:%d %s' % (n, m, h.keys ()))
    return h

  def ident (self):
    raise NotImplementedError

  ############
  # actual run
  ############
  def catchKill (self, signo, stackFrame):
    self.debug (1, "SIGTERM caught; terminating and sync'ing")
    try:
      self._data.sync ()
    except:
      pass
    self._terminate= True

  def periodic (self):
    self.joinServers ()

  def joinServers (self):
    # join the servers that were attending clients who quited
    for thread in self._threadsToJoin:
      self.debug (1, "thread.join()'ing %s" % thread)
      self._threadsToJoin.remove (thread)
      thread.join ()

  # 'main' loop: this is cron
  def run (self):
    # set the handler of sigterm
    signal (SIGTERM, self.catchKill)
    count= self._timeout

    while not self._terminate:
      try:
        if count<consts.periodicUTimeOut:
          self.debug (2, 'short uSleep')
          sleep (count)
          self.periodic ()
          count= self._timeout
        else:
          self.debug (2, 'long uSleep')
          sleep (consts.periodicUTimeOut)
          count-= consts.periodicUTimeOut
      except KeyboardInterrupt:
        self.debug (1, "SIGTERM caught; terminating")
        self._terminate= True

    self.stop ()

  def terminate (self):
    self.debug (1, "terminating...")
    self._terminate= True

  def stop (self):
    # end of the game
    self.debug (1, "join'ing server loop...")
    self._loop.join ()
    self.debug (1, "main finishing...")
    # self._clients.joinThem ()
    self.joinServers ()
    self.debug (1, "finished!")
