###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################


from Trieste.common.utils import next
from Trieste.common.object import Object

class Ring (Object):
  """
    This class handles all the calls to navels that can return a redirection
    and handle that redirection
  """
  def __init__ (self, master):
    Object.__init__ (self)
    self.master= master
    self.peers= master._peers

  def getData (self, key):
    navel= self.peers.getAuthNavel (key)
    ans= navel.getData (key)
    ok= ans[0]
    while not ok:
      (url, key)= ans[1]
      self.debug (1, "redirect to: %s:%d" % (url, key))
      navel= self.peers.getNavel (url, key)
      ans= navel.getData (key)
      ok= ans[0]

    # when succeed, returns a str of the list
    return ans

  def addData (self, data, max, peer=None):
    # may be this should be more clever,
    # just like what vice does
    if peer==None:
      keys=data.keys ()
      keys.sort ()
      peer= self.peers.getAuthNavel (keys[0])

    ans= peer.addData (data)
    # iterate as the keys get rejected 'cause there's another auth
    ok= ans[0]
    while not ok:
      (url, key)= ans[1]
      self.debug (1, "redirect to: %s:%d" % (url, key))
      peer= self.peers.getNavel (url, key)
      ans= peer.addData (self.master.giveData (peer.key (), max))
      ok= ans[0]

  def delKey (self, key):
    """
      removes one key from the ring. used when deleting inodes.
    """
    peer= self.peers.getAuthNavel (key)
    ans= peer.delKey (key)

  # methods to come:
  # takeData from Navel.keyPass()
  # forgetData from Navel.tellPredToForget()

  def vicesForIno (self, ino):
    urls= self.getData (ino)
    ok= next (urls)
    if ok:
      vices= []
      for url in urls:
        vices.append (self.peers.getVice (url))
      self.debug (1, 'ino %d vices: %s' % (ino, vices))
      return vices
    else:
      return None
