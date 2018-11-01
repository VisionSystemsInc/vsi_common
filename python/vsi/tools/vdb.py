import sys
import pdb
from bdb import BdbQuit
import os
import signal
from functools import partial
import traceback

#from vsi.tools import static

if os.name == 'nt':
  from vsi.windows.named_pipes import Pipe
  import threading
  import ctypes
  ATTACH_SIGNAL = signal.SIGINT
else:
  ATTACH_SIGNAL=signal.SIGUSR1

def find_frame(frame, depth=0):
  ''' Parameters
      ---------
      frame : str
          The Frame
      depth : int
          The Depth
      '''
  if not frame:
    frame = sys._getframe()
  for d in range(depth):
    if frame.f_back is None:
      break
    frame = frame.f_back
  return frame

def set_attach(db_cmd=None, signal=ATTACH_SIGNAL):
  ''' Set up this process to be "debugger attachable"

      Parameters
      ----------
      db_cmd : str
          The Debugger Command
      signal : var
          The Attach Signal


      Just like gdb can attach to a running process, if you execute this on a
      process, now you can "attach" to the running python using the attach
      command

      This works pretty well, and allows you to resume the code UNLESS you are
      running in windows and happen to interrupt a sleep command.'''
  #Todo: Add tcp OPTION?

  signal.signal(signal, partial(handle_db, db_cmd=db_cmd))
  if os.name == 'nt':
    thread = threading.Thread(target=pipe_server)
    thread.daemon = True
    thread.start()
  #print(os.getpid())

def attach(pid, signal=ATTACH_SIGNAL):
  ''' Trigger a python pid that's been already run set_attach

      Parameters
      ----------
      pid : str
          The Process ID
      signal : var
          The Attach Signal


      This is the second part of attaching to a python process. Once
      set_attach is run, on another prompt running attach will trigger
      the interrupt thing attaching or triggering whatever db_cmd was'''
  if os.name == 'nt':
    pipe = Pipe('vdb_%d' % pid)
    pipe.write('vsi')
    pipe.close()
  else:
    os.kill(pid, signal)

def pipe_server():
  ''' Part of attach/set_attach for Windows '''
  while 1:
    pipe = Pipe('vdb_%d' % os.getpid(), server=True)
    knock = pipe.read(3)
    if knock == 'vsi':
      os.kill(0, signal.CTRL_C_EVENT)
      #ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, os.getpid())
    pipe.disconnect()
    pipe.close()

def handle_db(sig, frame, db_cmd=None, signal=ATTACH_SIGNAL):
  ''' signal handler part of attach/set_attach 
  
      Parameters
      ----------
      sig :
      frame :
      db_cmd : str
          The Debugger Command
      signal : var
          The Attach Signal
      '''
  if sig == signal:
    #if not hasattr(sys, 'ps1'): #If not interactive
    if db_cmd:
      db_cmd()
    else: #default behavior
      set_trace(frame)

class PostMortemHook(object):
  original_excepthook = None

  @staticmethod
  def dbclear_if_error():
    if PostMortemHook.original_excepthook != None:
      sys.excepthook = PostMortemHook.original_excepthook
      PostMortemHook.original_excepthook = None

  @classmethod
  def dbstop_if_error(cls, interactive=False, *args, **kwargs):
    ''' Parameters
        ----------
        cls : array_like
            Colors
        interactive : bool
            True if interactive. False if not.
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        '''

    if PostMortemHook.original_excepthook == None:
      PostMortemHook.original_excepthook = sys.excepthook
    cls.set_post_mortem(interactive, *args, **kwargs)

  @staticmethod
  def set_post_mortem(interactive=False):
    ''' Overrite this function for each debugger

        Parameters
        ----------
        interactive : bool
            True if interactive. False if not.

        Raises
        ------
        Exception
            Makes users aware that this is purely a virtual function
    '''
    raise Exception('Purely virtual function')

