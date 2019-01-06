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

def parse_args(args=None):
  parser = get_parser()
  return parser.parse_args(args)


def main(args=None):
  args = parse_args(args)

  tempdir = tempfile.mkdtemp()

  atexit.register(shutil.rmtree, tempdir)
  # d2=os.path.join(tempdir, '2')
  # d3=os.path.join(tempdir, '3')
  # os.mkdir(d2)
  # os.mkdir(d3)

  python2 = None
  python3 = None

  # if sys.version_info.major == 3:
  #   python3 = sys.executable
  # else:
  #   python2 = sys.executable

  # If I am supposed to look for the other python, do so.
  # if not args.one_python:
  #   if sys.version_info.major == 3:
  #     python2 = which('python2', 'exe')
  #   else:
  #     python3 = which('python3', 'exe')

  # pip_install = urlopen('https://bootstrap.pypa.io/get-pip.py').read().decode(
  #     "utf-8")
  # pip_filename = os.path.join(tempdir, 'get-pip.py')
  # with open(pip_filename, 'w') as fid:
  #   fid.write(pip_install)
  #   fid.flush()

  # python2_venv = ''
  # python2_pipfile = 'Pipfile'

  # Set up python3 venv
  # python2_venv = 'python2'
  env = dict(os.environ)
  env.pop('PYTHONPATH', None)

  env = dict(os.environ)
  env.pop('PYTHONPATH', None)
  with open('Pipfile', 'w') as fid:
    fid.write('''[[source]]
name = "pypi"
url = "https://pypi.org/simple"
verify_ssl = true

[dev-packages]

[packages]

[requires]
python_version = "3"''')

  python2 = None

  try:
    Popen(['pipenv', "--three", 'install'], env=env).wait()
  except AssertionError:
    pass
  else:
    python3 = Popen(['pipenv', "--venv"], stdout=PIPE).communicate()[0].decode().strip()
    python2 = '2'

  # env['PYTHONUSERBASE'] = d3
  # Popen(['pipenv', '--user', 'virtualenv', '-U'],
  #       env=env).wait()
  # venv_file = find('virtualenv.py', d3)
  # env['PYTHONPATH'] = os.path.dirname(venv_file)
  # Popen([python3, venv_file, os.path.abspath(args.venv)]).wait()

  if python2:
    os.mkdir(python2)

  # Set up python2 venv
  env = dict(os.environ)
  env.pop('PYTHONPATH', None)
  with open('2/Pipfile', 'w') as fid:
    fid.write('''[[source]]
name = "pypi"
url = "https://pypi.org/simple"
verify_ssl = true

[dev-packages]

[packages]

[requires]
python_version = "2"''')

  try:
    Popen(['pipenv', "--two", 'install'], env=env, cwd=python2).wait()
  except AssertionError:
    if pythons:
      shutil.rmtree(python2)
  else:
    python2 = Popen(['pipenv', "--venv"], stdout=PIPE, cwd="2").communicate()[0].decode().strip()


