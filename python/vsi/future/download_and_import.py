
#from __future__ import absolute_import

from vsi.tools.network.wget import download
import imp
import tempfile

def download_and_import(module_name, url):
    
  temp = tempfile.NamedTemporaryFile

foo = imp.load_source('module.name', '/path/to/file.py')
foo.MyClass()