import os

try:
  # Use setuptools if available, for install_requires (among other things).
  import setuptools
  from setuptools import setup
except ImportError:
  setuptools = None
  from distutils.core import setup

with open('README.md', 'r') as fid:
  readme = fid.read()

def read(fname):
  return open(os.path.join(os.path.dirname(__file__), fname)).read()

#Helps silly crap. Not standard, but oh well
try:
  os.chdir(os.path.join(os.path.dirname(__file__), 'python'))
except OSError:
  pass

setup(
    name='vsi_common',
    version='0.0.1',
    packages=['vsi'],
    author = 'Andy Neff',
    author_email = 'andrew.neff@vsi-ri.com',
    license='MIT',
    description='VSI Library',
    long_description=readme,
    url='https://bitbucket.org/visionsystemsinc/vsi_common'
)