#     env['PYTHONUSERBASE'] = d2
#     Popen([python2, pip_filename, '--user', 'virtualenv', '-U'],
#           env=env).wait()
#     venv_file = find('virtualenv.py', d2)
#     env['PYTHONPATH'] = os.path.dirname(venv_file)
#     Popen([python2, venv_file,
#           os.path.abspath(os.path.join(args.venv, python2_venv))]).wait()

  if python3:
    python_dir = python3
  else:
    python_dir = python2

  # Setup config dir inside virtual env dir by monkey patching python executable
  os.environ['JUPYTER_CONFIG_DIR'] = os.path.join(python_dir, "jupyter_config")
  os.environ['JUPYTER_DATA_DIR'] = os.path.join(python_dir, "jupyter_data")

  try:
    os.makedirs(os.environ['JUPYTER_CONFIG_DIR'])
  except os.error:
    pass

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
    lib_dir = 'Lib'
    bash_kernel = ['bash_kernel']
  else:
    bin_dir = 'bin'
    lib_dir = 'lib/python*'
    bash_kernel = []

  site_file = glob(os.path.join(python_dir, lib_dir, 'site.py'))[0]
  patch_site(site_file,
            os.path.relpath(os.environ['JUPYTER_CONFIG_DIR'],
                            os.path.dirname(site_file)),
            os.path.relpath(os.environ['JUPYTER_DATA_DIR'],
                            os.path.dirname(site_file)))

  Popen(['pipenv',
         'install', 'notebook', 'jupyter-contrib-nbextensions',
         'ipywidgets'] + bash_kernel).wait()
  Popen([os.path.join(os.path.abspath(python_dir), bin_dir, 'python'),
        '-m', 'ipykernel.kernelspec', '--user']).wait()
  if os.name != "nt":
    Popen([os.path.join(os.path.abspath(python_dir), bin_dir, 'python'),
          '-m', 'bash_kernel.install', '--user']).wait()
  Popen([os.path.join(os.path.abspath(python_dir), bin_dir, 'jupyter-contrib'),
        'nbextension', 'install', '--user']).wait()
  Popen([os.path.join(os.path.abspath(python_dir),
                      bin_dir, 'jupyter-nbextension'),
        'enable', '--py', '--user', 'widgetsnbextension']).wait()

  if os.name == "nt":
    Popen(['c:\\Windows\\System32\\bash.exe',
           '-c',
           'tmp_dir="\\$(mktemp -d)";'
           'cd "\\${tmp_dir}";'
           'python3 <(curl -L https://bootstrap.pypa.io/get-pip.py) --no-cache-dir -I --root "\\${tmp_dir}" virtualenv;'
           'PYTHONPATH="\\$(cd "\\${tmp_dir}"/usr/local/lib/python*/*-packages/; pwd)" "\\${tmp_dir}/usr/local/bin/virtualenv" ~/bash_kernel;'
           '~/bash_kernel/bin/pip install --no-cache-dir bash_kernel;'
           'rm -r "\\${tmp_dir}"'], shell=False).wait()

  if python2 and python3:
    with open(os.path.join(os.environ['JUPYTER_CONFIG_DIR'],
                        'jupyter_notebook_config.py'), 'a') as fid:
      fid.write("c.MultiKernelManager.default_kernel_name = 'python2'")

    site_file = glob(os.path.join(python2, lib_dir, 'site.py'))[0]

    patch_site(site_file,
              os.path.relpath(os.environ['JUPYTER_CONFIG_DIR'],
                              os.path.dirname(site_file)),
              os.path.relpath(os.environ['JUPYTER_DATA_DIR'],
                              os.path.dirname(site_file)))
    Popen(['pipenv', 'install', 'ipywidgets'], cwd="2").wait()
    Popen([os.path.join(python2, bin_dir, 'python'),
          '-m', 'ipykernel.kernelspec', '--user', '--name', 'python2']).wait()


  # Add add_virtualenv script
  with open('add_virtualenv', 'w') as fid:
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

venv="$(PIPENV_PIPFILE="$(dirname "${BASH_SOURCE[0]}")/Pipfile" pipenv --venv)"

mkdir -p "${venv}/jupyter_data/kernels/${1}"

cat << EOS > "${venv}/jupyter_data/kernels/${1}/kernel.json"
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
  os.chmod('add_virtualenv', 0o755)

  # Add add_pipenv script
  with open('add_pipenv', 'w') as fid:
    fid.write('''#!/usr/bin/env bash

set -eu

if pipenv run python -c "import ipykernel_launcher" > /dev/null 2>&1; then
  ipykernel=ipykernel_launcher
elif pipenv run python -c "import ipykernel" > /dev/null 2>&1; then
  ipykernel=ipykernel
else
  echo "IPython kernel not found."
  exit 1
fi

venv="$(PIPENV_PIPFILE="$(dirname "${BASH_SOURCE[0]}")/Pipfile" pipenv --venv)"

mkdir -p "${venv}/jupyter_data/kernels/${1}"

cat << EOS > "${venv}/jupyter_data/kernels/${1}/kernel.json"
{
 "display_name": "${1}",
 "argv": [
  "$(command -v pipenv)",
  "run",
  "python",
  "-m",
  "${ipykernel}",
  "-f",
  "{connection_file}"
 ],
 "env": {"PIPENV_PIPFILE":"${PIPENV_PIPFILE-$(pipenv --venv)/Pipfile}"},
 "language": "python"
}
EOS''')
  os.chmod('add_pipenv', 0o755)

  # Add relocate script
  with open('relocate', 'w') as fid:
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
  os.chmod('relocate', 0o755)

  print("\n---------------------------------\n")
  print("Notebook configured successfully!")
  print('Run "jupyter-notebook password" to '
        'secure your notebook with a password')

if __name__=='__main__':
  main()