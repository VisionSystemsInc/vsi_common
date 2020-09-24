from __future__ import print_function # Python2 compat

from functools import (wraps, update_wrapper, WRAPPER_UPDATES,
                       WRAPPER_ASSIGNMENTS)

from collections.abc import Mapping, Iterable
import inspect
import sys

import logging
logger = logging.getLogger(__name__)

class Try(object):
  ''' Try catch helper for cases when you want to ignore certain exceptions

  Parameters
  ----------
  *ignore_exceptions : Exception
      Exception classes to be ignored. Default is all.
  '''

  def __init__(self, default_ignore=Exception, *other_ignore):
    self.ignore = (default_ignore,) + other_ignore

  def __enter__(self):
    pass

  def __exit__(self, exc_type=None, exc_value=None, traceback=None):
    if exc_type is None:
      return
    if issubclass(exc_type, self.ignore):
      return True

class ArgvContext:
  ''' Context to temporarily change the ``sys.argv`` variable

  Parameters
  ----------
  *args : str
      Arguments to replace ``sys.argv``, starting with ``argv[0]``
  '''
  def __init__(self, *args):
    self.args = args

  def __enter__(self):
    self.old_args = sys.argv
    sys.argv = list(self.args)

  def __exit__(self, *args):
    sys.argv = self.old_args

