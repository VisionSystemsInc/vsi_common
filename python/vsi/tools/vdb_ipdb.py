import IPython.core.debugger
import IPython.terminal.debugger
from functools import partial
import sys

import vsi.tools.vdb as vdb
from vsi.tools.vdb import set_attach, attach, pipe_server

class Vdb(IPython.terminal.debugger.TerminalPdb):
  ''' VSI Debugger, based off of IPython's 5.x or newer debugger '''
  def __init__(self, skipInput=True, *args, **kwargs):
    self.__ignore_next_user_return = skipInput
    IPython.terminal.debugger.TerminalPdb.__init__(self, *args, **kwargs)
    self.prompt = 'vdb> '

  #Modifications to skip initial user input
  def user_return(self, frame, return_value):
    if self.__ignore_next_user_return:
      self.__ignore_next_user_return = False
      self.onecmd('c')#continue, effectively ignoring the first input
    else:
      IPython.terminal.debugger.TerminalPdb.interaction(self, frame, None)

  #everything needed from set_trace, minus sys.settrace
  def _pre_settrace(self, frame=None):
    if frame is None:
      frame = sys._getframe().f_back
    f2 = frame

    self.reset()
    while f2:
      f2.f_trace = self.trace_dispatch
      self.botframe = f2
      f2 = f2.f_back
    self.setup(frame, None)

  #Manually call sys.settrace to use out mods
  def _settrace(self):
    sys.settrace(self.trace_dispatch)

try:
  delattr(IPython.core.debugger.OldPdb, 'do_r')
  delattr(IPython.core.debugger.OldPdb, 'do_q')
  delattr(IPython.core.debugger.Pdb, 'do_q') #New quit in newer ipython
except:
  pass
#I HATE these! Too powerful and too easy to do by accident

class VdbPostMortemHook(vdb.PostMortemHook):
  @staticmethod
  def set_post_mortem(interactive=False):
    sys.excepthook = partial(vdb.dbstop_exception_hook,
                             post_mortem=post_mortem,
                             interactive=interactive)

def dbclear_if_error():
  VdbPostMortemHook.dbclear_if_error()

def dbstop_if_error(interactive=False):
  ''' Run this to auto start the vdb debugger on an exception.

  Arguments
  ---------
  interactive : :class:`bool`, optional
      Default False. dbstop if console is interactive. You are still able to
      print and run commands in the debugger, just listing code declared
      interactively will not work. Does not appear to work in ipython. Use
      %debug instead. This will not help in the multithread case in ipython...
      ipython does too much, just don't try that. Unless someone adds a way to
      override ipython's override.
  '''
  VdbPostMortemHook.dbstop_if_error(interactive=interactive)

class DbStopIfError(vdb.DbStopIfErrorGeneric):
  ''' With statement for local dbstop situations '''
  #This is all needed JUST for threading. It uses syshook instead of __exit__

  def get_post_mortem_class(self):
    ''' Get post mortem class for Vdb '''
    return VdbPostMortemHook

  def get_post_mortem(self):
    return post_mortem

def runpdb(lines, debugger=None):
  ''' Executes a list of vdb command

  Arguments
  ---------
  lines : :obj:`str` or :obj:`list` or :obj:`tuple`
      Collection of strings to be executed as if you were already in the
      debugger. Useful for setting breakpoints programatically.

  Return
  ------
  object
      Returns the debugger object, since this can only be executed on the
      debugger object, you can optionally pass it in as the second argument
      if you want to call runpdb multiple times. If you do not, a new
      debugger object is created, and all the "memory" of the last debugger
      is lost, such as breakpoints, etc...
  '''

  try:
    lines + ' ' #Is str like
    lines = [lines] #make it a list
  except:
    pass

  if not debugger:
    debugger = Vdb()

  debugger._pre_settrace(frame=sys._getframe().f_back)

  for line in lines:
    debugger.onecmd(line)

  debugger._settrace()

  return debugger

def set_trace(frame=None, depth=None):
  ''' Helper function, like pdb.set_trace
  '''
  frame = vdb.find_frame(frame, depth if depth is not None else 2 if frame is None else 0)
  Vdb().set_trace(frame)

def post_mortem(tb=None):
  ''' Helper function, like pdb.post_mortem '''
  # handling the default
  if tb is None:
    # sys.exc_info() returns (type, value, traceback) if an exception is
    # being handled, otherwise it returns None
    tb = sys.exc_info()[2]
    if tb is None:
      raise ValueError("A valid traceback must be passed if no "
                       "exception is being handled")

  debugger=Vdb()
  debugger.reset()
  debugger.interaction(None, tb)
