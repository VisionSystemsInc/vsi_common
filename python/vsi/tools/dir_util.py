import os

from distutils.dir_util import mkpath, remove_tree

from tempfile import mkdtemp

class Chdir(object):
  ''' Simple helper function to change dir and guarantee you get back to your 
      original directory '''
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
      mkpath(self.dir)
    os.chdir(self.dir)
  
  def __exit__(self, exc_type, exc_value, traceback):
    try:
      os.chdir(self.oldDir)
    except OSError as osError:
      if osError.errno == 2 and self.error_on_exit:
        print "Previous directory does not exist anymore.\nCannot return to " \
              "%s" % self.oldDir
      else:
        raise(osError)

class TempDir(object):
  ''' Create and clean up a temp director 
  
      Does not generate random name, use something like tempfile.mkdtemp for 
      that'''

  def __init__(self, dir=None, cd=False, delete=True, delete_if_not_create=False,
              *args, **kwargs):
    ''' Create a temp dir object

        Arguments

        dir - dir must exist
        cd - Change into the temp dir (and change back). Default: false
        delete - Delete on exit. Default: true
        delete_if_not_create - Delete the directory "dir" even if it was
                               not created by TempDir
        *args/**kwargs - Same as Chdir (mostly for error_on_exit)'''
    self.dir= dir

    self.cd = Chdir(self.dir, *args, **kwargs) if cd else None
    
    self.delete = delete
    self.delete_if_not_create=delete_if_not_create
    
    self.created_dir = False

  def __enter__(self):
    if not os.path.exists(self.dir):
      mkpath(self.dir)
      self.created_dir = True

    if self.cd:
      self.cd.__enter__()
    return self.dir

  def __exit__(self, exc_type, exc_value, traceback):
    if self.cd:
      self.cd.__exit__(exc_type, exc_value, traceback)
    if self.delete and (self.created_dir or self.delete_if_not_create):
      print self.delete, self.created_dir, self.delete_if_not_create
      remove_tree(self.dir)
