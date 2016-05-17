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

class OptionalArgumentDecorator(object):
  ''' Decorator for easily defining a decorator class that may take arguments
      
      Write a decorator class as normal, that would always take arguments, and
      make sure they all have default values. Then just add this decorator and
      both notations will work

      '''
  def __init__(self, *args):
    if len(args)==1:
      #normal use
      self.cls = args[0]
    else:
      #inheritance 
      #args = (class_name_str, (parent_class,), {'__module__': module_name})
      parents = tuple(x.cls if type(x) == OptionalArgumentDecorator else x 
                      for x in args[1])
      self.cls = type(args[0], parents, args[2])

  def __call__(self, *args, **kwargs):
    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
      return self.cls()(args[0])
    else:
      return self.cls(*args, **kwargs)

class _BasicDecorator(object):
  ''' A basic decorator class that does not take arguments'''
  def __init__(self, fun):
    ''' No need to rewrite this '''
    self.fun = fun

  def __call__(self, *args, **kwargs):
    '''re-write this. No need for super'''
    #pre wrap code
    result = self.fun(*args, **kwargs)
    #postwrap code
    return result

class _BasicArgumentDecorator(object):
  ''' A basic decorator class that takes arguments

      It's best to define __init__ with a proper signature when inheriting'''

  def __call__(self, fun):
    ''' No need to rewrite this '''
    self.fun = fun
    return self.__inner_call__

  def __inner_call__(self, *args, **kwargs):
    '''re-write this. No need for super'''
    #pre wrap code
    result = self.fun(*args, **kwargs)
    #postwrap code
    return result

@OptionalArgumentDecorator
class BasicDecorator(_BasicArgumentDecorator):
  ''' A basic decorator class that can optionally take arguments

      It's best to define __init__ with a proper signature when inheriting

      Define __inner_call__(self, *args, **kwargs) to add your wrapper magic

      Usage: Define a new class that inherits from OptionalArgumentDecorator.
      There is logic to support inheritance as long as the classes are 
      decorated by OptionalArgumentDecorator ONLY. Any additional decorators
      will probably break the inheritance logic. If this is needed, than 
      inherit from _BasicArgumentDecorator instead and Add the 
      @OptionalArgumentDecorator decorator yourself, and don't inherit from 
      that.

      Example:

      class MyDecor(BasicDecorator):
        def __init__(self, name='Default'):
          self.name = name
        def __inner_call__(self, first_arg, *args, **kwargs):
          result = self.fun(first_arg, *args, **kwargs)
          print self.name, first_arg, result
          return result
          
      @MyDecor
      def test1(x, y):
        return x+y

      @MyDecor('not default')
      def test2(x, y):
        return x+y

      test1(11,22)
      test2(10,2)

      '''

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

def args_to_kwargs(function, args, kwargs):
  '''return a dict of all the args and kwargs as the keywords they would
     be received in a real function call.  It does not call function.
     
     Only works for python2. need to use signature instead of getargspec for 
     python3.
     
     Based on:
     https://github.com/merriam/dectools/blob/master/dectools/dectools.py'''

  import inspect

  if inspect.isclass(function):
    function = function.__init__
    args = (None,)+args #Dummy for self
  #TODO
  #handle bound function
  #handle unbound function
  #handle instance with __call__
  #handle static method
  #handle class method
  #elif hasattr(function, '__call__'):
  #  func = function.__call__
  #  function = (None,)+args
    
  names, args_name, kwargs_name, defaults = inspect.getargspec(function)
    
  # assign basic args
  params = {}
  if args_name:
    basic_arg_count = len(names)
    params.update(zip(names[:], args))  # zip stops at shorter sequence
    params[args_name] = args[basic_arg_count:]
  else:
    params.update(zip(names, args))

  # assign kwargs given
  if kwargs_name:
    params[kwargs_name] = {}
    for kw, value in kwargs.iteritems():
      if kw in names:
        params[kw] = value
      else:
        params[kwargs_name][kw] = value
  else:
      params.update(kwargs)

  # assign defaults
  if defaults:
    for pos, value in enumerate(defaults):
      if names[-len(defaults) + pos] not in params:
        params[names[-len(defaults) + pos]] = value

  # check we did it correctly.  Each param and only params are set
  assert set(params.iterkeys()) == (set(names)|set([args_name])|set([kwargs_name])
                                    )-set([None])

  return params

def command_list_to_string(cmd):
  try:
    from shlex import quote
  except:
    from pipes import quote
  return ' '.join([quote(x) for x in cmd])