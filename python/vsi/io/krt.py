import numpy as np

from vsi.tools import get_file

#Not done yet
class Krt(object):
  def __init__(self, k=None, r=None, t=None):
    '''Create Krt object
     
     Keyword Arguments
     fid - File object or Location of krt file
     
     or 

     k - 3x3 numpy array
     r - 3x3 numpy array
     t - 3, numpy array
     '''

    self.k = k
    self.r = r
    self.t = t

  def __eq__(self, rhs):
    try:
      return np.all(self.k==rhs.k) \
         and np.all(self.r==rhs.r) \
         and np.all(self.t==rhs.t)
    except:
      return False

  def save(self, filename):
    '''Save Krt object to disk
     
       Keyword Arguments
       fid - File object or Location of krt file
       '''
    
    fid = get_file(filename, 'w')

    np.savetxt(fid, self.k);
    fid.write('\n');
    np.savetxt(fid, self.r);
    fid.write('\n');
    np.savetxt(fid, self.t.reshape((1,3)));
    
  @classmethod
  def load(cls, fid):
    '''Load krt file
     
       Keyword Arguments
       filename - File object or Location of krt file
       
       Sets
       k - 3x3 numpy array
       r - 3x3 numpy array
       t - 3, numpy array
       '''
    
    data = np.loadtxt(fid);
  
    k = data[0:3, :];
    r = data[3:6, :];
    t = data[6, :];
    
    return cls(k=k, r=r, t=t)
  
  def __repr__(self):
    s =  str(self.k) + '\n'
    s += str(self.r) + '\n'
    s += str(self.t) + '\n'
    return s
    
  def __str__(self):
    s =  'K:\n'
    s += str(self.k) + '\n'
    s += 'R\n'
    s += str(self.r) + '\n'
    s += 't\n'
    s += str(self.t) + '\n'
    return s

  def camera_center(self):
    return -self.r.T.dot(self.t)

  def direction(self):
    return self.r.T.dot([0,0,1])

# class Krts(object):
#   def __init__(self):
#     pass
#   def load(self, filenames):
#     pass
