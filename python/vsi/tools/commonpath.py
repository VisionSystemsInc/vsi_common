import os.path as path

def commonpath(uris): # use path.commonpath in python3.5
  if isinstance(uris, basestring): # Python 3: isinstance(v, str)
    uris = [uris]
  return uris[0] if all(uris[0] == uri for uri in uris) \
      else common_dirname([path.dirname(uri) for uri in uris])
