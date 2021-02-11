"""
MIT License

Copyright (c) 2017 Youhei Sakurai

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

https://github.com/sakurai-youhei/envcontext
"""

# Vendored because the setup.py file in envcontext is written poorly, and
# creates a version mismatch starting in pip 20.3 and newer

"""
Usage:
    os.environ['MYVAR'] = 'oldvalue'
    with EnvironmentContex(MYVAR='myvalue', MYVAR2='myvalue2'):
        print(os.getenv('MYVAR'))  # Should print myvalue.
        print(os.getenv('MYVAR2'))  # Should print myvalue2.
    print(os.getenv('MYVAR'))  # Should print oldvalue.
    print(os.getenv('MYVAR2'))  # Should print None.
"""

from os import environ

class EnvironmentContext(object):
  """Context manager to update environment variables with preservation"""
  def __init__(self, **kwargs):
    self.envs = kwargs
    self.preservation = {}

  def __enter__(self):
    for k in self.envs:
      if k not in self.preservation:
        self.preservation[k] = environ.get(k)
      environ[k] = self.envs[k]

  def __exit__(self, *_):
    for k in self.preservation:
      if self.preservation[k]:
        environ[k] = self.preservation[k]
      else:
        environ.pop(k, None)