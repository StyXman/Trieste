###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################


from Trieste.common.server import Server
from Trieste.common.utils import coBetween

class NavelServer (Server):
  """
    a navel-to-any server
  """
  def __init__ (self, master, client):
    Server.__init__ (self, master, client)
    self._clientKey= None
    self.debug (1, "created and running n2arserver[%d]" % self._socket.fileno ())

  def attend (self, what, args):
    finished= False

    #######################
    # chord's ring maint proto
    #######################
    if what=='key':
      self.write ([self._master.key ()])

    elif what=='succ':
      succ= self._master.getSucc ()
      if succ:
        self.write ([succ.params ()])
      else:
        self.write ([(None, None)])

    elif what=='pred':
      pred= self._master.getPred ()
      if pred:
        self.write ([pred.params ()])
      else:
        self.write ([(None, None)])

    elif what=='notify':
      (url, key)= args[0]
      result= self._master.notify (url, key)
      self.write ([result])

    elif what=='succ of':
      key= args[0]
      stub= self._master.fastFindSucc (key)
      self.write ([stub.params ()])

    #############
    # key handling
    #############
    elif what=='value of':
      key= args[0]
      if self._master.amAuth (key):
        # value *IS* a list
        value= self._master._data.getValues (key)
        self.debug (1, 'value of: value: %s' % str (value))
        self.write ([True]+value)
      else:
        # find the correct one and redirect
        server= self._master.findAuth (key)
        self.write ([False, server.params ()])

    elif what=='add to':
      data= args[0]

      server= self._master.processKeyedData (data, self._master.addValues, self._master.keepInSync)
      if server:
        self.write ([False, server.params ()])
      else:
        self.write ([True])

    elif what=='del from':
      data= args[0]

      server= self._master.processKeyedData (data, self._master.delValues, self._master.keepInSync)
      if server:
        self.write ([False, server.params ()])
      else:
        self.write ([True])

    elif what=='del key':
      key= args[0]
      server= self._master.processKeyedData ({ key: None }, self._master.delKey, self._master.keepInSync)
      if server:
        self.write ([False, server.params ()])
      else:
        self.write ([True])


    elif what=='free':
      navels= self._master.navels ()
      vices= self._master.vices ()
      self.write ([
        self._master._data.findFree (),
        map (
          lambda key: navels[key].params (),
          navels.keys ()
        ), map (
          lambda key: vices[key].url (),
          vices.keys ()
        )
      ])

    ######################
    # ring maint key handling
    ######################
    elif what=='take':
      data= args[0]

      server= self._master.processKeyedData (data, self._master.setValues)
      if server:
        self.write ([False, server.params ()])
      else:
        self.write ([True])

    elif what=='forget':
      keys= args[0]

      self.debug (2, 'forgetting %s' % str(keys))
      self._master.forgetData (keys)
      self.write ([True])

    elif what=='backup':
      data= args[0]

      for key in data.keys ():
        if data[key]:
          self.debug (2, 'adding %d: %s' % (key, data[key]))
          self._master.setValues (key, data[key])
        else:
          self._master.forgetData ([key])
      self.write ([True])

    elif what=='tell pred to forget':
      self._master.tellPredToForget ()
      self.write ([True])

    ###########
    # gossiping
    ###########
    elif what=='known peers':
      navels= self._master.navels ()
      vices= self._master.vices ()
      self.write ([
        map (
          lambda key: navels[key].params (),
          navels.keys ()
        ), map (
          lambda key: vices[key].url (),
          vices.keys ()
        )
      ])

    #######
    # mkfs
    #######
    elif what=='emp':
      self._master.emp ()
      self.write ([True])

    #######################
    # don't look back in anger
    #######################
    elif what=='quit':
      self.write (["bye"])
      self.close ()
      finished= True

    ##########
    # debuging
    ##########
    elif what=='keys':
      keys= self._master._data.keys ()
      keys.sort ()
      self.write ([self._master.key (), keys])

    elif what=='terminate':
      self._master._terminate= True
      self.write (["i'm on that"])

    else:
      # fallback
      self.write (["unknown message"]);

    return finished
