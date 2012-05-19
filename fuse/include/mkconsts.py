#! /usr/bin/python
###########################################################################
#    Copyright (C) 2004 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from Trieste.common import consts

def main ():
  f= open ('consts.h', 'w')
  i= 0

  constList= ['statIno', 'statMode', 'statSize', 'statNlink', 'statCtime', 'statAtime', 'statMtime', 'statUid', 'statGid', 'pageSize', 'pageSizeBits']
  for c in constList:
    val= getattr (consts, c)
    if val>i:
      i= val
    f.write ("#define %s %d\n" % (c, val))

  f.write ("#define statTupleSize %d\n" % i)

  f.close ()

if __name__=='__main__':
  main ()
