###########################################################################
#    Copyright (C) 2003 by Marcos Dione
#    <mdione@grulic.org.ar>
#
# Copyright: See COPYING file that comes with this distribution
#
###########################################################################

from whrandom import uniform
from time import strftime, time, localtime
from getopt import getopt, GetoptError
from math import sqrt
import sys
import gzip

# helper functions
def chomp (a):
  """
    removes trailing \n's and \r's (for telnet communication)
  """
  while a and (a[-1]=="\n" or a[-1]=="\r"):
    a= a[:-1]
  return a

def debugLog (l, s):
  if l:
    now= time ()
    l.append ("%20.6f: %s\n" % (now, s))

def debugPrint (i, s, level=1, fast=True):
  # return
  if i==1 or i==5:
    now= time ()
    if fast:
      sys.stderr.write ("%20.6f: %s\n" % (now, s))
    else:
      (theClass, theMethod, theFileName, theLineNo)= getCaller (level)
      methodStr= "%s.%s()" % (theClass, theMethod)
      sys.stderr.write ("%s [%3d] @ %s.%s: %s\n" % (
        methodStr.ljust (20),
        theLineNo,
        strftime ("%H:%M:%S", localtime (now)),
        str (round (now-int(now), 4))[2:].ljust (4),
        str(s),
      ))

def random (m, n=None):
  """
    returns an uniformly generated integer in [m,n)
    or in [0,m) if n is not supplied.
  """
  if not n:
    return int(uniform (0, m))
  else:
    return int(uniform (m, n))

class UmbDead (Exception):
  """
    generic error that renders the peer unusable
  """
  pass

def ocBetween (a, b, c):
  """
    test b \belongs (a, c], using a generalized definition of (, ] in
    Chord's paper, subsection VI.C, paragraph 3
  """
  return (a<c and a<b and b<=c) or (a>=c and (b<=c or a<b))

def coBetween (a, b, c):
  """
    test b \belongs [a, c), using a generalized definition of (, ] in
    Chord's paper, subsection VI.C, paragraph 3
  """
  return (a<c and a<=b and b<c) or (a>=c and (b<c or a<=b))

def ooBetween (a, b, c):
  """
    test b \belongs (a, c), using a generalized definition of (, ] in
    Chord's paper, subsection VI.C, paragraph 3
  """
  return (a<c and a<b and b<c) or (a>=c and (b<c or a<b))

def ccBetween (a, b, c):
  """
    test b \belongs [a, c], using a generalized definition of (, ] in
    Chord's paper, subsection VI.C, paragraph 3
  """
  return (a<c and a<=b and b<=c) or (a>=c and (b<=c or a<=b))

def next (l):
  try:
    a= l.pop (0)
  except IndexError:
    a= None
  return a

class Option:
  """
    a parseable option.

    Option (short, long, value, list)
    where

    short is the short version of the option. must be a single character.
    long is the long version of the option. any string would do.
    value has several uses. if set, the option has an argument.
      also works as default value in case the opt is not found by getopt.
      the default is None.
    list, if set, is a string of separators of elements of the list.
      as long as parseOpts uses split for this task, there's no support
      for escapable separators. the default is None.
  """
  def __init__ (self, short, long, arg=None, list=None, default=None):
    self.short= short
    self.long= long
    if not default is None:
      self.value= default
      self.arg= True
    else:
      self.value= None
      self.arg= arg
    self.list= list

  def __str__ (self):
    return "-%s, --%s: %s" % (self.short, self.long, self.value)

  def asInteger (self):
    try:
      return int(self.value)
    except TypeError:
      return None

  def asFloat (self):
    try:
      return float(self.value)
    except TypeError:
      return None

  def asString (self):
    return self.value

  def asBool (self):
    try:
      return bool(self.value)
    except TypeError:
      return None

  def asBoolean (self):
    return self.asBool ()

def lstrip (s, chars=" "):
  """
    implements python 2.2.3's lstrip
  """
  i= 0
  while s[i] in chars:
    i+= 1

  return s[i:]

