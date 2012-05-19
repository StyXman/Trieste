###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

import re

from Trieste.common.object import Object

class NoParse (Exception):
  pass

class URL (Object):
  """
    defines a generic url handler
    has parser and pretty printer
  """
  def __init__ (self, url=None):
    Object.__init__ (self)
    self._proto= None
    self._host= None
    self._port= None
    # [a-zA-z0-9\-]
    self._match= re.compile ('(\w+)://([\w|\.|-]+):(\d+)/')
    if url:
      if not isinstance (url, URL):
        self.parse (url)
      else:
        self._proto= url.proto ()
        self._host= url.host ()
        self._port= url.port ()

  def parse (self, strUrl):
    self.debug (2, 'parsing >%s<' % strUrl)
    # don't forget to check for ''
    # no need, '' works as False and None here
    if strUrl:
      try:
        g= self._match.match (strUrl)
        (self._proto, self._host, self._port)= (g.group (1), g.group (2),
int(g.group (3)))
      except:
        raise NoParse, strUrl

  def __repr__ (self):
    if self._host and self._port:
      return "'%s://%s:%d/'" % (self._proto, self._host, self._port)
    else:
      return "''"

  def __str__ (self):
    if self._host and self._port:
      return "%s://%s:%d/" % (self._proto, self._host, self._port)
    else:
      return ""

  def setURL (self, url):
    self.parse (url)

  def getParams (self):
    return (self._host, self._port)

  def proto (self):
    return self._proto

  def host (self):
    return self._host

  def port (self):
    return self._port
