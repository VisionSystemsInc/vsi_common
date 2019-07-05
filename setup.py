import os

from setuptools import find_packages, setup

def read(fname):
  try:
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
  except:
    return ''

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))
#Helps silly crap. Not standard, but oh well
#try:
#  os.chdir(os.path.join(os.path.dirname(__file__), 'python'))
#except OSError:
#  pass

setup(
    name='vsi_common',
    version='0.0.1',
    packages=find_packages(where='python'),
    package_dir={'': 'python'},
    author = 'Andy Neff',
    author_email = 'andrew.neff@vsi-ri.com',
    license='MIT',
    description='VSI Library',
    long_description=read('README.md'),
    url='https://bitbucket.org/visionsystemsinc/vsi_common'
)
