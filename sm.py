#! /usr/bin/python
###########################################################################
#    Copyright (C) 2003-2005 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from sys import argv, exit
from socket import getfqdn

from Trieste.common.utils import debugPrint, Option, parseOpts
from Trieste.common import consts

from Trieste.vice.vice import Vice

def main ():
  (opts, args)= parseOpts ([
    Option ('a', 'append', False),
    Option ('b', 'broadcast-to', True, default=''),
    Option ('c', 'connect-to', True, default=''),
    Option ('n', 'column', True, default=0),
    Option ('p', 'port', True, default=consts.vicePort),
    Option ('s', 'space', True),
    Option ('d', 'data-dir', True, default='data'),
    Option ('l', 'log-file', True),
  ], argv[1:])

  debugPrint (1, 'parsed args: %s, left args: %s' % (
    ", ".join (
      map (
        lambda x: "%s: %s" % (x, opts[x].value),
        opts.keys ()
      ))
    , args))

  localPort= opts['p'].asInteger ()
  serverUrl= opts['c'].asString ()
  net= opts['b'].asString ()
  column= opts['n'].asInteger ()
  space= opts['s'].asInteger ()
  dataDir= opts['d'].asString ()
  append= opts['a'].asBoolean ()

  hostName= getfqdn ()
  # hostName= 'tempest.fsl.org.ar'

  a= Vice ("vice://%s:%d/" % (hostName, localPort), space=space, path=dataDir, fileName=opts['l'].asString ())
  if net:
    if not a.init (net=net):
      exit (1)
  else:
    # keep old opts so tests can still be performed on one machine
    a.init (url=serverUrl)

  a.run ()
  debugPrint (1, 'finished: saving log')
  a.saveLog ()

if __name__=='__main__':
  main ()
