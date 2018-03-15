#!/usr/bin/env python

import argparse
import atexit
import imp
import os
import sys
import shutil
import sys
import tempfile
from glob import glob

try:
  from urllib.request import urlopen
except ImportError:
  from urllib2 import urlopen

from subprocess import Popen as Popen_orig

class Popen(Popen_orig):
  def wait(self):
    rv = super(Popen, self).wait()
    assert rv == 0
    return rv

# https://stackoverflow.com/a/5227009/4166604
def which(file, windows_extension='exe'):
  if sys.platform=='win32':
    file=file+os.path.extsep+windows_extension
  for path in os.environ["PATH"].split(os.pathsep):
    if os.path.exists(os.path.join(path, file)):
      return os.path.join(path, file)
  return None

def find(name, path):
  for root, dirs, files in os.walk(path):
    if name in files:
      return os.path.join(root, name)

def patch_site(site, config_dir, data_dir):
  with open(site, 'a') as fid:
    fid.write('''
os.environ['JUPYTER_CONFIG_DIR'] = '''
'''os.path.abspath(os.path.join(os.path.dirname(__file__), {}))
os.environ['JUPYTER_DATA_DIR'] = '''
'''os.path.abspath(os.path.join(os.path.dirname(__file__), {}))'''.format(
      repr(config_dir),
      repr(data_dir)))

parser = argparse.ArgumentParser()
aa = parser.add_argument
aa('--notebook-dir',
   default=os.path.expanduser(os.path.join('~', 'notebooks')),
   help="Location where the notebooks will be stored")
aa('--ip', default='*', help='IP the notebook server will bind to')
aa('--port', default='8888', help='Port the notebook server will bind to')
aa('--browser', default=False, action='store_true',
   help='Open the web browser on start')
aa('--random-token', default=False, action='store_true',
   help='Use a random token')
aa('--one-python', default=False, action='store_true',
   help='''Don't try and look for another python2/3. You may need '''
        '''to do this if you don't have the python-devel installed '''
        '''for both pythons''')
aa('--token', default='', help='Fixed token to use')
aa('venv', default='.', nargs='?', help='Directory of the venv')
args = parser.parse_args()

tempdir = tempfile.mkdtemp()

atexit.register(shutil.rmtree, tempdir)
d2=os.path.join(tempdir, '2')
d3=os.path.join(tempdir, '3')
os.mkdir(d2)
os.mkdir(d3)

python2 = None
python3 = None

if sys.version_info.major == 3:
  python3 = sys.executable
else:
  python2 = sys.executable

# If I am supposed to look for the other python, do so.
if not args.one_python:
  if sys.version_info.major == 3:
    python2 = which('python2', 'exe')
  else:
    python3 = which('python3', 'exe')

pip_install = urlopen('https://bootstrap.pypa.io/get-pip.py').read().decode(
    "utf-8")
pip_filename = os.path.join(tempdir, 'get-pip.py')
with open(pip_filename, 'w') as fid:
  fid.write(pip_install)
  fid.flush()

python2_venv = ''

# Set up python3 venv
if python3:
  python2_venv = 'python2'
  env = dict(os.environ)
  env.pop('PYTHONPATH', None)
  env['PYTHONUSERBASE'] = d3
  Popen([python3, pip_filename, '--user', 'virtualenv', '-U'], env=env).wait()
  venv_file = find('virtualenv.py', d3)
  env['PYTHONPATH'] = os.path.dirname(venv_file)
  Popen([python3, venv_file, os.path.abspath(args.venv)]).wait()

# Set up python2 venv
if python2:
  env = dict(os.environ)
  env.pop('PYTHONPATH', None)
  env['PYTHONUSERBASE'] = d2
  Popen([python2, pip_filename, '--user', 'virtualenv', '-U'], env=env).wait()
  venv_file = find('virtualenv.py', d2)
  env['PYTHONPATH'] = os.path.dirname(venv_file)
  Popen([python2, venv_file,
         os.path.abspath(os.path.join(args.venv, python2_venv))]).wait()

# Setup config dir inside virtual env dir by monkey patching python executable
os.environ['JUPYTER_CONFIG_DIR'] = os.path.join(args.venv, "jupyter_config")
os.environ['JUPYTER_DATA_DIR'] = os.path.join(args.venv, "jupyter_data")

os.makedirs(os.environ['JUPYTER_CONFIG_DIR'])

with open(os.path.join(os.environ['JUPYTER_CONFIG_DIR'],
                       'jupyter_notebook_config.py'), 'w') as fid:
  fid.write("""c.NotebookApp.ip = {ip}
# To link to a specific NIC: pip install netifaces
# c.NotebookApp.ip=netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
# Put in try/except just in case
c.NotebookApp.port = {port}
c.NotebookApp.notebook_dir = {notebooks}
c.NotebookApp.open_browser = {browser}\n""".format(
    ip=repr(args.ip), port=args.port,
    notebooks=repr(args.notebook_dir),
    browser=str(args.browser)))
  if not args.random_token:
    fid.write("c.NotebookApp.token = {token}\n".format(token=repr(args.token)))
  fid.flush()

if os.name == 'nt':
  bin_dir = 'Scripts'
else:
  bin_dir = 'bin'