class DbStopIfErrorGeneric(object):
  ''' With statement for local dbstop situations '''

  ignore_exception = False

  def __init__(self, threading_support=False, *args, **kwargs):
    self.args = args
    self.kwargs = kwargs

    ''' Parameters
        ----------
        threading_support : bool
            Optional. Support the threading module and patch a bug preventing catching 
            exceptions in other threads. See add_threading_excepthook for more 
            info. Only neccesary if you want to catch exceptions not on the 
            main thread. This is only patched after __enter__ unpatched at 
            __exit__
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
            

        All other args from db_stop_if_error()
        '''
    self.threading_support=threading_support

  def __enter__(self):
    if self.threading_support:
      import threading
      self.threading_init = threading.Thread.__init__
      add_threading_excepthook()

      self.original_excepthook = sys.excepthook
      self.get_post_mortem_class().set_post_mortem(*self.args, **self.kwargs)

  def __exit__(self, exc_type, exc_value, tb):
    ''' Parameters
        ----------
        exc_type : str
            The Execption Type
        exc_value : float
            The Exception Value
        tb : str
            The Traceback
        '''
    if self.threading_support:
      import threading
      threading.Thread.__init__ = self.threading_init
      sys.excepthook = self.original_excepthook

    if tb is not None:
      print('Exception detected!!!')
      pm = self.get_post_mortem()
      pm(tb, *self.args, **self.kwargs)
      if self.ignore_exception:
        return True

  def get_post_mortem(self):
    ''' Returns
        -------
        func
            Should return a function that takes a traceback as the first 
            argument and any additional args/kwargs sent to __init__ after that
        
        Raises
        ------
        Exception
            For a virtual function
        '''
    raise Exception('Purely virtual function')

  @classmethod
  def set_continue_exception(cls):
    ''' Continue running code after exception

        Parameters
        ---------
        cls : bool
            True to continue to run code after the exception. Default: False.


        After the with statement scope fails, if this is called, python will
        continue running as if there was no error. Can be useful, can also be
        dangerous. So don't abuse it!'''
    cls.ignore_exception = True

def dbstop_exception_hook(type, value, tb,
                          post_mortem,
                          interactive=False):
    ''' Parameters
        ----------
        type :
        value :
        tb : str
            The Traceback
        post_mortem : 
        Interactive : bool
            True if interactive. False if not.
        '''
    if not interactive and (hasattr(sys, 'ps1') or not sys.stderr.isatty()):
    # we are in interactive mode or we don't have a tty-like
    # device, so we call the default hook
      sys.__excepthook__(type, value, tb)
    else:
      #we are NOT in interactive mode, print the exception
      traceback.print_exception(type, value, tb)
      # ...then start the debugger in post-mortem mode.
      post_mortem(tb)

def break_pool_worker():
  ''' Setup the ThreadPool to break when an exception occurs (so that it can
      be debugged)

      The ThreadPool class (and the Pool class too, but not useful here)
      always catches any exception and raises it in the main thread. This
      is nice for normal behavior, but for debugging, it makes it impossible
      to do post mortem debugging. In order to automatically attach a post
      mortem debugger, the exception has to be thrown. An exception being
      thrown WILL BREAK the pool call, and not allow your main function to
      continue, however you can now attach a debugger post_mortem. Useful
      with dbstop_if_error

      Threading has a "bug" where exceptions are also automatically caught.
      http://bugs.python.org/issue1230540
      In order to make THIS work, call add_threading_excepthook too

      Example::

          >>> from multiprocessing.pool import ThreadPool
          >>> import vsi.tools.vdb as vdb
          >>> def a(b):
          ...   print(b)
          ...   if b==3:
          ...     does_not_exist()
          >>> vdb.dbstop_if_error()
          >>> vdb.break_pool_worker()
          >>> vdb.add_threading_excepthook()
          >>> tp = ThreadPool(3)
          >>> tp.map(a, range(10))
      '''
  import multiprocessing.pool

  def worker(inqueue, outqueue, initializer=None, initargs=(), maxtasks=None):
    '''
    Parameters
    ----------
    inqueue :
    outqueue :
    initializer :
    initargs : array_like
        The Initial Argurments
    maxtasks : int
        The Maximum Number of Tasks

    Raises
    ------
    EOFError
    IOError
    Exception
    '''
    assert maxtasks is None or (type(maxtasks) == int and maxtasks > 0)
    put = outqueue.put
    get = inqueue.get
    if hasattr(inqueue, '_writer'):
      inqueue._writer.close()
      outqueue._reader.close()

    if initializer is not None:
      initializer(*initargs)

    completed = 0
    while maxtasks is None or (maxtasks and completed < maxtasks):
      try:
        task = get()
      except (EOFError, IOError):
        multiprocessing.pool.debug('worker got EOFError or IOError -- exiting')
        break

      if task is None:
        multiprocessing.pool.debug('worker got sentinel -- exiting')
        break

      job, i, func, args, kwds = task
