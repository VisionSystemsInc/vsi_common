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


def rmtree(path, ignore_errors=False, onerror=None, *args, onexc=None, keep_base_dir=False, **kwargs):
  """"
  shutil.rmtree with the ability to keep the directory at `path`. Necessary for situations
  when deleting the root directory would cause it to be unmounted.

  Parameters
  ----------
  keep_base_dir : bool, optional
      If True, the base directory will remain while its children are deleted. Default: False

  The rest of ``shutil.rmtree``'s parameters should be passed along.
  """
  if keep_base_dir == False:
    shutil.rmtree(path, ignore_errors=ignore_errors, onerror=onerror, *args,
                  onexc=onexc, **kwargs)
  else:
    # https://github.com/python/cpython/blob/v3.15.0a2/Lib/shutil.py#L832
    # Replicate this for file cleanup
    if ignore_errors:
      def onexc(*args):
        pass
    elif onerror is None and onexc is None:
      def onexc(*args):
        raise
    elif onexc is None:
      # delegate to onerror
      def onexc(*args):
        func, path, exc = args
        if exc is None:
          exc_info = None, None, None
        else:
          exc_info = type(exc), exc, exc.__traceback__
        return onerror(func, path, exc_info)

    try:
      names = os.listdir(path)
    except FileNotFoundError:
      return
    except OSError as err:
      onexc(os.listdir, path, err)

    for name in names:
      fullname = os.path.join(path, name)
      if os.path.isdir(fullname):
        # Changes in rmtree signature by version
        # 3.10 shutil.rmtree(path, ignore_errors=False, onerror=None)
        #   EOL 10/2026
        # 3.11 shutil.rmtree(path, ignore_errors=False, onerror=None, *,
        #                    dir_fd=None)
        #   EOL 10/2027
        # 3.12 shutil.rmtree(path, ignore_errors=False, onerror=None, *,
        #                    onexc=None, dir_fd=None)
        #   EOL 10/2028
        # 3.15 shutil.rmtree(path, ignore_errors=False, onerror=None, *,
        #                    onexc=None, dir_fd=None)
        #   EOL 10/2031
        if sys.version_info[1] < 12:
          # pre 3.12, shutil doesn't have onexc.
          # TODO: Remove this if branch on 10/2028
          shutil.rmtree(fullname, ignore_errors, onerror, *args, **kwargs)
        else:
          # don't need onerror or ignore error anymore, they were processed
          # into onexc
          shutil.rmtree(fullname, *args, onexc=None, **kwargs)
      else:
        try:
          os.unlink(fullname)
        except FileNotFoundError:
          continue
        except OSError as err:
          onexc(os.unlink, fullname, err)


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
    all_files = [os.path.join(root, file) for root, _, files in os.walk(directory)
                 for file in files if '.' in file and not file.startswith('.')]
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
