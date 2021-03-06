#!/usr/bin/env python

import argparse
import atexit
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

from subprocess import Popen as Popen_orig, PIPE

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

def get_parser():
  parser = argparse.ArgumentParser()
  aa = parser.add_argument
  aa('--notebook-dir',
     default=os.path.expanduser(os.path.join('~', 'notebooks')),
     help="Location where the notebooks will be stored")
  aa('--ip', default='0.0.0.0', help='IP the notebook server will bind to')
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
  return parser

windows_bash_kernel_json = r'''{
  "display_name": "Bash",
  "language": "bash",
  "argv": [
   "c:\\Windows\\System32\\bash.exe", "-c",
   "~/bash_kernel/bin/python -m bash_kernel -f \"`wslpath \"{connection_file}\"`\""
  ]
}'''

pipfile_3 = '''[[source]]
name = "pypi"
url = "https://pypi.org/simple"
verify_ssl = true

[dev-packages]

[packages]

[requires]
python_version = "3"'''

pipfile_2 = '''[[source]]
name = "pypi"
url = "https://pypi.org/simple"
verify_ssl = true

[dev-packages]

[packages]

[requires]
python_version = "2"'''

jupyter_notebook_config_py = """c.NotebookApp.ip = {ip}
# To link to a specific NIC: pip install netifaces
# c.NotebookApp.ip=netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
# Put in try/except just in case
c.NotebookApp.port = {port}
c.NotebookApp.notebook_dir = {notebooks}
c.NotebookApp.open_browser = {browser}\n"""

add_header = '''#!/usr/bin/env python

import json
import os
import sys
import argparse

parser = argparse.ArgumentParser(description='Add kernel.json for {}')
parser.add_argument('name', help='Name of kernel')
args = parser.parse_args()

try:
  import ipykernel_launcher
  ipykernel = 'ipykernel_launcher'
except ImportError:
  try:
    import ipykernel
    ipykernel = 'ipykernel'
  except ImportError:
    print('IPython kernel not found. "pip install ipykernel" and try again')
    exit(1)

kernel_dir = os.path.join(os.path.dirname(__file__),
                          'jupyter_data',
                          'kernels',
                          args.name)

try:
  os.makedirs(kernel_dir)
except:
  pass
'''

add_virtualenv = add_header.format('virtualenv. Run script from within an activated virtualenv.') + '''
kernel = {'display_name': args.name,
          'argv': [sys.executable, '-m', ipykernel, 
                   '-f', '{connection_file}'],
          'env': {}}

with open(os.path.join(kernel_dir, 'kernel.json'), 'w') as fid:
  json.dump(kernel, fid)

print('{} created'.format(kernel_dir))
'''

add_pipenv = add_header.format('pipenv. Run script from within a pipenv virtualenv ("pipenv run" or "pipenv shell").') + '''
import distutils.spawn
pipenv = distutils.spawn.find_executable('pipenv')

pipfile = os.environ.get('PIPENV_PIPFILE', None)
if pipfile is None:
  from subprocess import Popen, PIPE

  pid = Popen([pipenv, '--where'], stdout=PIPE)
  pipfile = pid.communicate()[0]
  if sys.version_info[0] == 3:
    pipfile = pipfile.decode()
  pipfile = pipfile.rstrip('\\r\\n')

  if not pipfile: # If empty, then it wasn't found
    pipfile = os.getcwd()
  pipfile = os.path.join(pipfile, 'Pipfile')

kernel = {'display_name': args.name,
          'argv': [pipenv, 'run', 'python', '-m', ipykernel, 
                   '-f', '{connection_file}'],
          'env': {'PIPENV_PIPFILE': pipfile}, 'language': 'python'}

with open(os.path.join(kernel_dir, 'kernel.json'), 'w') as fid:
  json.dump(kernel, fid)

print('{} created'.format(kernel_dir))
'''

