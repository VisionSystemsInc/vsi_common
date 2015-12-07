import sys

class Try(object):
  ''' Try catch helper for cases when you want to ignore certain exceptions '''
  def __init__(self, default_ignore=Exception, *other_ignore):
    ''' Arguments of Exception classes to ignore. Default is all '''
    self.ignore = (default_ignore,) + other_ignore
  def __enter__(self):
    pass
  def __exit__(self, exc_type=None, exc_value=None, traceback=None):
    if exc_type is None:
      return
    if issubclass(exc_type, self.ignore):
      return True

def reloadModules(pattern='.*', skipPattern='^IPython'):
  ''' Reload modules that match pattern regular expression (string or compile re) '''

  from types import ModuleType
  import sys
  import os
  import re

  pattern = re.compile(pattern)
  skipPattern = re.compile(skipPattern)

  modules = sys.modules.keys()
  #In case something is loaded in the background, it will craete a
  #"dictionary changed size during iteration" error 

  for m in modules:
    if isinstance(sys.modules[m], ModuleType) and \
       m not in sys.builtin_module_names and \
       '(built-in)' not in str(sys.modules[m]) and \
       pattern.search(m) and \
       not skipPattern.search(m):
      with Try():
        reload(sys.modules[m])

def is_string_like(obj):
  """
  Check whether obj behaves like a string.

  Copied from numpy
  """
  try:
    obj + ''
  except (TypeError, ValueError):
    return False
  return True

def get_file(fid, mode='rb'):
  ''' Helper function to take either a filename or fid
  
      Keyword Arguments:
      fid - File object or filename
      mode - Optional, file mode to open file if filename supplied
             Default rb'''

  if is_string_like(fid):
    fid = open(fid, mode);
  
  return fid 

def static(**kwargs):
  ''' Decorator for easily defining static variables
  
      Example:
      
      @static(count=0)
      def test(a, b):
        test.count += 1
        print a+b, test.count
  '''
  def decorate(func):
    for k in kwargs:
      setattr(func, k, kwargs[k])
    return func
  return decorate

def OptionalArgumentDecorator(cls):
  ''' Decorator for easily defining a decorator class that may take arguments
      
      Write a decorator class as normal, that would always take arguments, and
      make sure they all have default values. Then just add this decorator and
      both notations will work

      @Test
      def myfun():
        pass

      @Test(17, 'ok')
      def myfun2():
        pass

      Example:

      @OptionalArgumentDecorator
      class Test(object):
        def __init__(self, arg1=15, arg2='whatever'):
          self.arg1_name = arg1
          self.arg2_name = arg2

        #@test
        def __call__(self, *args, **kwargs):
          self.fun = args[0]
          return self.__inner_call__

        def __inner_call__(self, *args, **kwargs):
          #pre wrap code
          result = self.fun(*args, **kwargs)
          #postwrap code
          return result '''
  def inner(*args, **kwargs):
    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
      return cls()(*args, **kwargs)
    else:
      return cls(*args, **kwargs)
  return inner


class WarningDecorator(object):
  ''' Decorator to add to a function to print a message out when called 
      
      Usage:

      @WarningDecorator
      def my_prototype(x, y):
        print x/y

      @WarningDecorator('Warning: Unstable Code')
      def my_prototype(x, y):
        print x/y

      @WarningDecorator(output_stream=sys.stdout)
      def my_prototype(x, y):
        print x/y

  '''
  def __init__(self, *args, **kwargs):
    ''' Initilize decorator
    
        Arguments:
          message, output_stream
         or
          no arguments (no '()' either)
    '''
    if hasattr(args[0], '__call__'): #duck typing
      self.init1(*args, **kwargs)
    else:
      self.init2(*args, **kwargs)

  def init1(self, fun):
    self.fun = fun
    self.message = 'Warning'
    self.output_stream=sys.stderr
    
  def init2(self, message='Warning', output_stream=sys.stderr):
    self.message = message
    self.output_stream = output_stream
  
  def __call__(self, *args, **kwargs):
    if hasattr(self, 'fun'):
      print >>self.output_stream, self.message
      return self.fun(*args, **kwargs)
    else:
      self.fun = args[0]
      return self
