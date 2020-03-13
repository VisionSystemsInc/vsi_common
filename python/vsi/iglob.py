"""Filename globbing utility with optional case sensitive override."""

try:    # Python 2
  from glob import _unicode
except: # Python 3
  _unicode=str
  unicode=str

from fnmatch import translate
import os,posixpath,ntpath
import sys
import re

__all__ = ["glob", "iglob"]

def path_split(p):
  """ Well... it turns out that os.path.split is WRONG for both posix and nt.

  Parameters
  ----------
  p : str
      The Path
  
  Returns
  -------
  array_like
      The split path


  When you execute os.path.split('.') You SHOULD get ('.','') BUT... due
  to the simplicity of os.path.split, it only looks for /, and it fails to make
  an exception for this, which breaks the recursive logic of glob. The ORIGINAL
  glob does not FIX this, it just doesn't care since it does a lexists on what
  should have been isdir on a directory. Since I can't
  use lexists here for case insensitive reasons, the logic needed to be
  more lock tight... This (hopefully simple and complete?) solution will
  look for result where dirname is empty and basename is made up of all
  periods, and if that happens, switch it
  """
  s = os.path.split(p)
  if not s[0] and s[1] == '.'*len(s[1]):
    return (s[1], s[0])
  return s

def path_join(a, *p):
  ''' Same as path_split

  Parameters
  ----------
  a : str
  *p :

  Returns
  -------
  array_like
  '''
  if p==('',) and a == '.'*len(a):
    return a
  return os.path.join(a, *p)

def glob(pathname, case=None):
  """Return a list of paths matching a pathname pattern.

  Parameters
  ----------
  pathname : str
      The Path Name

  Returns
  -------
  list
      A list of paths matching a pathname pattern


  The pattern may contain simple shell-style wildcards a la fnmatch. However,
  unlike fnmatch, filenames starting with a dot are special cases that are not
  matched by '*' and '?' patterns.

  Set case to true to force case sensitive, false to force case insensitive or
  None(default) to run glob natively

  """
  return list(iglob(pathname, case))

def checkcase(case=None):
  """ Determing which case mode to use

  Returns
  -------
  bool
      If None(default) then uses which ever mode is native to the OS
      If True, forces case sensitive mode
      If False, forces case insensitive mode
  """
  if case is None:
    return os.path is posixpath
  elif case:
    return True
  return False

def iglob(pathname, case=None):
  """Return an iterator which yields the paths matching a pathname pattern.

  Parameters
  ----------
  pathname : str
      The Path Name


  The pattern may contain simple shell-style wildcards a la fnmatch. However,
  unlike fnmatch, filenames starting with a dot are special cases that are not
  matched by '*' and '?' patterns.

  Set case to true to force case sensitive, false to force case insensitive or
  None(default) to run glob natively
  """

  dirname, basename = path_split(pathname)

  walker = os.walk(dirname)

  case = checkcase(case)

  # The only REAL use I have for these lines are to make sure iglob('')
  #returns EMPTY. Other than that, this is repeat of logic below
  if not dirname:
    for name in glob1(os.curdir, basename):
      yield name
    return

  # `os.path.split()` returns the argument itself as a dirname if it is a
  # drive or UNC path.  Prevent an infinite recursion if a drive or UNC path
  # contains magic characters (i.e. r'\\?\C:').
  if dirname != pathname:
    dirs = iglob(dirname, case)
  else:
    dirs = [dirname]

  if basename=='':
    glob_in_dir = glob0
  else:
    glob_in_dir = glob1

  for dirname in dirs:
    for name in glob_in_dir(dirname, basename, case):
      yield path_join(dirname, name)


# These 2 helper functions non-recursively glob inside a literal directory.
# They return a list of basenames. `glob1` accepts a pattern while `glob0`
# takes a literal basename (so it only has to check for its existence).

def glob0(dirname, basename, case=None):
  """

  Parameters
  ----------
  dirname : str
      The Directory Name
  basename : str
      The Base Name
  
  Returns
  -------
  list
      A list of basenames
  """
  if dirname == '':
    dirname = os.curdir
  # `os.path.split()` returns an empty basename for paths ending with a
  # directory separator.  'q*x/' should match only directories.
  if os.path.isdir(dirname):
    return [basename]
  return []

def glob1(dirname, pattern, case=None):
  """

  Parameters
  ----------
  dirname : str
      The Directory Name
  pattern : str
      A Pattern
  
  Returns
  -------
  list
      A list of basenames
  """
  if not dirname:
    dirname = os.curdir
  if isinstance(pattern, _unicode) and not isinstance(dirname, unicode):
    dirname = unicode(dirname, sys.getfilesystemencoding() or
                               sys.getdefaultencoding())
  try:
    names = os.listdir(dirname)
  except os.error:
    return []
  if pattern and pattern[0] != '.':
    names = filter(lambda x: x[0] != '.', names)
  return fnmatch_filter(names, pattern, case)

_casecache = {}
_nocasecache = {}

def fnmatch_filter(names, pat, casesensitive):
  # Return the subset of the list NAMES that match PAT
  """

  Parameters
  ----------
  names : :obj:`list` or :obj:`tuple`
      A list of names
  pat : str
      A pattern
  casesensitive : bool
      True if case sensitive, False if not.

  Returns
  -------
  list
      The subset of the list NAMES that match PAT
  """
  result=[]

  if casesensitive:
    if not pat in _casecache:
      res = translate(pat)
      if len(_casecache) >= 100:
        _casecache.clear()
      _casecache[pat] = re.compile(res)
    match=_casecache[pat].match

    for name in names:
      if match(name):
        result.append(name)
  else:
    if not pat in _nocasecache:
      res = translate(pat)
      if len(_nocasecache) >= 100:
        _nocasecache.clear()
      _nocasecache[pat] = re.compile(res, re.IGNORECASE)
    match=_nocasecache[pat].match

    pat=ntpath.normcase(pat)
    for name in names:
      if match(ntpath.normcase(name)):
        result.append(name)
  return result