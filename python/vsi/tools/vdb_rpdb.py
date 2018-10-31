
import rpdb
import os
import sys
import vsi.tools.vdb as vdb
from functools import partial
import traceback

DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 4444

class RpdbPostMortemHook(vdb.PostMortemHook):
  @staticmethod
  def set_post_mortem(interactive=False, ip=DEFAULT_IP, port=DEFAULT_PORT):
    sys.excepthook = partial(vdb.dbstop_exception_hook,
                             interactive=interactive,
                             post_mortem=partial(post_mortem,
                                                 ip=ip, port=port))

def dbclear_if_error():
  RpdbPostMortemHook.dbclear_if_error()

def dbstop_if_error(interactive=False, ip=DEFAULT_IP, port=DEFAULT_PORT):
  ''' Run this to auto start the debugger on an exception.

      Optional arguments

      Parameters
      ----------
      interactive : bool
          see vsi.tools.vdb.dbstop_if_error
      ip : str
          Default 127.0.0.1 - Ip to bind to for remote debugger
      port : int
        Default 4444 - Port to bind to for remote debugger'''

  RpdbPostMortemHook.dbstop_if_error(interactive=interactive,
                                     ip=ip, port=port)

def post_mortem(tb=None, ip=DEFAULT_IP, port=DEFAULT_PORT):
  ''' Parameters
      ---------
      tb : str
          The Traceback
      ip : str
          The IP Address
      port : int
          The Port

      Raises
      ------
      ValueError
          Passes a valied traceback
      '''
  if tb is None:
    # sys.exc_info() returns (type, value, traceback) if an exception is
    # being handled, otherwise it returns None
    tb = sys.exc_info()[2]
    if tb is None:
      raise ValueError("A valid traceback must be passed if no "
                       "exception is being handled")
  r = rpdb.Rpdb(addr=ip, port=port)
  r.reset()
  r.interaction(None, tb)

class DbStopIfError(vdb.DbStopIfErrorGeneric):
  def get_post_mortem(self):
    return post_mortem
  def get_post_mortem_class(self):
    return RpdbPostMortemHook


def set_trace(frame=None, depth=None, ip=DEFAULT_IP, port=DEFAULT_PORT):
  ''' Wrapper function to keep the same import x; x.set_trace() interface.

      We catch all the possible exceptions from pdb and cleanup. 
      
      Parameters
      ----------
      frame : str
          The Frame
      depth : int
          The Depth
      ip : str
          The IP Address
      port : int
          The Port
      '''
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
  ''' NOT IMPLEMENTED! Needs a telnet client 
  
      Parameters
      ----------
      pid : str
          The Process ID
      ip : str
          The IP Address
      port : str
          The Port
      '''
  vdb.attach(pid)
  assert(False)

def set_attach(ip=DEFAULT_IP, port=DEFAULT_PORT):
  ''' Parameters
      ----------
      ip : str
          The IP Address
      port : str
          The Port
      '''
  vdb.set_attach(db_cmd=partial(set_trace, ip=ip, port=port))