def parseOpts (opts, args):
  # help support
  opts.append (Option ('h', 'help'))

  shorts= ''
  longs= []
  result= {}
  for opt in opts:
    if opt.short:
      shorts+= opt.short+(opt.arg and ':' or '')
      result[opt.short]= opt
    if opt.long:
      longs.append (opt.long+(opt.arg and '=' or ''))
      result[opt.long]= opt

  debugPrint (2, "s: >%s<, l: %s" % (shorts, longs))

  # now, parse
  try:
    (found, args)= getopt (args, shorts, longs)
    for (opt, value) in found:
      # take out leading '-'s
      opt= lstrip (opt, '-')
      optObj= result[opt]
      # if the option accepts values, set it
      if optObj.arg:
        if optObj.list:
          optObj.value= value.split (optObj.list)
        else:
          optObj.value= value
      else:
        optObj.value= True

    # help support
    if result['h'].asBoolean ():
      usage (opts)
      sys.exit (1)

  except GetoptError:
    debugPrint (1, 'option parsing error!')
    usage (opts)
    sys.exit (1)

  return (result, args)

def usage (opts):
  print 'usage:'
  for opt in opts:
    print opt

class LungTimer:
  """
    just like an alarm, but you gotta tick it every time you want it to advance
  """
  def __init__ (self, timer):
    self._max= timer
    self._timer= 0

  def inc (self):
    self._timer= (self._timer+1) % self._max

  def tick (self):
    self.inc ()

  def rang (self):
    return self._timer==0

def getCaller (level=0):
  # taken from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/144838/
  # code from Christian Bird
  # slightly improved and generalized by Marcos Dione.

  # this gets us the frame of the caller and will work
  # in python versions 1.5.2 and greater (there are better
  # ways starting in 2.1
  try:
    raise UmbDead ("this is fake")
  except Exception:
    # get the current execution frame
    f= sys.exc_info ()[2].tb_frame
  # go back as many call-frames as was specified
  while level>=0 and f.f_back:
    f= f.f_back
    level= level-1
  try:
    # FIX: nor caller nor string (???) were defined
    if f[0][-3:] == '.py':
      file = "[%s:%s] " % (f[0][:-3].split('/')[-1], f[1])
    else:
      file = "[%s:%s] " % (f[0].split('/')[-1], f[1])
  except:
    file = ""
  # if there is a self variable in the caller's local namespace then
  # we'll make the assumption that the caller is a class method
  obj= f.f_locals.get ("self", None)
  if obj:
    return (obj.__class__.__name__, f.f_code.co_name, file, f.f_lineno)
  else:
    return (None, f.f_code.co_name, file, f.f_lineno)

def csvPrettyPrint (list):
  return str(list)

def csvParse (str):
  try:
    return eval(str)
  except:
    # means gibberish's what came, nothing
    return None

def reverse (s):
  l= list(s)
  l.reverse ()
  return ''.join (l)

class BackTrackFile (object):
  def __init__ (self, fileName, compressed=False):
    if compressed:
      self.f= gzip.open (fileName)
    else:
      self.f= file (fileName)
    self.buffer= []
    self.index= 0

  def readfromfile (self):
    l= self.f.readline ()
    self.buffer.append (l)

    return l

  def readline (self):
    # use the buffer
    try:
      l= self.buffer[self.index]
    except:
      l= None

    self.index+= 1
    if not l:
      l= self.readfromfile ()

    return l

  def commit (self):
    self.buffer= self.buffer[self.index:]
    self.index= 0

  def rollback (self, index=0):
    self.index= index

  def dropline (self):
    l= self.readline ()
    self.commit ()
    return l

class Avg (object):
  def __init__ (self):
    self.sum= 0.0
    self.qty= 0.0

  def add (self, f):
    self.sum+= float (f)
    self.qty+= 1

  def value (self):
    ans= 0.0
    if self.qty:
      ans= self.sum/self.qty
    return ans

  def __repr__ (self):
    return "%10.6f" % self.value ()

class Std (Avg):
  def __init__ (self):
    Avg.__init__ (self)
    self.sqr= 0.0

  def add (self, f):
    Avg.add (self, f)
    self.sqr+= float (f)**2

  def value (self):
    avg= Avg.value (self)
    ans= 0.0
    if self.qty:
      ans= sqrt (self.sqr/self.qty - avg**2)
    return (avg, ans)

  def __repr__ (self):
    val= self.value ()
    return ("(%10.6f, %10.6f)" % val)

class SizeError (Exception):
  pass

class Seq (object):
  def __init__ (self, size, kls):
    self.seq= [kls () for i in xrange (size)]
    self.size= size

  def add (self, seq):
    if not len (seq)==self.size:
      raise SizeError
    for i in xrange (self.size):
      self.seq[i].add (seq[i])

  def value (self):
    return (self.seq[0].qty, [self.seq[i].value () for i in xrange (self.size)])

  def __repr__ (self):
    s= "%d, %s" % (self.seq[0].qty, ", ".join ([self.seq[i].__repr__ () for i in xrange (self.size)]))
    return s
