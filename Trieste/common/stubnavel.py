###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from __future__ import nested_scopes

from Trieste.common.navelclient import NavelClient
from Trieste.common.utils import chomp
from Trieste.common.stub import Stub
from Trieste.common.consts import Normal, Succ, Pred

class StubNavel (Stub):
  """
    This class should represent anything we might need from a navel,
    including if it's our succ or pred
  """
  def __init__ (self, navel, url, key, kind=Normal):
    Stub.__init__ (self, navel, url, key)
    self.debug (1, "StubNavel: %s" % (url))
    self._kind= kind

  def createEmptyClient (self):
    self._client= NavelClient (self._url, self._master)

  def setKind (self, kind=Normal):
    self._kind= kind

  def kind (self):
    return self._kind

  def __repr__ (self):
    return "StubNavel: %s:%s [%d]" % (self.url (), self.key (), self._kind)

#   def isDead (self):
#     # test the socket?
#     return self._dead

  ##############
  # chord's proto
  ##############
  def succ (self):
    what= ['succ']
    (url, key)= self._client.ask (what)[0]

    try:
      return (url, key)
    except ValueError:
      # succ is None,None or some other shit
      return None

  def pred (self):
    what= ['pred']
    (url, key)= self._client.ask (what)[0]

    return (url, key)

  def notify (self, params):
    what= ['notify', params]
    ans= self._client.ask (what)

    self.debug (1, "on notify, got >%s<" % ans[0])
    return ans[0]

  def findSucc (self, reqKey):
    """
      Looks for the succ of key.
      returns: the parameters of such peer (url, key)
    """
    what= ['succ of', reqKey]
    (url, key)= self._client.ask (what)[0]

    return (url, key)

  ############
  # extensions
  ############
  def getData (self, key):
    what= ['value of', key]
    ans= self._client.ask (what)

    return ans

  def addData (self, h):
    if len (h.keys ())>0:
      what= ['add to', h]
      return self._client.ask (what)
    else:
      return [True]

  def delKey (self, key):
    what= ['del key', key]
    return self._client.ask (what)

  def free (self):
    what= ['free']
    ans= self._client.ask (what)

    # self.debug (1, 'free gave me: >%s<' % ret)
    self._master.updatePeers (ans[1], ans[2])
    return ans[0]

  def takeData (self, h):
    if len (h.keys ())>0:
      what= ['take', h]
      return self._client.ask (what)
    else:
      return [True]

  def forgetData (self, keys):
    """
      didn't I told you about my condition...?
    """
    if len (keys)>0:
      keys.sort ()
      keys.reverse ()
      what= ['forget', keys]
      return self._client.ask (what)
    else:
      return [True]

  def backupData (self, h):
    if len (h.keys ())>0:
      # self.debug (1, "giving %s" % h)
      what= ['backup', h]
      return self._client.ask (what)
    else:
      return [True]

  def tellPredToForget (self):
    what= ['tell pred to forget']
    return self._client.ask (what)

  def emp (self):
    what= ['emp']
    return self._client.ask (what)
