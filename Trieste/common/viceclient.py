###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################


from Trieste.common.client import Client

class ViceClient (Client):
  def __init__ (self, url, master=None, stub=None):
    Client.__init__ (self, url, master)
    self._stub= stub

  def ident (self):
    if self._master:
      try:
        self.write (self._master.ident ())
        self.read ()
      except:
        Client.ident (self)
    else:
      Client.ident (self)

  def ask (self, what, data=None):
    ans= Client.ask (self, what, data)
    if self._stub:
      self._stub.setStats (ans[0])
    return ans[1]
