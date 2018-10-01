import IPython.core.debugger
from functools import partial
import sys

import vsi.tools.vdb as vdb
from vsi.tools.vdb import set_attach, attach, pipe_server

class Tracer(IPython.core.debugger.Tracer):
  ''' Used by Vdb '''
  def __init__(self, colors=None, skipInput = True, *args, **kwargs):
    try:
      super(Tracer, self).__init__(colors)
    except ValueError:
      #This is JUST IN CASE invalid color is specified, should not be relied on
      super(Tracer, self).__init__('Linux')
    self.debugger = Vdb(skipInput, self.debugger.color_scheme_table.active_scheme_name, *args, **kwargs)
    #This may be dirty, but is less likely to miss features in the future

class Vdb(IPython.core.debugger.Pdb):
  ''' VSI Debugger '''
  def __init__(self, skipInput=True, *args, **kwargs):
    self.__ignore_next_user_return = skipInput
    IPython.core.debugger.Pdb.__init__(self, *args, **kwargs)
    self.prompt = 'vdb> '

  #Modifications to skip initial user input
  def user_return(self, frame, return_value):
    if self.__ignore_next_user_return:
      self.__ignore_next_user_return = False
      self.onecmd('c')#continue, effectively ignoring the first input
    else:
      IPython.core.debugger.Pdb.interaction(self, frame, None)

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
  def set_post_mortem(interactive=False, colors=None):
    sys.excepthook = partial(vdb.dbstop_exception_hook,
                             post_mortem=partial(post_mortem, colors=colors),
                             interactive=interactive)

def dbclear_if_error():
  VdbPostMortemHook.dbclear_if_error()

def dbstop_if_error(interactive=False, colors=None):
  ''' Run this to auto start the vdb debugger on an exception.

      Optional arguments:
      interactive - Default False. dbstop if console is interactive. You are
                    still able to print and run commands in the debugger, just
                    listing code declared interactively will not work. Does
                    not appear to work in ipython. Use %debug instead. This
                    will not help in the multithread case in ipython...
                    ipython does too much, just don't try that. Unless
                    someone adds a way to override ipython's override.
      colors - Default None. Set ipython debugger color scheme'''
  VdbPostMortemHook.dbstop_if_error(interactive=interactive, colors=colors)

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

      Arguments:
      lines - list/tuple/etc... of strings to be executed as if you were
              already in the debugger. Useful for setting breakpoints
              programatically.

      Returns the debugger object, since this can only be executed on the
      debugger object, you can optionally pass it in as the second argument
      if you want to call runpdb multiple times. If you do not, a new
      debugger object is created, and all the "memory" of the last debugger
      is lost, such as breakpoints, etc...'''

  try:
    lines + ' ' #Is str like
    lines = [lines] #make it a list
  except:
    pass

  if not debugger:
    debugger = Tracer().debugger

  debugger._pre_settrace(frame=sys._getframe().f_back)

  for line in lines:
    debugger.onecmd(line)

  debugger._settrace()

  return debugger

def get_colors(colors=None):
  if colors is None:
    from IPython import get_ipython
    ip = get_ipython()
    if ip is None:
      colors='Linux'
    else:
     colors = ip.colors
  return colors

def set_trace(frame=None, colors=None, depth=None):
  ''' Helper function, like pdb.set_trace

      set colors = "NoColor", "Linux", or "LightBG"  '''
  colors=get_colors(colors)
  frame = vdb.find_frame(frame, depth if depth is not None else 2 if frame is None else 0)
  Tracer(skipInput=False, colors=colors).debugger.set_trace(frame)

def post_mortem(tb=None, colors=None):
  ''' Helper function, like pdb.post_mortem '''
  # handling the default
  if tb is None:
    # sys.exc_info() returns (type, value, traceback) if an exception is
    # being handled, otherwise it returns None
    tb = sys.exc_info()[2]
    if tb is None:
      raise ValueError("A valid traceback must be passed if no "
                       "exception is being handled")
  colors = get_colors(colors)
  tracer = Tracer(skipInput=False, colors=colors)
  tracer.debugger.reset()
  tracer.debugger.interaction(None, tb)
