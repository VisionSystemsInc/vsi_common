#!/usr/bin/env python

import sys
import os

os.environ['PATH'] += os.pathsep+os.path.join(sys._MEIPASS, 'linux')

import glob
# print(glob.glob(os.path.join(sys._MEIPASS, 'vsi', '*')))
# print(glob.glob(os.path.join(sys._MEIPASS, 'vsi', 'just')))

# os.execlp('bash', 'bash', os.path.join(sys._MEIPASS, 'vsi', 'just'))
import subprocess
sp=subprocess.Popen(['bash', '-c', os.path.join(sys._MEIPASS, 'linux', 'just').replace('\\', '/')], shell=True)
sp.wait()
sys.exit(sp.returncode)