#      try:
      result = (True, func(*args, **kwds))
#      except Exception as e:
#        result = (False, e)
      try:
        put((job, i, result))
      except Exception as e:
        wrapped = multiprocessing.pool.MaybeEncodingError(e, result[1])
        multiprocessing.pool.debug("Possible encoding error while sending result: %s" % (wrapped))
        put((job, i, (False, wrapped)))
      completed += 1
    multiprocessing.pool.debug('worker exiting after %d tasks' % completed)
  multiprocessing.pool.worker = worker

def add_threading_excepthook():
  """
  Workaround for sys.excepthook thread bug
  From
  http://spyced.blogspot.com/2007/06/workaround-for-sysexcepthook-bug.html

  (https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470).
  Call once from __main__ before creating any threads.
  If using psyco, call psyco.cannotcompile(threading.Thread.run)
  since this replaces a new-style class method.

  Raises
  ------
  KeyboardInterrupt
  SystemExit
  """
  import threading, sys
  init_old = threading.Thread.__init__
  def init(self, *args, **kwargs):
    ''' Parameters
        ----------
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.
        '''
    import sys
    init_old(self, *args, **kwargs)
    run_old = self.run
    def run_with_except_hook(*args, **kw):
      ''' Parameters
          ----------
          *args
              Variable length argument list.
          **kw
              Arbitrary keyword arguments.
          '''
      try:
        run_old(*args, **kw)
      except (KeyboardInterrupt, SystemExit):
        raise
      except:
        sys.excepthook(*sys.exc_info())
    self.run = run_with_except_hook
  threading.Thread.__init__ = init

def main():
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--pid', '-p', type=int, default=None)
  db = parser.add_mutually_exclusive_group(required=False)
  db.add_argument('--rpdb2', '-r', default=False, action='store_true',
                  help='Attach using rpdb2')
  db.add_argument('--rpdb', default=False, action='store_true',
                  help='Attach using rpdb (Client not implemented, use putty)')
  db.add_argument('--winpdb', '--gui', '-g', default=False, action='store_true',
                  help='Attach using winpdb')
  parser.add_argument('--ip', default='127.0.0.1',
                      help='Set ip address for rpdb/rpdb2/winpdb to attach on')
  parser.add_argument('--port', default=4444, type=int,
                      help='Set port for rpdb to attach on')
  parser.add_argument('--password', '--pw', default='vsi')
  parser.add_argument('args', nargs='*',
                      help='Command to run with vdb attached. Not implemented yet')
  args = parser.parse_args()

  if args.pid:
    #attach to a pid
    if args.rpdb2 or args.winpdb:
      from .vdb_rpdb2 import attach as rpdb2_attach
      rpdb2_attach(args.pid, password=args.password, ip=args.ip, gui=args.winpdb)
    elif args.rpdb:
      from .vdb_rpdb import attach as rpdb_attach
      rpdb_attach(args.pid, ip=args.ip, port=args.port)
    else:
      attach(args.pid)
  else:
    pass #Do whatever pdb does to run the command
    #Copy pdb.main or ipdb.main

if __name__=='__main__':
  main()