def reloadModules(pattern='.*', skipPattern='^IPython'):
  ''' Reload modules that match pattern regular expression (string or re)

  Parameters
  ----------
  pattern : str or re.Pattern
      The regular expression pattern of modules that will be reloaded.
  skipPattern : str or re.Pattern
      The regular expression pattern of modules that will not be reloaded.
  '''

  from types import ModuleType
  import os
  import re

  pattern = re.compile(pattern)
  skipPattern = re.compile(skipPattern)

  modules = sys.modules.keys()
  #In case something is loaded in the background, it will create a
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
  """ Check whether obj behaves like a string.

  Copied from numpy

  Parameters
  ----------
  obj : object
      Object being tested for string like behavior

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

  Parameters
  ----------
  fid : str
      File object or filename
  mode : :class:`str`, optional
      Optional, file mode to open file if filename supplied
      Default is 'rb'

  Returns
  -------
  :term:`file-like object`
      The opened file object
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

  # Note: don't need functools.wraps, since I'm returning the same func
  def decorate(func):
    for k in kwargs:
      setattr(func, k, kwargs[k])
    return func
  return decorate

def update_wrapper_class(wrapper, wrapped):
  '''functools.update_wrapper for classes

  Version of ``functools.update_wrapper`` that works when the wrapper is a
  class

  Parameters
  ----------
  wrapper : :term:`class`
      The class to be updated
  wrapped : :term:`class`
      The original function/class

  Returns
  -------
  :term:`class`
      A subclass of ``wrapper`` that has the updated attributes. If ``wrapped``
      was a function, ``wrapper`` is still a class.
  '''

  __dict__ = dict(getattr(wrapper, '__dict__'))
  # Init is a special case, that if set before __new__ is done, then the
  # wrapped's init is called insted of OptionalArgumentDecorator
  __dict__.update({k:v for (k,v) in \
      getattr(wrapped, '__dict__', {}).items() if k != '__init__'})
  __dict__['__wrapped__'] = wrapped

  Wrapper = type("Wrapper", (wrapper,), __dict__)

  if sys.version_info.major == 2:
    update_wrapper(Wrapper, wrapped,
        assigned = (x for x in WRAPPER_ASSIGNMENTS if x != '__doc__'),
        updated = (x for x in WRAPPER_UPDATES if x != '__dict__'))
  else:
    update_wrapper(Wrapper, wrapped,
        updated = (x for x in WRAPPER_UPDATES if x != '__dict__'))

  return Wrapper

def _meta_generate_class(cls, *args, **kwargs):
  '''Determine class to use for decorators

  Parameters
  ----------
  cls : :term:`class`
      The class of the decorator type
  args : tuple
      The arguments passed to the decorate, when decorating a class
  kwargs : dict
      The keyword arguments passed to the decorate, when decorating a class


  Helper function to parse the arguments from a class's __new__ or __init__
  to handle both the normal case, and when the class is being inherited by
  another class::

      class A:
        def __new__(cls, *args):
          return super(A, cls).__new__(_meta_generate_class(A, *args))
      @A
      class B():
        pass
      class C(B):
        pass

  When B is decorated by A, ``A.__new__/__init__`` is called with 1 argument,
  ``B``.
  When C inherits from B, ``A.__new__/__init__`` is called with 3 arguments
  instead of one, the 3 arguments to a ``type()`` call.

  This helper will run all that logic for you, and just always return the class
  you need.
  '''

  if len(args)==1:
    #normal use, when decorating a decorator
    return args[0]
  else: # three args
    #inheritance case, when a decorated class is being inherited from
    #args = (class_name_str, (parent_class,), {'__module__': module_name})
    parents = tuple(x.__wrapped__
                    if isinstance(x, cls)
                    else x
                    for x in args[1])
    return type(args[0], parents, args[2])

class OptionalArgumentDecorator(object):
  ''' Decorator for easily defining a decorator class that may take arguments

  Write a decorator class as normal, that would always take arguments, and
  make sure they all have default values. Then decorate that decorator with
  this decorator and both ``@decorator`` and ``@decorator()`` notations will
  work.

  See Also
  --------
  BasicDecorator : Simple decorator with optional arguments
  '''

  def __new__(cls, *args, **kwargs):
    WrappedClass = _meta_generate_class(cls, *args, **kwargs)
    return super(OptionalArgumentDecorator, cls).__new__(
      update_wrapper_class(cls, WrappedClass))

  def __call__(self, *args, **kwargs):
    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
      return self.__wrapped__()(args[0])
    else:
      return self.__wrapped__(*args, **kwargs)

class _BasicDecorator(object):
  ''' A basic decorator class that does not take arguments

  Parameters
  ----------
  fun : :term:`function`
      The function that gets wrapped

  Attributes
  ----------
  fun : :term:`function`
      The function that is being wrapped

  Examples
  --------
  Usage::

      class MyDecorAdd1(_BasicDecorator):
        def __call__(self, *args, **kwargs):
          result = self.fun(*args, **kwargs)
          res

      @MyDecorAdd1
      def fun(a, b=2):
        return a+b
  '''

  fun = None

  def __new__(cls, *args, **kwargs):
    WrappedClass = _meta_generate_class(cls, *args, **kwargs)
    # In python3, the use of "_BasicDecorator" can be "__class__" instead, but
    # must not be "cls", that won't work
    return super(_BasicDecorator, cls).__new__(
        update_wrapper_class(cls, WrappedClass))

  def __init__(self, fun):
    ''' No need to rewrite this in the child class
    '''

    self.fun = fun
    update_wrapper(self, fun)

  def __call__(self, *args, **kwargs):
    '''Re-write this. Do need to call ``super().__call__``

    The general idea of this class is you re-write the ``__call__`` method to
    do what you want, and call ``self.fun`` and return the result. This can
    be accomplished by ``return super().__call__(*args, **kwargs)``, but more
    often then not, you will want the result of ``self.fun``, and will call
    ``result = self.fun(*args, **kwargs)`` yourself, and then ``return result``
    '''

    #pre wrap code
    result = self.fun(*args, **kwargs)
    #postwrap code
    return result

class _BasicArgumentDecorator(object):
  ''' A basic decorator class that takes arguments

      It's best to define __init__ with a proper signature when inheriting
  '''

  def __call__(self, fun):
    ''' No need to rewrite this

        Parameters
        ----------
        fun : :term:`function`
          The Function
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

class WarningDecorator(BasicDecorator):
  def __init__(self, message='Warning', output_stream=sys.stderr):
    self.message = message
    self.output_stream = output_stream
  def __inner_call__(self, *args, **kwargs):
    print(self.message, file=self.output_stream)
    return self.fun(*args, **kwargs)

# Fix of https://gist.github.com/MacHu-GWU/0170849f693aa5f8d129aa03fc358305
def __is__method(cls, attribute, kind, exceptions):
  value = getattr(cls, attribute)

  if attribute in exceptions:
    return True

  if inspect.isclass(cls):
    for cls in inspect.getmro(cls):
      if inspect.isroutine(value): # No else, no builtin statics?
        if attribute in cls.__dict__:
          if isinstance(cls.__dict__[attribute], kind):
            return True
          else:
            return False
  else: # class instance
    if attribute in cls.__dict__:
      value = cls.__dict__[attribute]
    elif attribute in type(cls).__dict__:
      value = type(cls).__dict__[attribute]
    else:
      return False

    if isinstance(value, kind):
      return True
    else:
      return False

  return False

def is_static_method(cls, attribute):
  ''' Returns whether the attribute refers to a staticmethod or not

      Parameters
      ----------
      cls : object
          The class/instance being checked
      attribute : str
          The name of the function to be checked

      Returns
      -------
      bool
          True if the attribute is a static function, else false if anything
          else
  '''
  return __is__method(cls, attribute, staticmethod,
      # https://docs.python.org/3.7/reference/datamodel.html#object.__new__
      ('__new__',))

def is_class_method(cls, attribute):
  return __is__method(cls, attribute, classmethod,
      # https://docs.python.org/3/library/abc.html#abc.ABCMeta.__subclasshook__
      ('__subclasshook__',))


class ARGS:
  pass

class KWARGS:
  pass

# REVIEW When we no longer support python2, this function should be updated to
# use the newer inspect.signature, Signature.bind() and
# BoundArguments.apply_defaults() instead of inspect.getfullargspec
def args_to_kwargs(function, args=tuple(), kwargs={}):
  '''returns a single dict of all the args and kwargs

     Should handle: functions, classes (their __init__), bound and unbound
     versions of methods, class methods, and static methods. Furthermore, if a
     class instance has a __call__ method, this is used.

     It does not call the function.

     Parameters
     ----------
     function : :term:`function`
         The Function
     args : tuple
     kwargs : dict

     Returns
     -------
     dict
         The returned dictionary has the keywords that would be received in a
         real function call. Leftover args are put into the key ARGS, and
         leftover KWARGS are placed in the key KWARGS. While everything
         should behave exactly as python would, certain failure situations are
         not reproduced, for exampled it does not raise exception if you
         declare the same parameter in both /*/args and /**/kwargs)

     On python3, ``args_to_kwargs_unbound`` must be used for unbound class
     methods

     Based on:
     https://github.com/merriam/dectools/blob/master/dectools/dectools.py
  '''

  return args_to_kwargs_unbound(function, None, args, kwargs)

def args_to_kwargs_unbound(function, attribute=None, args=tuple(), kwargs={}):

  # Clean up the inputs

  pop_first = False
  args=tuple(args)

  if attribute:
    parent = function
    function = getattr(function, attribute)
  else:
    parent = None

  if inspect.isclass(function):
    function = function.__init__
    args = (None,)+args #Dummy for self
    pop_first = True
  # Check for bound function or class function, both treated the same
  elif inspect.ismethod(function):
    if hasattr(function, '__self__'):
      #if it has a __self__, then it is a class/normal method (not static)
      args = (None,)+args #Dummy for self/cls
      pop_first = True
  # Check to see if it is a class instance with __call__. Only class
  # instanaces can have bound methods in python3
  elif hasattr(function, '__call__') and inspect.ismethod(function.__call__):
    function = function.__call__
    args = (None,)+args
    pop_first = True
  # This is how to handle unbound functions
  elif parent:
    if not is_static_method(parent, attribute):
      # Must be class/normal method
      args = (None,)+args
      pop_first = True

  ############
  # Parse args
  ############

  kwonly_args_names = []
  kwonly_defaults = None
  annotations = {}

  try:
    args_names, extra_args_name, extra_kwargs_name, defaults, \
        kwonly_args_names, kwonly_defaults, annotations = \
        inspect.getfullargspec(function)
  except:
    args_names, extra_args_name, extra_kwargs_name, defaults = \
        inspect.getargspec(function)

  # assign basic args
  params = dict(zip(args_names, args))  # zip stops at shorter sequence
  if extra_args_name:
    params[ARGS] = args[len(args_names):]
  elif len(args_names) < len(args):
      logger.warning("args_to_kwargs: Too many positional arguments specified")

  # assign kwargs given
  if extra_kwargs_name:
    params[KWARGS] = {}
  for keyword, value in kwargs.items():
    if keyword in args_names + kwonly_args_names:
      params[keyword] = value
    else:
      if extra_kwargs_name:
        params[KWARGS][keyword] = value
      else:
        logger.warning("args_to_kwargs: Unspecified keyword argument '%s' "
                       "used", keyword)
        params[keyword] = value

  # assign defaults
  if defaults:
    for pos, value in enumerate(defaults):
      if args_names[-len(defaults) + pos] not in params:
        params[args_names[-len(defaults) + pos]] = value

  # assign keyword only defaults
  if kwonly_defaults:
    for key, value in kwonly_defaults.items():
      if key not in params:
        params[key] = value

  # check we did it correctly.  Each param and only params are set
  if set(params.keys()) != (set(args_names)|set(kwonly_args_names)|
                            set([KWARGS if extra_kwargs_name else None,
                                 ARGS if extra_args_name else None]) -
                            set([None])):
  #Remove None, since if *args/**kwargs isn't used, it will have the value None
  #And that is not used
    logger.warning("args_to_kwargs: Number of named arguments used does not "
                   "equal arguments parsed. This can mean you are "
                   "missing required arguments")

  if pop_first:
    params.pop(args_names[0])

  return params

# def args_to_kwargs_easy(function, *args, **kwargs):
def args_to_kwargs_easy(*args, **kwargs):
  '''
     Parameters
     ----------
     *args : tuple
          Variable length argument list.
     **kwargs : dict
          Arbitrary keyword arguments.

     Returns
     -------
     dict
  '''
  return args_to_kwargs(args[0], args[1:], kwargs)

# def args_to_kwargs_unbound_easy(function, attribute, *args, **kwargs):
def args_to_kwargs_unbound_easy(*args, **kwargs):
  '''
     Parameters
     ----------
     *args : tuple
          Variable length argument list.
     **kwargs : dict
          Arbitrary keyword arguments.

     Returns
     -------
     dict
  '''
  return args_to_kwargs_unbound(args[0], args[1], args[2:], kwargs)

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

def nested_update(dict_, *args, **kwargs):
  ''' Updated a dictionary in a nested fashion

  Parameters
  ----------
  dict_ : dict
      The dict to be updated
  *args : tuple
      Same arguments as dict.update
  **kwargs : dict
      Same arguments as dict.update
  '''

  # patch iterables
  def patch_it(v):
                   # Handle Mappings
    return type(v)(type(dict_)(item)
                   if isinstance(item, Mapping)
                   and not isinstance(item, type(dict_))
                   # Handle Iterables
                   else patch_it(item)
                   if isinstance(item, Iterable)
                   and not isinstance(item, str)
                   # Handle Everything else
                   else item
                   # Loop through v items
                   for item in v)

  # Don't use dict comprehension (I forget why, readability?) or constructor
  # here (infinite recursion)!
  for key, value in dict(*args, **kwargs).items():
    if isinstance(value, Mapping):
      dict_[key] = nested_update(dict_.get(key, type(dict_)()), value)
    elif isinstance(value, Iterable) and not isinstance(value, str):
      dict_[key] = patch_it(value)
    else:
      dict_[key] = value

  return dict_

def nested_in_dict(dict1, dict2):
  ''' Checks to see if dict1 is in dict2

  Parameters
  ----------
  dict1 : dict
      Subset dictionary
  dict2 : dict
      Superset dictionary
  '''

  try:
    items = dict1.iteritems()
  except:
    items = dict1.items()

  for key, value1 in items:
    if key not in dict2:
      return False
    if isinstance(value1, Mapping):
      if not nested_in_dict(value1, dict2[key]):
        return False
    elif dict2[key] != value1:
        return False

  return True

def nested_patch(obj, condition, patch, _spare_key = None):
  ''' Patch strings in a nested python dict

  Will patch values in mapping and iterable containers recursively. This
  includes (but is not limited to) ``set``, ``list``, ``dict``, ``tuple``,
  etc... Only iterates through values, not keys.

  When the condition is met for a given key,value pair, then the patch function
  is used to replace the value.

  Parameters
  ----------
  obj: :term:`mapping` or :term:`iterable` or object
      The python object to be patched. Typically a dict, but can be a list,
      etc... or even a normal object, but that kind of defeats the purpose
  condition: :term:`function`
      The condition function to decide if each value should be patched.
      ``condition`` takes two arguments, ``(key, value)``
  patch: :term:`function`
      Callable that should return a patched version of the value. ``patch``
      takes two arguments, ``(key, value)``

  Returns
  -------
  object
      Returns a patched version of the object. This should not be though of as
      a deep-copy of the original object, as unpatched values will still be the
      same python objects, not copies.

  Example
  -------

  ::

      patterns = ['_file', '_dir', '_path',
            '_files', '_dirs', '_paths']
      condition = lambda key, value: isinstance(key, str) and \\
                  any(key.endswith(pattern) for pattern in patterns)

      def patch_value(value, volume_map):
        for vol_from, vol_to in volume_map:
          if isinstance(value, str) and value.startswith(vol_from):
            return value.replace(vol_from, vol_to, 1)
        return value

      volume_map = [['/tmp', '/temp'],
                    ['/tmp/home', '/nope'],
                    ['/home', '/Home']]
      patch = lambda key, value: patch_value(value, reversed(volume_map))

      z = {'test': '/tmp',
          'foo_file': '/tmp',
          'foo': 15,
          17: 'bar',
          'foo_dir': ['/tmp', '/home'],
          'foo_files': 15,
          'stuff': {
            'this_path': '/home',
            'a': {
              'b': {
                'c': {
                  'e': [{'b_path': '/home'}, {'c_dir': '/tmp'}],
                  'd': {
                    'q_path': (('/home', '/opt'), ('/tmp', '/tmp/home/foo/bar')),
                    'q_orig': (('/home', '/opt'), ('/tmp', '/tmp/home/foo/bar')),
                    'a_path': ('/home', '/opt', '/tmp', '/tmp/home/foo/bar')
                  }
                }
              }
            }
          }
          }

      z2 = nested_patch(z, condition, patch)
  '''

  # Handle mapping
  if isinstance(obj, Mapping):
    # Muttable mappings could be in-place patched, but for symmetry and DRY,
    # just return it like everything else, plus this would work on an immutable
    # mapping should one ever be used?
    return type(obj)((key,nested_patch(value, condition, patch, key)) \
                     for key,value in obj.items())

  # Handle iterables
  elif not isinstance(obj, str) and isinstance(obj, Iterable):
    return type(obj)(nested_patch(val, condition, patch, _spare_key) \
                     for val in obj)

  # Handle everything else
  else:
    if condition(_spare_key, obj):
      return patch(_spare_key, obj)
    return obj

def nested_patch_inplace(obj, condition, patch, _spare_key = None):
  ''' Destructive inplace version of :func:`vsi.tools.python.nested_patch`
  '''
  # Handle mapping
  if isinstance(obj, Mapping):
    for key, value in obj.items():
      if isinstance(value, Mapping):
        nested_patch_inplace(value, condition, patch) # Inplace
      # This would work but adds extra recursions and tests
      # else:
      #   obj[key] = nested_patch_inplace(value, condition, patch, key)
      elif not isinstance(value, str) and isinstance(value, Iterable):
        obj[key] = nested_patch_inplace(value, condition, patch, key)
      elif condition(key, value):
        obj[key] = patch(key, value)
    return obj
  # Handle iterable
  elif not isinstance(obj, str) and isinstance(obj, Iterable):
    return type(obj)(nested_patch_inplace(val, condition, patch, _spare_key) for val in obj)
  # Handle everything else
  else:
    if condition(_spare_key, obj):
      return patch(_spare_key, obj)
    return obj

def unwrap_wraps(func):
  '''
  Unwraps a wrapped function

  Finds the originally wrapped function, using the :func:`functools.wraps`
  pattern of storing in ``__wrapped__``
  '''

  is_method = inspect.ismethod(func)

  try:
    while func.__wrapped__:
      func = func.__wrapped__
      # It only takes one to be a method
      if inspect.ismethod(func):
        is_method = True
  except AttributeError:
    pass
  return (func, is_method)