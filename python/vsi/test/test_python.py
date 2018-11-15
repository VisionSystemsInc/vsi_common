import unittest

import vsi.tools.python
from vsi.tools.python import BasicDecorator

class PythonTest(unittest.TestCase):

  def test_try(self):
    with vsi.tools.python.Try():
      5/0

  def test_basic_decorator(self):
    class MyDecor(BasicDecorator):
      def __init__(self, name='Default'):
        self.name = name

      def __inner_call__(self, first_arg, *args, **kwargs):
        self.fun.name = self.name
        result = self.fun(first_arg, *args, **kwargs)
        print(self.name, first_arg, result)
        return result

    @MyDecor
    def test1(x, y):
      ''' Ok... '''
      return x+y

    @MyDecor('not default')
    def test2(x, y):
      return x+y

    help(BasicDecorator)

    # help(type(test1))

    # self.assertEqual(test1.name, 'Default')
    # self.assertEqual(test2.name, 'not default')
