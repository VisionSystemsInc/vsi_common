1>2# : ^
'''
@echo off
python %~f0 %*
exit /b 
'''

import argparse
from subprocess import Popen, PIPE
from xml.dom.minidom import parseString as parseStringXml
import datetime
import os
from vsi.windows.wmic import Pgrep, Wmic

class CommaList(argparse.Action):
  def __init__(self, option_strings, dest, type=str, **kwargs):
    self.objectType=type
    super(CommaList, self).__init__(option_strings, dest, type=str, **kwargs)
  def __call__(self, parser, namespace, values, option_string=None):
    #print '%r %r %r' % (namespace, values, option_string)
    setattr(namespace, self.dest, map(self.objectType, values.split(',')))

def main(args=None):
  parser = argparse.ArgumentParser()
  parser.add_argument('-P', dest='ppid', help='Only match processes whose parent process ID is listed.', default=[], type=int, action=CommaList)
  parser.add_argument('-p', dest='pid', help='Only match processes whose process ID is listed.', default=[], type=int, action=CommaList)
  parser.add_argument('--listfields', help='List all possible fields. All other options are ignored', action='store_true')
  parser.add_argument('-F', '--fields', help='List of fields to show', default=['ProcessId'], type=str, action=CommaList)
  parser.add_argument('-H', dest='header', help='Do not print header', action='store_false', default=True)
  parser.add_argument('-f', dest='full', default=False, action='store_true', help='The pattern is normally only matched against the process name.  When -f is set, the full command line is used.')
  parser.add_argument('pattern', nargs='?')
  args = parser.parse_args(args)

  fields_get = list(args.fields) #Create a copy
  if 'processid' not in map(str.lower, fields_get):
    fields_get.append('processid')

  if args.listfields:
    wmic = Wmic('win32_process')
    props = wmic.getProperties()
    for prop in props:
      print prop.name
    return None, args
  elif args.pid:
    cmd = ['where']
    f = ''
    for pid in args.pid:
      f += "ProcessId='%d' or " % pid
    cmd.append(f[:-4])
  elif args.ppid:
    cmd = ['where']
    f = ''
    for ppid in args.ppid:
      f += "ParentProcessId='%d' or " % ppid
    cmd.append(f[:-4])
  elif args.pattern:
    if args.full:
      cmd = ['where', "CommandLine like '%%%s%%'" % args.pattern]
    else:
      cmd = ['where', "Name like '%%%s%%'" % args.pattern]
  else:
    parser.print_help()
    return None, args

  pgrep = Pgrep(cmd, fields_get)
  #Run the pgrep command
  
  remove_pids = [pgrep.pid, os.getpid()]
  
  
  pgrep.pids = filter(lambda x:not x['processid'] in remove_pids,pgrep.pids)
  #Remove these pids to have more "pgrep" like results aka BETTER
  return pgrep, args

if __name__=='__main__':
  (pgrep, args) = main()

  if pgrep:
    import sys
    if args.header:
      sys.stdout.write('\t'.join(args.fields)+'\n')
    sys.stdout.write('\n'.join(map(lambda pid: '\t'.join(map(lambda x:str(pid[x.lower()]), args.fields)), pgrep.pids)))
