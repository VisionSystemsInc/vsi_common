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

# This function was copied from cpython,
# and changed to allow the base directory to be kept.
# Source: https://github.com/python/cpython/blob/v3.6.15/Lib/shutil.py#L451
def rmtree(path, ignore_errors=False, onerror=None, keep_base_dir=False):
  """"
  shutil.rmtree with the ability to keep the directory at `path`. Necessary for situations
  when deleting the root directory would cause it to be unmounted.

  Parameters
  ----------
  path : str
      Path to the directory with contents to remove
  ignore_errors : bool, optional
      If True, exceptions will not be raised when an error is encountered. Default: False
  onerror : Callable, optional
      Function to be called when an error is encountered. Only used if ignore_errors is False.
      Default: None
  keep_base_dir : bool, optional
      If True, the base directory will remain while its children are deleted. Default: False
  """
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
        if not keep_base_dir:
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
    return _rmtree_unsafe(path, onerror, keep_base_dir)


# version vulnerable to race conditions
def _rmtree_unsafe(path, onerror, keep_base_dir=False):
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
  if not keep_base_dir:
    try:
      os.rmdir(path)
    except OSError:
      onerror(os.rmdir, path, sys.exc_info())


def glob_files_with_extensions(directory, extensions, recursive=True):
  '''
  Return files that have one of the given extension(s) in the directory.
  Searches subdirectories recursively. Extensions are case insensitive.

  Parameters
  ----------
  directory : str
    The file directory.
  extensions : :term:`iterable`
    List of desired file extensions. Don't include the period.
  recursive : bool, optional
    If True, find files in subdirectories as well. Default: True

  Returns
  -------
  list
    Files in the given directory that have one of the given extensions.
  '''

  # Convert the extensions to lower case
  lower_case_extensions = [ext.lower() for ext in extensions]

  # List of files to search for extension
  if recursive:
    all_files = glob.glob(os.path.join(directory, "**", "*.*"), recursive=True)
  else:
    all_files = glob.glob(os.path.join(directory, "*.*"), recursive=False)

  # List of files to return
  files = []

  # For every file in directory
  for f in all_files:

    # Get the extension of the file
    _, ext = os.path.splitext(f)

    # Remove the period from the extension
    ext = ext[1:]

    # Store the file if the extension matches
    if ext.lower() in lower_case_extensions:
      files.append(f)

  return files


def glob_neighbor_files_with_extensions(path, extensions):
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
