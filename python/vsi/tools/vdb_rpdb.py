
import rpdb
import os
import sys
import vsi.tools.vdb as vdb
from functools import partial
import traceback

DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 4444

def dbstop_if_error(ip=DEFAULT_IP, port=DEFAULT_PORT):
  ''' Run this to auto start the debugger on an exception. '''
  sys.excepthook = partial(dbstop_exception_hook, ip=ip, port=port)

def dbstop_exception_hook(type, value, tb, ip=DEFAULT_IP, port=DEFAULT_PORT):
  if hasattr(sys, 'ps1') or not sys.stderr.isatty():
  # we are in interactive mode or we don't have a tty-like
  # device, so we call the default hook
    sys.__excepthook__(type, value, tb)
  else:
    #we are NOT in interactive mode, print the exception
    traceback.print_exception(type, value, tb)
    # ...then start the debugger in post-mortem mode.
    post_mortem(tb, ip=ip, port=port)

def post_mortem(tb=None, ip=DEFAULT_IP, port=DEFAULT_PORT):
  if tb is None:
    # sys.exc_info() returns (type, value, traceback) if an exception is
    # being handled, otherwise it returns None
    tb = sys.exc_info()[2]
    if tb is None:
      raise ValueError("A valid traceback must be passed if no "
                       "exception is being handled")
  print 'Its %s:%d' % (ip, port)
  r = rpdb.Rpdb(addr=ip, port=port)
  r.reset()
  r.interaction(None, tb)

def set_trace(frame=None, depth=None, ip=DEFAULT_IP, port=DEFAULT_PORT):
  ''' Wrapper function to keep the same import x; x.set_trace() interface. 
  
      We catch all the possible exceptions from pdb and cleanup. '''
  frame = vdb.find_frame(frame, depth if depth is not None else 2 if frame is None else 0)

  try:
    debugger = rpdb.Rpdb(addr=ip, port=port)
  except socket.error:
    if rpdb.OCCUPIED.is_claimed(port, sys.stdout):
      # rpdb is already on this port - good enough, let it go on:
      sys.stdout.write("(Recurrent rpdb invocation ignored)\n")
      return
    else:
      # Port occupied by something else.
      raise
  try:
    debugger.set_trace(frame)
  except Exception:
    import traceback
    traceback.print_exc()


def attach(pid, ip=DEFAULT_IP, port=DEFAULT_PORT):
  ''' NOT IMPLEMENTED! Needs a telnet client '''
  vdb.attach(pid)
  assert(False)

def set_attach(ip=DEFAULT_IP, port=DEFAULT_PORT):
  vdb.set_attach(db_cmd=partial(set_trace, ip=ip, port=port))
