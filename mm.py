#! /usr/bin/python
###########################################################################
#    Copyright (C) 2003-2005 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from sys import argv
# from __future__ import nested_scopes
from socket import getfqdn

from Trieste.common.utils import debugPrint, Option, parseOpts
from Trieste.common import consts

from Trieste.umbie.navel import Navel

def main ():
  debugPrint (1, "args: %s" % str(argv))
  (opts, args)= parseOpts ([
    Option ('b', 'broadcast-to', True, default=''),
    Option ('c', 'connect-to', True, default=''),
    Option ('n', 'column', True, default=0),
    Option ('p', 'port', True),
    Option ('s', 'simulated-values', default=0),
    Option ('l', 'log-file', True),
  ], argv[1:])

  debugPrint (1, 'parsed args: %s, left args: %s' % (
    ", ".join (
      map (
        lambda x: "%s: %s" % (x, opts[x].value),
        opts.keys ()
      ))
    , args))

  if opts['p'].asInteger ():
    debugPrint (1, 'using port %s' % opts['p'].asString ())
    localPort= opts['p'].asInteger ()
  else:
    debugPrint (1, 'using default port %d' % consts.umbiePort)
    localPort= consts.umbiePort
  serverUrl= opts['c'].asString ()
  net= opts['b'].asString ()
  column= opts['n'].asInteger ()
  simVals= opts['s'].asInteger ()

  hostName= getfqdn ()
  # hostName= 'tempest.fsl.org.ar'

  a= Navel ("umbie://%s:%d/" % (hostName, localPort), column, fileName=opts['l'].asString ())
  if not net:
    # keep old opts so tests can still be performed on one machine
    a.init ()
    if serverUrl:
      a.joinTo (serverUrl)
    else:
      # we're supposed to be alone
      a.createRing (simVals)
  else:
    a.init (net)
  a.run ()
  debugPrint (1, 'finished: saving log')
  a.saveLog ()

if __name__=='__main__':
  main ()
