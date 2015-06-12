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
        #Return you to / or the c:\ or d:\, etc... If THIS errors, something
        #is seriously WRONG
        os.chdir(os.path.abspath(os.sep))
      else:
        raise(osError)

class TempDir(object):
  ''' Create and clean up a temp director 
  
      Does not generate random name, use something like tempfile.mkdtemp for 
      that'''

  def __init__(self, dir=None, cd=False, delete=True, mkdtemp=False, 
               delete_if_not_create=False, *args, **kwargs):
    ''' Create a temp dir object

        Arguments

        dir - dir must exist
        cd - Change into the temp dir (and change back). Default: false
        mkdtemp - Call mkdtemp in dir to create a temp dir. Default: false
                  Try and use this INSTEAD of delete_if_not_create, much safer
        delete - Delete on exit. Default: true
        delete_if_not_create - Default: false. Delete the directory "dir" 
                               even if it was not created by TempDir. ONLY 
                               TURN THIS ON when you are absolutely sure you
                               want this directory deleted. Make sure the 
                               input dir is something you want deleted, or 
                               else just don't use this argument! For example, 
                               in an unsantized case the tempdir could be / or
                               something like /home/username. Then / or the
                               entire home directory would be deleted! That 
                               has to be bad, right? 
        *args/**kwargs - Passed on to Chdir (mostly for error_on_exit)'''

    self.base_dir= dir
    
    self.mkdtemp = mkdtemp

    self.cd = Chdir(self.base_dir, *args, **kwargs) if cd else None
    
    self.delete = delete
    self.delete_if_not_create=delete_if_not_create
    
    self.created_dir = False

  def __enter__(self):
    if self.mkdtemp:
      self.dir = mkdtemp(dir=self.base_dir)
      self.cd.dir = self.dir #<-- hack
      self.created_dir = True
    else:
      #These two are separate variables incase with is called twice on the
      #same instance... It COULD happen
      self.dir = self.base_dir
    
    if not os.path.exists(self.dir):
      mkpath(self.dir)
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
      print self.delete, self.created_dir, self.delete_if_not_create
      remove_tree(self.dir)