def main(args=None):
  args = get_parser().parse_args(args)

  tempdir = tempfile.mkdtemp()

  atexit.register(shutil.rmtree, tempdir)

  env = os.environ.copy()
  env.pop('PYTHONPATH', None)
  with open('Pipfile', 'w') as fid:
    fid.write(pipfile_3)

  python2 = None
  python3 = None

  ### Setup python 3 ###
  try:
    Popen(['pipenv', "--three", 'install'], env=env).wait()
  except AssertionError:
    pass
  else:
    # Get python3 venv dir
    python3 = Popen(['pipenv', "--venv"], stdout=PIPE).communicate()[0].decode().strip()
    python2 = '2'

  ### Setup Python 2 ###
  if python2:
    try:
      os.makedirs(python2)
    except os.error:
      pass

  # Set up python2 venv
  env = dict(os.environ)
  env.pop('PYTHONPATH', None)
  with open('2/Pipfile', 'w') as fid:
    fid.write(pipfile_2)

  try:
    Popen(['pipenv', "--two", 'install'], env=env, cwd=python2).wait()
  except AssertionError:
    # If Python2 failed, and python3 succeeded, remove python2 subdir
    if python2 == '2':
      shutil.rmtree(python2)
    python2 = None
  else:
    # get python2 venv dir
    python2 = Popen(['pipenv', "--venv"], stdout=PIPE, cwd="2").communicate()[0].decode().strip()

  # Determine which python dir is the "main" one, favor 3
  if python3:
    python_dir = python3
  else:
    python_dir = python2

  # Setup config dir inside virtual env dir by monkey patching python executable
  os.environ['JUPYTER_CONFIG_DIR'] = os.path.join(os.getcwd(), "jupyter_config")
  os.environ['JUPYTER_DATA_DIR'] = os.path.join(os.getcwd(), "jupyter_data")

  try:
    os.makedirs(os.environ['JUPYTER_CONFIG_DIR'])
  except os.error:
    pass

  with open(os.path.join(os.environ['JUPYTER_CONFIG_DIR'],
                        'jupyter_notebook_config.py'), 'w') as fid:
    fid.write(jupyter_notebook_config_py.format(
      ip=repr(args.ip), port=args.port,
      notebooks=repr(args.notebook_dir),
      browser=str(args.browser)))
    if not args.random_token:
      fid.write("c.NotebookApp.token = {token}\n".format(token=repr(args.token)))
    fid.flush()

  # On windows, we don't install the bash_kernel in windows
  if os.name == 'nt':
    bin_dir = 'Scripts'
    lib_dir = 'Lib'
    bash_kernel = []
  else:
    bin_dir = 'bin'
    lib_dir = 'lib/python*'
    bash_kernel = ['bash_kernel']

  # Patch the site.py file
  site_file = glob(os.path.join(python_dir, lib_dir, 'site.py'))[0]
  patch_site(site_file,
            os.path.relpath(os.environ['JUPYTER_CONFIG_DIR'],
                            os.path.dirname(site_file)),
            os.path.relpath(os.environ['JUPYTER_DATA_DIR'],
                            os.path.dirname(site_file)))

  # Install packages
  Popen(['pipenv',
         'install', 'notebook', 'jupyter-contrib-nbextensions',
         'ipywidgets'] + bash_kernel).wait()
  # Install the main python kernel
  Popen([os.path.join(os.path.abspath(python_dir), bin_dir, 'python'),
        '-m', 'ipykernel', 'install', '--user']).wait()
  # Setup Notebook extensions and widgets
  Popen([os.path.join(os.path.abspath(python_dir), bin_dir, 'jupyter-contrib'),
        'nbextension', 'install', '--user']).wait()
  Popen([os.path.join(os.path.abspath(python_dir),
                      bin_dir, 'jupyter-nbextension'),
        'enable', '--py', '--user', 'widgetsnbextension']).wait()

  # Setup bash_kernel
  if os.name != "nt":
    Popen([os.path.join(os.path.abspath(python_dir), bin_dir, 'python'),
          '-m', 'bash_kernel', 'install', '--user', '--name', 'Bash']).wait()
  else:
    # on windows, use wsl to setup bash_kernel if available
    if os.path.exists('c:\\Windows\\System32\\bash.exe'):
      Popen(['c:\\Windows\\System32\\bash.exe',
             '-c',
             'tmp_dir="\\$(mktemp -d)";'
             'cd "\\${tmp_dir}";'
             'python3 <(curl -L https://bootstrap.pypa.io/get-pip.py) --no-cache-dir -I --root "\\${tmp_dir}" virtualenv;'
             'PYTHONPATH="\\$(cd "\\${tmp_dir}"/usr/local/lib/python*/*-packages/; pwd)" "\\${tmp_dir}/usr/local/bin/virtualenv" ~/bash_kernel;'
             '~/bash_kernel/bin/pip install --no-cache-dir bash_kernel ipykernel;'
             'rm -r "\\${tmp_dir}"'], shell=False).wait()
      try:
        os.makedirs(os.path.join(os.environ['JUPYTER_DATA_DIR'], 'kernels',
                                 'bash'))
      except os.error:
        pass
      with open(os.path.join(os.environ['JUPYTER_DATA_DIR'], 'kernels', 'bash',
                            'kernel.json'), 'w') as fid:
        fid.write(windows_bash_kernel_json)

  # if both pythons worked, setup multi kernels
  if python2 and python3:
    with open(os.path.join(os.environ['JUPYTER_CONFIG_DIR'],
                        'jupyter_notebook_config.py'), 'a') as fid:
      fid.write("c.MultiKernelManager.default_kernel_name = 'python3'")

    # patch python2's site too
    site_file = glob(os.path.join(python2, lib_dir, 'site.py'))[0]
    patch_site(site_file,
              os.path.relpath(os.environ['JUPYTER_CONFIG_DIR'],
                              os.path.dirname(site_file)),
              os.path.relpath(os.environ['JUPYTER_DATA_DIR'],
                              os.path.dirname(site_file)))
    # Install python2's ipywidget too
    Popen(['pipenv', 'install', 'ipywidgets'], cwd="2").wait()
    # Install the python2 kernel
    Popen([os.path.join(python2, bin_dir, 'python'),
          '-m', 'ipykernel', 'install', '--user', '--name', 'python2']).wait()


  # Add add_virtualenv script
  with open('add_virtualenv.py', 'w') as fid:
    fid.write(add_virtualenv)
  os.chmod('add_virtualenv.py', 0o755)

  # Add add_pipenv script
  with open('add_pipenv.py', 'w') as fid:
    fid.write(add_pipenv)
  os.chmod('add_pipenv.py', 0o755)

  print("\n---------------------------------\n")
  print("Notebook configured successfully!")
  print('Run "jupyter-notebook password" to '
        'secure your notebook with a password')

if __name__=='__main__':
  main()