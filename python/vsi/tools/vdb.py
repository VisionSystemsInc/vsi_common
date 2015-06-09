import sys
import pdb
import IPython.core.debugger
from bdb import BdbQuit

class Tracer(IPython.core.debugger.Tracer):
  def __init__(self, colors=None, skipInput = True, *args, **kwargs):
    super(Tracer, self).__init__(colors)
    self.debugger = Vdb(skipInput, self.debugger.color_scheme_table.active_scheme_name, *args, **kwargs)
    #This may be dirty, but is less likely to miss features in the future

class Vdb(IPython.core.debugger.Pdb):
  ''' VSI Debugger '''
  def __init__(self, skipInput=True, *args, **kwargs):
    self.__ignore_next_user_return = skipInput;
    IPython.core.debugger.Pdb.__init__(self, *args, **kwargs);

  #Modifications to skip initial user input
  def user_return(self, frame, return_value):
    if self.__ignore_next_user_return:
      self.__ignore_next_user_return = False;
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

delattr(IPython.core.debugger.OldPdb, 'do_r');
delattr(IPython.core.debugger.OldPdb, 'do_q');
#I HATE these! Too powerful and too easy to do by accident

def runpdb(lines, debugger=None):
  try:
    lines + ' ' #Is str like
    lines = [lines] #make it a lise
  except:
    pass;

  if not debugger:
    debugger = Tracer().debugger;
    
  debugger._pre_settrace(frame=sys._getframe().f_back);
  
  for line in lines:
    debugger.onecmd(line)
  
  debugger._settrace()

def set_trace(frame=None, colors=None):
  ''' set colors = "NoColor", "Linux", or "LightBG"  ''' 
  if colors is None:
    from IPython import get_ipython
    ip = get_ipython()
    if ip is None:
      colors='Linux'
    else:
     colors = ip.colors
  if not frame:
    frame = sys._getframe().f_back
  Tracer(skipInput=False, colors=colors).debugger.set_trace(frame)