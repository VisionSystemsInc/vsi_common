import os.path as path

def commonpath(uris):
  # use path.commonpath in python3.5
  #
  # >>> common_dirname(['/root/path/file.txt', '/root/file.txt'])
  # '/root'
  # >>> common_dirname(['root/path/file.txt', 'root/file.txt'])
  # 'root'

  def subdirs(stems):
    if isinstance(stems, basestring): # Python 3: isinstance(v, str)
      stems = [stems]

    def isroot(p):
      return path.dirname(p) == p
    stems.append(path.dirname(stems[-1]))
    return stems if path.dirname(stems[-1]) == '' else stems[:-1] if isroot(stems[-1]) else subdirs(stems)

  for stem in subdirs(uris[0]):
    if all(uri.startswith(stem) for uri in uris): return stem