site_file = glob(os.path.join(args.venv, 'lib/python*/site.py'))[0]
patch_site(site_file,
           os.path.relpath(os.environ['JUPYTER_CONFIG_DIR'],
                           os.path.dirname(site_file)),
           os.path.relpath(os.environ['JUPYTER_DATA_DIR'],
                           os.path.dirname(site_file)))

Popen([os.path.join(os.path.abspath(args.venv), bin_dir, 'pip'),
       'install', 'notebook', 'jupyter-contrib-nbextensions',
       'bash_kernel', 'ipywidgets', '-U']).wait()
Popen([os.path.join(os.path.abspath(args.venv), bin_dir, 'python'),
       '-m', 'ipykernel.kernelspec', '--user']).wait()
Popen([os.path.join(os.path.abspath(args.venv), bin_dir, 'python'),
       '-m', 'bash_kernel.install', '--user']).wait()
Popen([os.path.join(os.path.abspath(args.venv), bin_dir, 'jupyter-contrib'),
       'nbextension', 'install', '--user']).wait()
Popen([os.path.join(os.path.abspath(args.venv),
                    bin_dir, 'jupyter-nbextension'),
       'enable', '--py', '--user', 'widgetsnbextension']).wait()

if python2 and python3:
  with open(os.path.join(os.environ['JUPYTER_CONFIG_DIR'],
                       'jupyter_notebook_config.py'), 'a') as fid:
    fid.write("c.MultiKernelManager.default_kernel_name = 'python2'")

  site_file = glob(os.path.join(args.venv, python2_venv, 'lib/python*/site.py'))[0]

  patch_site(site_file,
             os.path.relpath(os.environ['JUPYTER_CONFIG_DIR'],
                             os.path.dirname(site_file)),
             os.path.relpath(os.environ['JUPYTER_DATA_DIR'],
                             os.path.dirname(site_file)))
  Popen([os.path.join(os.path.abspath(args.venv),
                      python2_venv, bin_dir, 'pip'),
         'install', 'ipywidgets', '-U']).wait()
  Popen([os.path.join(os.path.abspath(args.venv),
                      python2_venv, bin_dir, 'python'),
         '-m', 'ipykernel.kernelspec', '--user', '--name', 'python2']).wait()


# Add add_kernel script
with open(os.path.join(os.path.abspath(args.venv), bin_dir, 'add_kernel'), 'w') as fid:
  fid.write('''#!/usr/bin/env bash

set -eu

if python -c "import ipykernel_launcher" > /dev/null 2>&1; then
  ipykernel=ipykernel_launcher
elif python -c "import ipykernel" > /dev/null 2>&1; then
  ipykernel=ipykernel
else
  echo "IPython kernel not found."
  exit 1
fi

mkdir -p "$(dirname "${BASH_SOURCE[0]}")/../jupyter_data/kernels/${1}"

cat << EOS > "$(dirname "${BASH_SOURCE[0]}")/../jupyter_data/kernels/${1}/kernel.json"
{
 "display_name": "${1}",
 "argv": [
  "$(command -v python)",
  "-m",
  "${ipykernel}",
  "-f",
  "{connection_file}"
 ],
 "env": {},
 "language": "python"
}
EOS''')
os.chmod(os.path.join(os.path.abspath(args.venv), bin_dir, 'add_kernel'), 0o755)


# Add relocate script
with open(os.path.join(os.path.abspath(args.venv), bin_dir, 'relocate'), 'w') as fid:
  fid.write('''#!/usr/bin/env bash

set -eu

full_path="$(cd "${1-"$(dirname "${BASH_SOURCE[0]}")/.."}"; pwd)"

VIRTUAL_ENV_DISABLE_PROMPT=1
OLD_LOCATION=$(source "${full_path}/bin/activate"; echo "${VIRTUAL_ENV}")

# Make sure activate is bash/zsh compliant _\|
sed -i 's|^VIRTUAL_ENV=.*|VIRTUAL_ENV="$(cd "$(dirname "${BASH_SOURCE-"$0"}")/.."; pwd)"|' "${full_path}/bin/activate"
sed -i "s|^setenv VIRTUAL_ENV.*|setenv VIRTUAL_ENV '${full_path}'|" "${full_path}/bin/activate.csh"
sed -i "s|^set -gx VIRTUAL_ENV.*|set -gx VIRTUAL_ENV '${full_path}'|" "${full_path}/bin/activate.fish"

IFS=$'\n'
files=($(find "${full_path}/bin" -type f))

for f in "${files[@]}"; do
  if grep -qi 'python.* script' <(file "${f}"); then
    sed -i "1 s|#!.*/bin/|#!${full_path}/bin/|" "${f}"
  fi
done

find "${full_path}/jupyter_data/" "${full_path}/jupyter_config/" \( -name kernel.json -o -name jupyter_nbconvert_config.json \) \
  -exec sed -i "s|${OLD_LOCATION}|${full_path}|" \{\} \;
''')
os.chmod(os.path.join(os.path.abspath(args.venv), bin_dir, 'relocate'), 0o755)

print("\n---------------------------------\n")
print("Notebook configured successfully!")
print('Run "jupyter-notebook password" to '
      'secure your notebook with a password')