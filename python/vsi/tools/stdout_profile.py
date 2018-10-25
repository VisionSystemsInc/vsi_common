#!/usr/bin/env python

import argparse
import sys
from subprocess import Popen, PIPE
from time import time


def argumet_parser():
  ''' Returns
      -------
      str
          The Parser
      '''
  parser = argparse.ArgumentParser(prefix_chars='\0')
  parser.add_argument('command', nargs='+')
  return parser


def main(args=sys.argv[1:]):
  ''' Parameters
      ----------
      args : array_like
          An array of arguments
      '''
  parser = argumet_parser()
  arguments = parser.parse_args(args)
  pid = Popen(arguments.command, stdout=PIPE)

  time0 = time()
  line = ' ==Starting==\n'
  while line:
    time1 = time()
    sys.stdout.write(('%0.9f ' + line) % (time1 - time0))
    time0 = time1
    line = pid.stdout.readline()


if __name__ == '__main__':
  main()
