import os
import shutil

def lncp(source, dest):
  ''' Symlink or copy if that fails. Should work for Linux and Windows 

      Parameters
      ----------
      source : array_like
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