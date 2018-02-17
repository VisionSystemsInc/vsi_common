#!/usr/bin/env python

import argparse
import atexit
import imp
import os
import shutil
import sys
import tempfile
#imp.find_module('site')[1]

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

#https://stackoverflow.com/a/5227009/4166604
def which(file):
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
aa('--token', default='', help='Fixed token to use')
aa('venv', default='.', nargs='?', help='Directory of the venv')
args = parser.parse_args()

tempdir = tempfile.mkdtemp()

atexit.register(shutil.rmtree, tempdir)
d2=os.path.join(tempdir, '2')
d3=os.path.join(tempdir, '3')
os.mkdir(d2)
os.mkdir(d3)

#This won't work in windows, but oh well
if sys.version_info.major == 3:
  python3 = sys.executable
  python2 = which('python2')
else:
  python2 = sys.executable
  python3 = which('python3')

pip_install = urlopen('https://bootstrap.pypa.io/get-pip.py').read().decode(
    "utf-8")
pip_filename = os.path.join(tempdir, 'get-pip.py')
with open(pip_filename, 'w') as fid:
  fid.write(pip_install)
  fid.flush()

python2_venv = ''

if python3:
  python2_venv = 'python2'
  env = dict(os.environ)
  env.pop('PYTHONPATH', None)
  env['PYTHONUSERBASE'] = d3
  Popen([python3, pip_filename, '--user', 'virtualenv', '-U'], env=env).wait()
  venv_file = find('virtualenv.py', d3)
  env['PYTHONPATH'] = os.path.dirname(venv_file)
  Popen([python3, venv_file, os.path.abspath(args.venv)]).wait()

if python2:
  env = dict(os.environ)
  env.pop('PYTHONPATH', None)
  env['PYTHONUSERBASE'] = d2
  Popen([python2, pip_filename, '--user', 'virtualenv', '-U'], env=env).wait()
  venv_file = find('virtualenv.py', d2)
  env['PYTHONPATH'] = os.path.dirname(venv_file)
  Popen([python2, venv_file,
         os.path.abspath(os.path.join(args.venv, python2_venv))]).wait()

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
    fid.write("c.NotebookApp.token = {token}".format(token=repr(args.token)))
  fid.flush()

if os.name == 'nt':
  bin_dir = 'Scripts'
else:
  bin_dir = 'bin'

site_file = find('site.py', args.venv)
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
  site_file = find('site.py', os.path.join(args.venv, python2_venv))
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


print("\n---------------------------------\n")
print("Notebook configured successfully!")
print('Run "jupyter-notebook password" to '
      'secure your notebook with a password')