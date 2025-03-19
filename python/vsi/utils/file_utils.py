""" Utility Functions for common file operations """
import functools
import glob
import os
import sys
import re
import shutil
import stat
import tempfile

import logging
logger = logging.getLogger(__name__)


def rmtree(path, ignore_errors=False, onerror=None, rmdir=True):
  ''' shutil.rmtree with the ability to keep top dir '''
  if ignore_errors:
    def onerror(*args):
      pass
  elif onerror is None:
    def onerror(*args):
      raise
  if shutil._use_fd_functions:
    # While the unsafe rmtree works fine on bytes, the fd based does not.
    if isinstance(path, bytes):
      path = os.fsdecode(path)
    # Note: To guard against symlink races, we use the standard
    # lstat()/open()/fstat() trick.
    try:
      orig_st = os.lstat(path)
    except Exception:
      onerror(os.lstat, path, sys.exc_info())
      return
    try:
      fd = os.open(path, os.O_RDONLY)
    except Exception:
      onerror(os.lstat, path, sys.exc_info())
      return
    try:
      if os.path.samestat(orig_st, os.fstat(fd)):
        shutil._rmtree_safe_fd(fd, path, onerror)
        if rmdir:
          try:
            os.rmdir(path)
          except OSError:
            onerror(os.rmdir, path, sys.exc_info())
      else:
        try:
          # symlinks to directories are forbidden, see bug #1669
          raise OSError("Cannot call rmtree on a symbolic link")
        except OSError:
          onerror(os.path.islink, path, sys.exc_info())
    finally:
      os.close(fd)
  else:
    return _rmtree_unsafe(path, onerror, rmdir)


# version vulnerable to race conditions
def _rmtree_unsafe(path, onerror, rmdir=True):
  try:
    if os.path.islink(path):
      # symlinks to directories are forbidden, see bug #1669
      raise OSError("Cannot call rmtree on a symbolic link")
  except OSError:
    onerror(os.path.islink, path, sys.exc_info())
    # can't continue even if onerror hook returns
    return
  names = []
  try:
    names = os.listdir(path)
  except OSError:
    onerror(os.listdir, path, sys.exc_info())
  for name in names:
    fullname = os.path.join(path, name)
    try:
      mode = os.lstat(fullname).st_mode
    except OSError:
      mode = 0
    if stat.S_ISDIR(mode):
      _rmtree_unsafe(fullname, onerror)
    else:
      try:
        os.unlink(fullname)
      except OSError:
        onerror(os.unlink, fullname, sys.exc_info())
  if rmdir:
    try:
      os.rmdir(path)
    except OSError:
      onerror(os.rmdir, path, sys.exc_info())


def get_files_with_extension_from_dir(directory, extensions):
  '''
  Return files that have one of the given extension(s) in the directory.
  Searches subdirectories recursively. Extensions are case insensitive.

  Parameters
  ----------
  directory : str
    The file directory.
  extensions : :term:`iterable`
    List of desired file extensions. Don't include the period.

  Returns
  -------
  list
    Files in the given directory that have one of the given extensions.
  '''

  # Convert the extensions to lower case
  lower_case_extensions = [ext.lower() for ext in extensions]

  # List of files to return
  files = []

  # For every file in directory
  for f in glob.glob(os.path.join(directory, "**", "*.*"), recursive=True):

    # Get the extension of the file
    _, ext = os.path.splitext(f)

    # Remove the period from the extension
    ext = ext[1:]

    # Store the file if the extension matches
    if ext.lower() in lower_case_extensions:
      files.append(f)

  return files


def get_neighbor_files_with_extension(path, extensions):
  '''
  Return files which are the "neighbor" of the given file. A file is
  a neighbor if it exists in the same directory, with the same name,
  but has a different extension.

  Extensions are case insensitive.

  Parameters
  ----------
  path : str
    The path to a file. We will search for files that are a neighbor with the same name,
    to this file.
  extensions : :term:`iterable`
    List of desired file extensions. Don't include the period.

  Returns
  -------
  list
    Files next to the given file that have one of the given extensions.
  '''

  # Convert the extensions to lower case
  lower_case_extensions = [ext.lower() for ext in extensions]

  # List of files to return
  files = []

  # Get the root of the file's path, i.e. the path without an extension
  path_root = os.path.splitext(path)[0]

  # For every neighbor file
  for f in glob.glob(f"{path_root}.*"):

    # Get the extension of the file
    _, ext = os.path.splitext(f)

    # Remove the period from the extension
    ext = ext[1:]

    # Store the file if the extension matches
    if ext.lower() in lower_case_extensions:
      files.append(f)

  return files


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


def dir_or_temp(kwarg_key):
  '''
  Decorator to replace a missing kwarg (missing, empty, or ``None``) that
  defines a directory with a valid temporary directory.

  The temporary directory will be created on entering the decorated function,
  and the directory & its contents will be deleted on exiting the decorated
  function.
  '''
  return _path_or_temp(kwarg_key)


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
