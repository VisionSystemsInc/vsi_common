from __future__ import print_function # Python2 compat

from functools import wraps, update_wrapper, WRAPPER_UPDATES, WRAPPER_ASSIGNMENTS
from inspect import isclass
import sys

class Try(object):
  ''' Try catch helper for cases when you want to ignore certain exceptions

      Attributes
      ----------
      default_ignore : array_like
        Arguments of Exception classes is set to ignore. Default is all.
      *other_ignore : str
      '''

  def __init__(self, default_ignore=Exception, *other_ignore):
    ''' Arguments of Exception classes to ignore. Default is all

        Parameters
        ----------
        *ignore_exceptions : exception class
            Exception classes to be ignored. Default is all.
        '''

    self.ignore = (default_ignore,) + other_ignore
  def __enter__(self):
    pass
  def __exit__(self, exc_type=None, exc_value=None, traceback=None):
    ''' Exits if the previous directory no longer exists.

    Parameters
    ----------
    exc_type : str
        The Execption Type
    exc_value : float
        The Exception Value
    traceback : str
        The Traceback

    Returns
    -------
    bool
        True if subclass
    '''

    if exc_type is None:
      return
    if issubclass(exc_type, self.ignore):
      return True

def reloadModules(pattern='.*', skipPattern='^IPython'):
  ''' Reload modules that match pattern regular expression (string or
  compile re)

  Parameters
  ----------
  pattern : str
      The regular expression pattern of modules that will be reloaded.
  skipPattern : str
      The regular expression pattern of modules that will not be reloaded.
  '''

  from types import ModuleType
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

  Parameters
  ----------
  obj : str
      type of object

  Returns
  -------
  bool
      True if object behaves like a string. False otherwise.
  """
  try:
    obj + ''
  except (TypeError, ValueError):
    return False
  return True

def get_file(fid, mode='rb'):
  ''' Helper function to take either a filename or fid

      Arguments
      ---------
      fid : str
          File object or filename
      mode :str
          Optional, file mode to open file if filename supplied
          Default rb

      Returns
      -------
      str
          The Filename
      '''

  if is_string_like(fid):
    fid = open(fid, mode)

  return fid

def static(**kwargs):
  ''' Decorator for easily defining static variables

      Parameters
      ----------
      **kwargs
          Arbitrary keyword arguments.


      Example::

            @static(count=0)
            def test(a, b):
              test.count += 1
              print(a+b, test.count)
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

  def __new__(cls, *args, **kwargs):
    if len(args)==1:
      #normal use, when decorating a decorator
      WrappedClass = args[0]
    else: # three args
      #inheritance case, when a decorated class is being inherited from
      #args = (class_name_str, (parent_class,), {'__module__': module_name})
      parents = tuple(x.__wrapped_cls__
                      if isinstance(x, OptionalArgumentDecorator)
                      else x
                      for x in args[1])
      WrappedClass = type(args[0], parents, args[2])

    __dict__ = dict(getattr(cls, '__dict__'))
    # Init is a special case, that if set before __new__ is done, then the
    # WrappedClass's init is called insted of OptionalArgumentDecorator
    __dict__.update({k:v for (k,v) in \
        getattr(WrappedClass, '__dict__', {}).items() if k != '__init__'})
    __dict__['__wrapped_cls__'] = WrappedClass

    Wrapper = type("Wrapper", (cls,), __dict__)

    if sys.version_info.major == 2:
      update_wrapper(Wrapper, WrappedClass,
          assigned = (x for x in WRAPPER_ASSIGNMENTS if x != '__doc__'),
          updated = (x for x in WRAPPER_UPDATES if x != '__dict__'))
    else:
      update_wrapper(Wrapper, WrappedClass,
          updated = (x for x in WRAPPER_UPDATES if x != '__dict__'))

    return super(OptionalArgumentDecorator, cls).__new__(Wrapper)


  def __call__(self, *args, **kwargs):
    '''
    Parameters
    ----------
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.

    Returns
    -------
    class
        The decorated class
    '''

    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
      return self.__wrapped_cls__()(args[0])
    else:
      return self.__wrapped_cls__(*args, **kwargs)

class _BasicDecorator(object):
  ''' A basic decorator class that does not take arguments

      Attributes
      ----------
      fun : func
          It gets wrapped.
      '''

  def __init__(self, fun):
    ''' No need to rewrite this

        Parameters
        ----------
        fun : func
          It gets wrapped
    '''

    self.fun = fun

  def __call__(self, *args, **kwargs):
    '''re-write this. No need to call super().__call__

       Parameters
       ----------
       *args
          Variable length argument list.
       **kwargs
            Arbitrary keyword arguments.

       Returns
       -------
       arrray_like
            The Result
    '''

    #pre wrap code
    result = self.fun(*args, **kwargs)
    #postwrap code
    return result

class _BasicArgumentDecorator(object):
  ''' A basic decorator class that takes arguments

      It's best to define __init__ with a proper signature when inheriting'''

  def __call__(self, fun):
    ''' No need to rewrite this

        Parameters
        ----------
        fun :
    '''

    @wraps(fun)
    def wrapped(*args, **kwargs):
      return self.__inner_call__(*args, **kwargs)

    self.fun = fun
    return wrapped

  def __inner_call__(self, *args, **kwargs):
    '''re-write THIS. No need for super().__inner_call__
       Parameters
       ----------
       *args
          Variable length argument list.
       **kwargs
            Arbitrary keyword arguments.
    '''

    #pre wrap code
    result = self.fun(*args, **kwargs)
    #postwrap code
    return result

# Decorated methods do not show up in sphinx unless we use functools.wraps
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

      Example::

          class MyDecor(BasicDecorator):
            def __init__(self, name='Default'):
              self.name = name
            def __inner_call__(self, first_arg, *args, **kwargs):
              result = self.fun(first_arg, *args, **kwargs)
              print(self.name, first_arg, result)
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

      Attributes
      ----------
      *args
          message
      **kwargs
          output_stream


      no arguments (no '()' either)


      Example::

          @WarningDecorator
          def my_prototype(x, y):
            print(x/y)

          @WarningDecorator('Warning: Unstable Code')
          def my_prototype(x, y):
            print(x/y)

          @WarningDecorator(output_stream=sys.stdout)
          def my_prototype(x, y):
            print(x/y)
  '''
  def __init__(self, *args, **kwargs):
    ''' Initilize decorator

        Arguments
        ---------
        *args
            message
        **kwargs
            output_stream

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
      print(self.message, file=self.output_stream)
      return self.fun(*args, **kwargs)
    else:
      self.fun = args[0]
      return self

class WarningDecorator(BasicDecorator):
  def __init__(self, message='Warning', output_stream=sys.stderr):
    self.message = message
    self.output_stream = output_stream
  def __inner_call__(self, *args, **kwargs):
    print(self.message, file=self.output_stream)
    return self.fun(*args, **kwargs)


ARGS=-1
KWARGS=-2


def args_to_kwargs(function, args=tuple(), kwargs={}):
  '''returns a single dict of all the args and kwargs

     Should handle: functions, classes (their __init__), bound and unbound
     versions of methods, class methods, and static methods. Furthermore, if a
     class instance has a __call__ method, this is used.

     It does not call the function.

     Parameters
     ----------
     function : func
        The Function
     args : tuple
     kwargs : array_like

     Returns
     -------
     dict
        The returned dictionary has the keywords that would be received in a
        real function call. Leftover args are put into the key ARGS(-1), and
        leftover KWARGS are placed in the key KWARGS(-2). While everything
        should behave exactly as python would, certain failure situations are
        not reproduced,for exampled it does not raise exception if you declare
        the same parameter in both /*/args and /**/kwargs)

     Only works for python2. need to use signature instead of getargspec for
     python3.

     Based on:
     https://github.com/merriam/dectools/blob/master/dectools/dectools.py'''

  import inspect

  pop_self = False

  args=tuple(args)

  if inspect.isclass(function):
    function = function.__init__
    args = (None,)+args #Dummy for self
    pop_self = True
  elif inspect.ismethod(function):
    #check if bound/unbound doesn't seem to matter
    #if function.im_self is not None
    if hasattr(function, '__self__'):
      #Check if class/normal method doesn't matter
      #if inspect.isclass(function.__self__):
      args = (None,)+args #Dummy for self/cls
      pop_self = True
    else:
      #static method
      pass
  elif hasattr(function, '__call__') and inspect.ismethod(function.__call__):
    function = function.__call__
    args = (None,)+args
    pop_self = True

  names, args_name, kwargs_name, defaults = inspect.getargspec(function)

  # assign basic args
  params = {}
  if args_name:
    basic_arg_count = len(names)
    params.update(zip(names[:], args))  # zip stops at shorter sequence
    params[ARGS] = args[basic_arg_count:]
  else:
    params.update(zip(names, args))

  # assign kwargs given
  if kwargs_name:
    params[KWARGS] = {}
    for kw, value in kwargs.iteritems():
      if kw in names:
        params[kw] = value
      else:
        params[KWARGS][kw] = value
  else:
      params.update(kwargs)

  # assign defaults
  if defaults:
    for pos, value in enumerate(defaults):
      if names[-len(defaults) + pos] not in params:
        params[names[-len(defaults) + pos]] = value

  # check we did it correctly.  Each param and only params are set

  assert set(params.iterkeys()) == (set(names)|
                                    set([KWARGS if kwargs_name else None,
                                         ARGS if args_name else None]) \
                                   -set([None]))
  #Remove None, since if *args/**kwargs isn't used, it will have the value None
  #And that is not used

  if pop_self:
    params.pop(names[0])

  return params

def args_to_kwargs2(function, *args, **kwargs):
  '''
     Parameters
     ----------
     *args
          Variable length argument list.
     **kwargs
          Arbitrary keyword arguments.

     Returns
     -------
     array_like
  '''
  return args_to_kwargs(function, args, kwargs)


def command_list_to_string(cmd):
  '''
    Parameters
    ----------
    cmd : list
        The Command List

    Returns
    -------
    str
        The Command List as a string
  '''
  try:
    from shlex import quote
  except:
    from pipes import quote
  return ' '.join([quote(x) for x in cmd])