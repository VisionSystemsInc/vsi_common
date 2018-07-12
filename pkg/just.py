#!/usr/bin/env python

import sys
import os

if hasattr(sys, 'frozen'):
  os.environ['PATH'] = os.path.join(sys._MEIPASS, 'linux')+os.pathsep+os.environ['PATH']
  os.environ['VSI_COMMON_DIR'] = sys._MEIPASS

import subprocess

if os.name=='nt':
  import pipes
  args = ' '.join([pipes.quote(x) for x in sys.argv[1:]])
  # sp=subprocess.Popen(['powershell', 'bash'], shell=False)
  sp=subprocess.Popen(['powershell', 'cmd /c color 07; bash just '+args+'; bash --rcfile "' + os.path.join(os.environ['VSI_COMMON_DIR'], '.winbashrc"')], shell=False)
  #   python -c "import pipes as p; import sys as s; print(' '.join([p.quote(x) for x in s.argv[1:]]))" "${@}"

# "cmd /c color 07; bash \"$0\" ${@}; bash --rcfile \"${VSI_COMMON_DIR}/.winbashrc\""
  sp.wait()
else:
  sp=subprocess.Popen(['bash', '-c', os.path.join(sys._MEIPASS, 'linux', 'just').replace('\\', '/')], shell=True)
  sp.wait()
  sys.exit(sp.returncode)
