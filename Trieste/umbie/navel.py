###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from threading import RLock, Lock
from time import sleep

from Trieste.common.url import URL
from Trieste.common.utils import chomp, random, UmbDead, ooBetween, ocBetween, coBetween
from Trieste.common.consts import Normal, Succ, Pred, maxIno
from Trieste.common.master import Master

from Trieste.umbie.umbdata import UmbData
from Trieste.umbie.navelserver import NavelServer
from Trieste.umbie.challenger import Challenger

class Navel (Master):
  def __init__ (self, url=None, column=0, fileName=None):
    # take care of repeated keys!
    key= random (maxIno)
    Master.__init__ (self, url, key, column, fileName=fileName)
    self._succ= None
    self._pred= None

    # thread support
    # RLock's; just in case
    self._succLock= RLock ()
    self._predLock= RLock ()

    self._serverType= NavelServer
    self._chal= None

    self._self= None
    self._prevSucc= None
    self._prevPred= None

  def __str__ (self):
    return "Navel %s" % self.url ()

  def init (self, net=None):
    Master.init (self)
    self._data= UmbData (self._key, self._key)
    self._self= self._peers.getNavel (self._url, self._key, Normal)

    if net:
      # create a challenger for new nodes and such
      self._chal= Challenger (self)
      self._chal.start ()

      # find a ring and join it or create a new one
      self.debug (1, 'ping')
      peer= self.discover (net, self._self)
      if peer==None:
        self.debug (1, "gave up! noone's here!")
        self.createRing ()
      else:
        self.join (peer)

  def amAuth (self, key):
    # ! someone should have the lock on succ
    m= self._key
    n= self.getSucc ().key ()
    if coBetween (m, key, n):
      return True
    else:
      return False

  def params (self):
    return (self._url, self._key)

  def getPred (self):
    pred= self._pred
    return pred

  def setPred (self, pred):
    self._predLock.acquire ()
    self.debug (1, "changing pred to %s" % pred)
    if self._pred:
      self._pred.setKind (Normal)
    self._pred= pred
    if self._pred:
      self._pred.setKind (Pred)
    self._predLock.release ()

  def getSucc (self):
    succ= self._succ
    return succ

  def setSucc (self, succ):
    self._succLock.acquire ()
    self.debug (1, "changing succ to %s" % succ)
    if self._succ:
      self._succ.setKind (Normal)
    self._succ= succ
    if self._succ:
      self._succ.setKind (Succ)
      self._data.resizeFree (succ.key ())
    self._succLock.release ()


  ###########
  # chord impl
  ###########
  def createRing (self, n=0):
    """
      creates a umb ring, setting our succ to ourself
      returns: naught
    """
    # the str is for the URL parser
    self.debug (1, 'creating ring')
    self.setSucc (self._peers.getNavel (self._url, self._key, Succ))
    self.addRandomData (n)
    self.debug (1, 'ring created')

  def findSucc (self, key):
    """
      simple key location
      returns: the peer
    """
    succ= self.getSucc ()
    if ocBetween (self.key (), key, succ.key ()):
      return succ
    else:
      # ask the next one
      self.debug (1, "asking %s about succ of %d" % (succ, key))
      (url, key)= succ.findSucc (key)
      # succ.close ()
      # add it to the known peer's list
      return self._peers.getNavel (url, key)

  def fastFindSucc (self, key):
    """
      scalable key location
      returns: the peer
    """
    succ= self.getSucc ()
    self.debug (1, "being asked about succ of %d" % (key))
    if succ and ocBetween (self.key (), key, succ.key ()):
      return succ
    else:
      try:
        # ask the closest one
        # WRONG: must find the closest one not connected (or something)
        # we can try to defer the realization of this new peer.
        # peer= self.findAuth (key)
        peer= self.findKnownSucc (key)
        if not peer==self._self:
          self.debug (1, "asking %s about succ of %d" % (peer, key))
          (url, key)= peer.findSucc (key)
          if peer.kind ()==Normal:
            peer.close ()
        else:
          self.debug (1, 'fallbacking to myself')
          (url, key)= self.params ()
          url= str(url)
        # add it to the known peer's list
        return self._peers.getNavel (url, key)
      except UmbDead:
        # that guy's dead! let's bury him!
        self._peers.delNavel (peer.key ())
        # and try again
        return self.fastFindSucc (key)

  def join (self, other):
    self.debug (1, "joining to %s" % other)
    # WTF?
    # self.pred= None
    self._pred= None

    self._prevSucc= self.getSucc ()
    try:
      (url, key)= other.findSucc (self.key ())
      peer= self._peers.getNavel (url, key)
      self.setSucc (peer)
      self.debug (1, "succ found %s, %s" % (url, key))
      self.debug (1, 'notifying w/ %s' % peer)
      if peer.notify (self.params ()):
        self.keypass ()
    except UmbDead:
      # that one's dead, rollback
      self.setSucc (self._prevSucc)
      self._peers.delNavel (key)
    self.debug (1, 'join finished')

  def keypass (self):
    succ= self.getSucc ()
    if not succ==self._self:
      # here we also pass to the new node its data
      peer= succ
      self.debug (1, 'got succ, giving data')
      given= self.giveData (self.key (), peer.key (), self.Complement)
      ans= peer.takeData (given)
      # iterate as the keys get rejected 'cause there's another auth
      ok= ans[0]
      while not ok:
        (url, key)= ans[1]
        self.debug (1, "redirect to: %s:%d" % (url, key))
        peer= self._peers.getNavel (url, key)
        if not peer==self._self:
          ans= peer.takeData (self.giveData (self.key (), peer.key (), self.Complement))
          ok= ans[0]

      # see keypass.txt
      pred= self.getPred ()
      if not pred:
        self.debug (1, 'no pred, succ.tellPredToForget ()')
        succ.tellPredToForget ()
      else:
        # try not to do stupid things
        # (i.e., don't tell ourselves to forget nor our new succ)
        # if not pred==self._self and not pred==succ:
        if not pred==succ:
          self.debug (1, '%s.forgetData (given.keys ())' % pred)
          # peer= pred
          pred.forgetData (given.keys ())
        else:
          self.debug (1, 'I wouldn\'t guess that this would happen. pred is: %s' % pred)
    if self._prevSucc:
      # close connection to the 'old' succ
      self._prevSucc.close ()

  def stabilize (self):
    """
      implements stabilize code of Chord's paper, fig 6
      with some error handling
      returns: naught
    """
    self.debug (1, "stab!")
    # * we must have a head to talk to
    succ= self.getSucc ()
    if succ:
      self._succLock.acquire ()
      self.debug (2, "stab-2!")
      try:
        (url, key)= succ.pred ()
        self.debug (1, "stab-3! key: %s" % str(key))
        # None,None means he has none
        if key and ooBetween (self.key (), key, succ.key ()):
          # save it for restoring on exception
          self._prevSucc= succ
          succ= self._peers.getNavel (url, key)
          self.debug (1, "stab-4!")
          self.setSucc (succ)
          self.debug (1, "stab-5!")
          try:
            # do not give data to ourselves
            self.debug (1, 'notifying w/ %s' % succ)
            if succ.notify (self.params ()):
              self.keypass ()
          except UmbDead:
            self.debug (1, "%s:%s's dead, Jim!" % (url, key))
            # self.delNavel (key)
            # this one's dead; restore the previous one
            self.setSucc (self._prevSucc)
            # should we notify the old one?
        else:
          # don't care about this
          self.debug (1, 'notifying w/ %s' % succ)
          succ.notify (self.params ())

      except UmbDead:
        self.debug (1, "%s's dead, Jim!" % (self._succ.key ()))
        # self.delNavel (self._succ.key ())
        self.setSucc (None)

      self._succLock.release ()
      self.debug (1, 'stab finished')

  def notify (self, url, key):
    """
      implements chord's notify.
      returns: True if the notifying peer is now our pred, False otherwise
    """
    result= False
    self.debug (1, "notify!")
    self._predLock.acquire ()
    self.debug (2, "pred locked")
    pred= self.getPred ()
    prevPred= pred

    if not pred or ooBetween (pred.key (), key, self.key ()):
      # self.debug (1, "set %s,%s as new pred" % (url, key))
      pred= self._peers.getNavel (url, key)
      self.setPred (pred)

      # don't talk in the brain
      if not pred==self._self:
        # give our data so he makes a backup
        self.debug (1, 'giving data as backup')
        # this may fail
        try:
          given= self.giveData (self.key (), self._succ.key (), self.Set)
          pred.backupData (given)
          # shouldn't we also tell him to forget about anything else?
          # nope
          if prevPred:
            # no more business w/ him
            prevPred.close ()
          # gotta save it for later ref.
          self._prevPred= prevPred
        except UmbDead:
          self.debug (1, '\'tis dead, Jim!')
          self.setPred (prevPred)
      result= True

    self._predLock.release ()
    self.debug (2, "pred released")
    return result

  def checkPred (self):
    self._predLock.acquire ()
    if self._pred.isDead ():
      self._pred= None
    self._predLock.release ()


  ############
  # extensions
  ############
  def findAuth (self, key):
    """
      looks for the auth of the key, but only in the already know peers.
      returns: the peer
    """
    self.debug (1, "findAuth! %d" % key)
    # we already have ourselves in the peer list, so there's at least one answer.
    peer= self._peers.getAuthNavel (key)
    return peer

  def findKnownSucc (self, key):
    """
      looks for the succ of the key, but only in the already know peers.
      returns: the peer
    """
    self.debug (1, "findKnownSucc! %d" % key)
    # * then 'and ...' is when have head but no tail
    if self._succ and self._pred:
      peer= self._peers.getSuccNavel (key)
      return peer
    else:
      self.debug (1, "fall back!")
      # is *this* right?
      return self._peers.getAuthNavel (self._key)

  def joinTo (self, url, key=None):
    """
      joins to a certain peer. asks the peer's key for adding it to the list and
      checks out that our key is not already in the ring (not implemented yet).
      returns: naught
    """
    if not key:
      # ask for the key...
      key= self.getNavelKey (url)
    # ... so we can add it to the server list properly.
    peer= self._peers.getNavel (url, key)
    terminated= self.join (peer)
    # while not terminated:
      # can fail only when the key already exists
      # TODO
      # terminated= self.join (peer)

  def processKeyedData (self, data, function, backupFunction=None):
    keys= data.keys ()
    keysQty= len (keys)
    accepted= {}
    i= 0
    added= 0
    m= self.key ()
    n= self.getSucc ().key ()
    wrongKey= None
    while i<keysQty:
      key= keys[i]
      args= data[key]
      if coBetween (m, key, n):
        self.debug (2, '[%d,%d] processing %d; data %s' % (i, keysQty, key, args))
        function (key, args)
        if backupFunction:
          accepted[key]= args
        added+= 1
      else:
        self.debug (2, '[%d,%d] dropping %d' % (i, keysQty, key))
        if not wrongKey:
          wrongKey= key
      i+= 1
    if backupFunction and len (accepted.keys())>0:
      backupFunction (accepted)
    if added<keysQty:
      # some values don't belong to us
      server= self.findAuth (wrongKey)
      return server
    else:
      return None

  def keepInSync (self, hash):
    # keep backup n'sync
    pred= self.getPred ()
    if pred:
      pred.backupData (hash)

  def addValues (self, key, values):
    """
      adds the values to the key
      returns: naught
    """
    self._data.addValues (key, values)

  def setValues (self, key, values):
    """
      sets the new value at key, forgetting whatever was there.
      use with caution!
      returns: naught
    """
    self._data.setValues (key, values)
    # keep backup n'sync
    # no, this is the one used for backup and taking itself

  def delValues (self, key, values):
    """
      deletes the value from the key's associated list
      returns: naught
    """
    self._data.delValues (key, values)

  def delKey (self, key, none):
    """
      deletes the key at all
      returns: naught
    """
    self._data.delKey (key)

  def forgetData (self, keys):
    self._data.acquire ()
    for key in keys:
      # only those that do not belong to us.
      if not self.amAuth (key):
        self._data.delKey (key)
    self._data.release ()

  def addRandomData (self, n):
    i= 0
    while i<n:
      key= random (1000)
      char= chr (ord ('a')+random (3))
      self._data.addValue (key, char)
      i+= 1

  def tellPredToForget (self):
    prevPred= self._prevPred
    if prevPred and not prevPred==self._self:
      # only if it's not us
      self.tellPeerToForget (prevPred, self.key (), self._succ.key (), self.Set)
      # no more no more
      # as in bye bye
      self._prevPred= None

  def tellPeerToForget (self, peer, m, n, what):
    self.debug (1, '%s.forgetData (given.keys ())' % peer)

    given= self.giveData (m, n, what)
    keys= given.keys ()
    keys.sort ()
    keys.reverse ()

    ans= peer.forgetData (keys)
    ok= ans[0]
    while not ok:
      (url, key)= ans[1]
      self.debug (1, "redirect to: %s:%d" % (url, key))
      peer= self._peers.getNavel (url, key)
      if not peer==self._self:
        # WTF?!?
        ans= peer.takeData (self.giveData (self.key (), peer.key (), what))
        ok= ans[0]

  def emp (self):
    self._data.emp ()

  def ident (self):
    params= self.params ()
    # ugly as old man butts
    return ["i am", str(params[0]), params[1]]

  def periodic (self):
    self.debug (1, 'periodic')
    Master.periodic (self)
    if not self._terminate:
      # we migh been asked to finish right now.
      self.stabilize ()

      if random (10)==1:
        peer= self._peers.getRandomNavel ()
        # don't gossip w/ myself!
        if not peer==self._self:
          self.gossip (peer)

      self.debug (1, "%s <-- %d --> %s" % (self._pred and self._pred.key () or None, self.key (), self._succ and self._succ.key () or None))
    else:
      self.debug (1, 'you might be pregnant...')

  def stop (self):
    self.debug (1, "join'ing challenger...")
    self._chal.join ()
    Master.stop (self)
