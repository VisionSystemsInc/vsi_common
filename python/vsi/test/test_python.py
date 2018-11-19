import unittest
try:
  from unittest import mock
except ImportError:
  import mock

from vsi.tools.python import Try, is_string_like, BasicDecorator, static, WarningDecorator

import sys

try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO


class PythonTest(unittest.TestCase):

  def test_try(self):
    with Try():
      5/0

    with Try(ValueError):
      raise ValueError

    with Try(KeyError, ZeroDivisionError, ValueError):
      raise ValueError

    with self.assertRaises(TypeError):
      with Try(KeyError, ZeroDivisionError, ValueError):
        raise TypeError

    with self.assertRaises(TypeError):
      with Try():
        pass
      raise TypeError

  def test_is_string_like(self):
    self.assertTrue(is_string_like("ok"))
    if sys.version_info[0] == 2:
      self.assertTrue(is_string_like(b"ok"))
    else:
      self.assertFalse(is_string_like(b"ok"))
    self.assertTrue(is_string_like(u"ok"))

  def test_static(self):
    @static(count=0)
    def x(y, z):
      x.count+=1
      return y+z+x.count

    self.assertEqual(x(1,1), 3)
    self.assertEqual(x(1,1), 4)
    self.assertEqual(x(1,1), 5)
    self.assertEqual(x.count, 3)

  def test_basic_decorator(self):
    class MyDecor(BasicDecorator):
      ''' MD '''

      def __init__(self, extra=1):
        self.extra = extra

      def __inner_call__(self, first_arg, *args, **kwargs):
        result = self.fun(first_arg, *args, **kwargs)
        return result + self.extra


    class MyDecor2(MyDecor):
      ''' MD2 '''

    @MyDecor
    def test1(x, y):
      ''' Ok... '''
      return x+y

    @MyDecor2(3)
    def test2(x, y):
      ''' T2 '''
      return x+y

    self.assertEqual(MyDecor.__doc__, ' MD ')
    self.assertEqual(MyDecor2.__doc__, ' MD2 ')
    self.assertEqual(test1.__doc__, ' Ok... ')
    self.assertEqual(test2.__doc__, ' T2 ')

    self.assertEqual(test1(11, 22), 34)
    self.assertEqual(test2(11, 22), 36)

  # @mock.patch('sys.stderr', StringIO())
  def test_warning_decorator(self):
    out = StringIO('')
    @WarningDecorator(output_stream=out)
    def fun():
      return 16

    self.assertEqual(fun(), 16)
    self.assertEqual(out.getvalue(), 'Warning\n')

    # Have to reload vsi.tools.python since sys.stderr is used as a default
    # value
    with mock.patch('sys.stderr', StringIO()):
      try:
        from imp import reload
      except ImportError:
        pass
      import vsi.tools.python
      reload(vsi.tools.python)

      @vsi.tools.python.WarningDecorator("This is a warning")
      def fun():
        return 15
      self.assertEqual(fun(), 15)
      self.assertEqual(sys.stderr.getvalue(), 'This is a warning\n')

    reload(vsi.tools.python)
