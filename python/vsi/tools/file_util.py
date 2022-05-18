import os
import shutil
import tempfile
import functools

def lncp(source, dest):
  ''' Symlink or copy if that fails. Should work for Linux and Windows

      Parameters
      ----------
      source : str
        The Source
      dest : str
          The Destination

  '''

  if os.path.isdir(dest):
    dest = os.path.join(dest, os.path.basename(source))

  try:
    os.symlink(source, dest)
  except:
    shutil.copyfile(source, dest)

def _path_or_temp(kwarg_key, kwarg_func=lambda temp_dir: temp_dir):
  '''
  Decorator to replace a missing kwarg (missing, empty, or ``None``) that
  defines a path with a valid temporary path.
  '''
  def inner(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):

      # named kwarg key
      kwarg_value = kwargs.get(kwarg_key)

      # temporary file
      if not kwarg_value:
        with tempfile.TemporaryDirectory() as temp_dir:
          kwargs[kwarg_key] = kwarg_func(temp_dir)
          return func(*args, **kwargs)

      # defined file - call with original kwargs
      else:
        return func(*args, **kwargs)

    return wrapper
  return inner

def file_or_temp(kwarg_key, filename):
  '''
  Decorator to replace a missing kwarg (missing, empty, or ``None``) that
  defines a file with a filename in a valid temporary directory.

  The temporary directory intended to contain the temporary file will be
  created on entering the decorated function, and the directory & its contents
  will be deleted on exiting the decorated function.

  The decorated function is expected to create the file itself.
  '''
  kwarg_func = lambda temp_dir: os.path.join(temp_dir, filename)
  return _path_or_temp(kwarg_key, kwarg_func)
