import os

from distutils.dir_util import remove_tree

from tempfile import mkdtemp as mkdtemp_orig, gettempdir

from shutil import Error, copy2, copystat, rmtree

def mkdtemp(*args, **kwargs):
  ''' Version of tempfile.mkdtemp that is r/w by uid and gid'''
  tempdir = mkdtemp_orig(*args, **kwargs)
  os.chmod(tempdir, 0770)
  return tempdir

class Chdir(object):
  ''' Simple helper function to change dir and guarantee you get back to your 
      original directory 
      
      Example:
      
      >>> import os
      >>> import tempfile
      >>> from vsi.tools.dir_util import Chdir
      >>> os.chdir(os.path.abspath(os.sep))
      >>> print(os.getcwd())
      /
      >>> with Chdir(tempfile.tempdir):
      ...   print(os.getcwd())
      /tmp
      >>> print(os.getcwd())
      /

      '''
  def __init__(self, dir, create=False, error_on_exit=False):
    ''' Create Chdir object
    
        Required arguments
        dir - the directory you want to change directory to
        
        Optional arguments
        create - Create the directory if it doesn't exist (else os error 2 
                 will occur) Default: False
        error_on_exit - When exiting the with loop, if the return directory 
                        does not exist anymore, (OSError 2), if this is true
                        an error is thrown, else it is ignore and you are left
                        in the new directory. Default: False
        '''
    self.dir = dir
    self.oldDir = None
    self.create = create
    self.error_on_exit = error_on_exit
  
  def __enter__(self):
    self.oldDir = os.getcwd()
    if self.create and not os.path.exists(self.dir):
      os.makedirs(self.dir)
    os.chdir(self.dir)
  
  def __exit__(self, exc_type, exc_value, traceback):
    try:
      os.chdir(self.oldDir)
    except OSError as osError:
      if osError.errno == 2 and self.error_on_exit:
        print "Previous directory does not exist anymore.\nCannot return to " \
              "%s" % self.oldDir
        #Return you to / or the c:\ or d:\, etc... If THIS errors, something
        #is seriously WRONG
        os.chdir(os.path.abspath(os.sep))
      else:
        raise(osError)

class TempDir(object):
  ''' Create and clean up a temp directory 
  
      The most common usage for this would be to create a random directory
      each time. The mkdtemp flag was added to facilitate this.
      
      Example:
      
      >>> from vsi.tools.dir_util import TempDir
      >>> import tempfile
      >>> from glob import glob
      >>> with TempDir(tempfile.tempdir, mkdtemp=True) as tempDir:
      ...   print(tempDir)
      ...   print(glob(tempDir))
      >>> print(glob(tempDir))
  '''

  def __init__(self, dir=None, cd=False, delete=True, mkdtemp=False, 
               delete_if_not_create=False, *args, **kwargs):
    ''' Create a temp dir object

        Arguments

        dir - Base dir must exist. Default is None. None will only work if 
              mkdtemp is true.
        cd - Change into the temp dir (and change back). Default: false
        mkdtemp - Call mkdtemp in dir to create a temp dir. Default: false
                  Try and use this INSTEAD of delete_if_not_create, much safer.
                  The class must call mkdtemp for you, or else it will not have
                  "created" the directory, thus introducing unsafe situations
                  where a directory may be inadvertently deleted if you
                  accidentally tell it to be.
        delete - Delete on exit. Default: true
        delete_if_not_create - Default: false. Delete the directory "dir" 
                               even if it was not created by TempDir. ONLY 
                               TURN THIS ON when you are absolutely sure you
                               want this directory deleted. Make sure the 
                               input dir is something you want deleted, or 
                               else just don't use this argument! For example, 
                               in an unsanitized case the tempdir could be / or
                               something like /home/username. Then / or the
                               entire home directory would be deleted! That 
                               has to be bad, right? 
        *args/**kwargs - Passed on to Chdir (mostly for error_on_exit)'''

    self.base_dir= dir
    
    self.mkdtemp = mkdtemp

    if self.mkdtemp and not self.base_dir:
      self.base_dir = gettempdir()

    self.cd = Chdir(self.base_dir, *args, **kwargs) if cd else None
    
    self.delete = delete
    self.delete_if_not_create=delete_if_not_create
    
    self.created_dir = False

  def __enter__(self):
    if self.mkdtemp:
      if not os.path.exists(self.base_dir):
        os.makedirs(self.base_dir)

      self.dir = mkdtemp(dir=self.base_dir)
      if self.cd:
        self.cd.dir = self.dir #<-- hack
      self.created_dir = True
    else:
      #These two are separate variables incase with is called twice on the
      #same instance... It COULD happen
      self.dir = self.base_dir
    
    if not os.path.exists(self.dir):
      os.makedirs(self.dir)
      self.created_dir = True

    if self.cd:
      self.cd.__enter__()
    return self.dir

  def __exit__(self, exc_type, exc_value, traceback):
    if self.cd:
      self.cd.__exit__(exc_type, exc_value, traceback)
    #The reason for not making this all automatically work is JUST IN
    #CASE someone says something like / is the temp dir... Can you
    #Imagine running remove tree on / or /home/user? BAD THINGS.
    #It is up to the dev to make sure he knows what he is doing
    if self.delete and (self.created_dir or self.delete_if_not_create):
      remove_tree(self.dir)

def checksum_dir(checksum, checksum_depth=2, base_dir=None):
  ''' Generate checksum directory name

      For example, if the checksum was 1234567890abcdef, and the depth was 3, 
      you would get 12/34/56/1234567890abcdef

      An optional base_dir will be prefixed'''

  dir_parts = [checksum[x:x+2] if x<checksum_depth*2 else checksum \
               for x in range(0,checksum_depth*2+1,2)]
  if base_dir:
    return os.path.join(base_dir, *dir_parts)
  else:
    return os.path.join(*dir_parts)


#copy from shutil actually
def copytree(src, dst, symlinks=False, ignore=None):
    """Recursively copy a directory tree using copy2().

    The destination directory may not already exist.
    If exception(s) occur, an Error is raised with a list of reasons.

    If the destination directory exists, it will be clobber by the 
    source, including replacing entire directory trees with symlinks,
    if the symlinks flags is true.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
      os.makedirs(dst)
    else:
      os.chmod(dst, 0777)

    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                if os.path.exists(dstname) and os.path.isdir(dstname):
                  rmtree(dstname)
                else:
                  os.unlink(dstname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                if os.path.exists(dstname):
                  os.unlink(dstname)
                # Will raise a SpecialFileError for unsupported file types
                copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error, err:
            errors.extend(err.args[0])
        except EnvironmentError, why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError, why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.append((src, dst, str(why)))
    if errors:
        raise Error, errors
