###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################


from Trieste.common.client import Client

class NavelClient (Client):
  """
    is a Navel for local quering, but it really asks the server.
  """

  def key (self):
    """
      I need this one here for blind-joining
    """
    return self.ask (['key'])[0]

  def ident (self):
    if self._master:
      try:
        self.write (self._master.ident ())
        self.read ()
      except:
        Client.ident (self)
    else:
      Client.ident (self)
