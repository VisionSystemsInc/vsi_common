
import os

class Chdir(object):
  ''' Simple helper function to change dir and guarantee you get back to your original directory '''
  def __init__(self, newDir):
    ''' One argument, the directory you want to change directory to'''
    self.newDir = newDir
    
  def __enter__(self):
    self.cwd = os.getcwd()
    os.chdir(self.newDir)
  
  def __exit__(self, exc_type, exc_value, traceback):
    os.chdir(self.cwd)
    
class TempDir(object):
  ''' TODO Create tempdir, return it as as.. string? And then delete it all when done '''
  
  def __init__(self):
    return None
  def __enter__(self):
    pass
  def __exit__(self, exc_type, exc_value, traceback):
    pass