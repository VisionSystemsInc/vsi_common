def is_string_like(obj):
    """
    Check whether obj behaves like a string.
    
    Copied from numpy
    """
    try:
        obj + ''
    except (TypeError, ValueError):
        return False
    return True
  
def get_file(fid, mode='rb'):
  ''' Helper function to take either a filename or fid
  
      Keyword Arguments:
      fid - File object or filename
      mode - Optional, file mode to open file if filename supplied
             Default rb'''

  if is_string_like(fid):
    fid = open(fid, mode);
  
  return fid 

def static(**kwargs):
  ''' Decorator for easily defining static variables
  
      Example:
      
      @static(count=0)
      def test(a, b):
        test.count += 1
        print a+b, test.count
  '''
  def decorate(func):
    for k in kwargs:
      setattr(func, k, kwargs[k])
    return func
  return decorate