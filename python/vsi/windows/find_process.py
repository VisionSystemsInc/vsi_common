import subprocess
from vsi.tools.subprocess_util import PopenBg as Popen


def findProcess(imageName, filterString):
  pid = Popen(['wmic', 'path', 'win32_process', 'where',
               "Name='%s'" % imageName, 'get',
               'CommandLine,ProcessId', '/VALUE'],
              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out = pid.communicate()
  out = out[0].split('\r\r\n\r\r\n')
  out = filter(lambda x: 'CommandLine' in x, out)
  out = map(lambda x: x.strip().split('\r\r\n'), out)

  if out:
    if out[0][0].startswith('CommandLine'):
      commandLineIndex = 0
      processIndex = 1
    else:
      commandLineIndex = 1
      processIndex = 0
    out = map(
        lambda x: [int(x[processIndex][10:]), x[commandLineIndex][12:]], out)

    out = filter(lambda x: filterString in x[1], out)
    return map(lambda x: x[0], out)
  return []

if __name__ == '__main__':
  import sys
  import os
  myPid = os.getpid()
  try:
    imageName = sys.argv[1]
    filterString = sys.argv[2]
    pids = findProcess(imageName, filterString)
    pids = filter(lambda x: x != myPid, pids)
    print('\n'.join(map(str, pids)))
  except:
    print('Usage: {} [imageName] [filterString]'.format(sys.argv[0]))
