import rpdb2
import os
import sys
import vsi.tools.vdb as vdb
from functools import partial

def dbstop_if_error(_rpdb2_pwd='vsi', fAllowUnencrypted=True,
                         fAllowRemote=False, timeout=0, source_provider=None,
                         fDebug=False, depth=0):
  ''' Run this to auto start the debugger on an exception.

      I THINK rpdb2 does no use the same traceback or the frame/stack objects
      as pdb. So there is no way to just hand the debugger a traceback (yet)
      So by starting the debugger, all exceptions will be cause, and just
      attach to the debugger and type "analyze" to start debugging the last
      exception.

      Of course, this means that if the debugger slows down execution, it will
      have to slow down all of the execution, instead of being loaded "just in
      time"'''
  rpdb2.start_embedded_debugger(_rpdb2_pwd, fAllowUnencrypted, fAllowRemote,
                                timeout, source_provider, fDebug, depth)

#I'm not even going to attempt a DbStopIfError class, since this profiler does
#not have a Post Mortem equivalent... yet. Need to find a way to push the pm
#data into whatever the analyze command uses, so that it can be faked out

""" I can't get this working yet either. rpdb uses the profiler to catch exceptions, NOT excepthook
  #old_excepthook = rpdb2.__excepthook
  #rpdb2.__excepthook = partial(rpdb_exception_hook, old_excepthook)
  #sys.excepthook = rpdb_exception_hook

def rpdb_exception_hook(old_excepthook, type, value, tb, next_excepthook, index):
#def rpdb_exception_hook(type, value, tb):
  traceback.print_exception(type, value, tb)
  print('Starting rpdb2 for post_mortem... Remember to type analyze in the debugger')
  #import sys
  #sys.stdout.flush()
  #print(sys.excepthook)
  #rpdb2.start_embedded_debugger('vsi', timeout=0)
  #rpdb2.m_current_ctx.m_core._break(rpdb2.m_current_ctx, tb.tb_frame, 'return', None)
  old_excepthook(type, value, traceback, next_excepthook, index)

# I can't get this working yet...
  sys.excepthook = partial(rpdb_dbstop_exception_hook, _rpdb2_pwd=_rpdb2_pwd, *args, **kwargs)
  rpdb2.set_excepthook()

def rpdb_post_mortem(tb=None, _rpdb2_pwd='vsi', **kwargs):
  #NO idea how to do this right right now...
  #This isn't perfect... but should help
  ###rpdb_set_trace(*args, **kwargs)
  #print('rpdb start')
  #rpdb2.start_embedded_debugger(_rpdb2_pwd, timeout=5*60, **kwargs)

  '''print('rpdb settrace')
  rpdb2.settrace(f=tb.tb_frame)
  ctx = rpdb2.g_debugger.get_ctx(rpdb2.thread.get_ident())
  ctx.m_fUnhandledException = True
  print('rpdb setbreak')
  rpdb2.setbreak()
  print('rpdb broke''')

def rpdb_dbstop_exception_hook(type, value, tb, _rpdb2_pwd='vsi', *args, **kwargs):
  if hasattr(sys, 'ps1') or not sys.stderr.isatty():
    sys.__excepthook__(type, value, tb)
  else:
    import traceback
    traceback.print_exception(type, value, tb)

    rpdb_post_mortem(tb, _rpdb2_pwd, *args, **kwargs) # more "modern" """

def set_trace(_rpdb2_pwd='vsi', fAllowUnencrypted=True,
                   fAllowRemote=False, timeout=5*60, source_provider=None,
                   fDebug=False, depth=1):
  ''' Works, but without the other parts, it's far from auto '''
  print('Starting rpdb2...')
  rpdb2.start_embedded_debugger(_rpdb2_pwd, fAllowUnencrypted, fAllowRemote,
                                timeout, source_provider, fDebug, depth)
  #else:#This does NOT work, as far as I know. It doesn't get the depth right, so....
  #  __start_embedded_debugger(_rpdb2_pwd, fAllowUnencrypted, fAllowRemote,
  #                                timeout, source_provider, fDebug, depth, frame)
    #rpdb2.g_debugger.settrace(frame, timeout=timeout)
    #rpdb2.g_debugger.m_current_ctx._break(rpdb2.g_debugger.m_current_ctx, frame, 'return', None)
#  sm = rpdb2.CSessionManager(_rpdb2_pwd, *args, **kwargs)
#
#  sm.start()
#  #set timeout 0
#  frame = find_frame(frame, depth)
#  rpdb2.g_debugger.settrace(frame)

def attach(pid, ip='127.0.0.1', password='vsi', gui=False, break_exit=False):
  vdb.attach(pid)
  import sys
  old_args = sys.argv

  #attach must come last for some STUPID reason. Dumb parser
  sys.argv = ['', '--pwd=%s' % password, '--host=%s' % ip, '--attach', str(pid)]
  print(sys.argv)
  if gui:
    import winpdb
    winpdb.main()
  else:
    rpdb2.main()

  # Debuggee breaks (pauses) here
  # before program termination.
  #
  # You can step to debug any exit handlers.
  #
  if break_exit:
    rpdb2.setbreak()
  sys.argv = old_args

def set_attach(_rpdb2_pwd='vsi', *args, **kwargs):
  vdb.set_attach(partial(set_trace, *args, **kwargs))

class CDebuggerCoreThread2(rpdb2.CDebuggerCoreThread):
  ''' I just wanted to add some output on exception!!!'''
  def profile(self, frame, event, arg):
    """
    Profiler method.
    The Python profiling mechanism is used by the debugger
    mainly to handle synchronization issues related to the
    life time of the frame structure.
    """
    #print_debug('profile: %s, %s, %s, %s, %s' % (repr(frame), event, frame.f_code.co_name, frame.f_code.co_filename, repr(arg)[:40]))

    if event == 'return':
      self.m_depth -= 1

      if sys.excepthook != rpdb2.g_excepthook:
        rpdb2.set_excepthook()

      self.m_frame = frame.f_back

      try:
        self.m_code_context = self.m_core.m_code_contexts[self.m_frame.f_code]
      except AttributeError:
        if self.m_event != 'return' and self.m_core.m_ftrap:
          #
          # An exception is raised from the outer-most frame.
          # This means an unhandled exception.
          #

          self.m_frame = frame
          self.m_event = 'exception'

          self.m_uef_lineno = self.m_ue_lineno

          self.m_fUnhandledException = True
          print("Exception detected. Attach with rpdb2 pid {}\n"
                "Don't forget to type 'analyze'".format(os.getpid()))
          self.m_core._break(self, frame, event, arg)

          self.m_uef_lineno = None

          if frame in self.m_locals_copy:
            self.update_locals()

          self.m_frame = None

        self.m_core.remove_thread(self.m_thread_id)
        sys.setprofile(None)
        sys.settrace(self.m_core.trace_dispatch_init)

      if self.m_frame_external_references == 0:
        return

      try:
        self.m_frame_lock.acquire()

        while self.m_frame_external_references != 0:
          rpdb2.safe_wait(self.m_frame_lock, 1.0)

      finally:
        self.m_frame_lock.release()

rpdb2.CDebuggerCoreThread = CDebuggerCoreThread2
#This is a crappy patch. Then again, rpdb2 could use a re-write. Then again,
#rpdb2 IS NOT A DEBUGGER! It's a profiler acting as a debugger.