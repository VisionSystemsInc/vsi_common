import unittest
try:
  from unittest import mock
except ImportError:
  import mock

from vsi.tools.python import (Try, is_string_like, BasicDecorator, static,
                              WarningDecorator, args_to_kwargs,
                              args_to_kwargs_unbound, args_to_kwargs_easy,
                              args_to_kwargs_unbound_easy,
                              ARGS, KWARGS, is_class_method, is_static_method,
                              ArgvContext, nested_update, nested_in_dict)

import sys

if sys.version_info.major > 2:
  from vsi.test.py3_python import *

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
        from importlib import reload
      except ImportError:
        from imp import reload
      import vsi.tools.python
      reload(vsi.tools.python)

      @vsi.tools.python.WarningDecorator("This is a warning")
      def fun():
        return 15
      self.assertEqual(fun(), 15)
      self.assertEqual(sys.stderr.getvalue(), 'This is a warning\n')

    reload(vsi.tools.python)

  def test_is_static_methods(self):
    def fun(a):
      pass
    class A(object):
      def b(self):
        pass
      @staticmethod
      def c(d):
        pass

      @classmethod
      def d(cls):
        pass

    class B(A):
      def __new__(cls):
        return cls
      @staticmethod
      def b(a):
        pass

      def c(self):
        pass

      def d(self):
        pass

    A.fun = fun
    B.fun = staticmethod(fun)
    B.fun2 = classmethod(fun)

    self.assertFalse(is_static_method(A, 'fun'))
    self.assertTrue(is_static_method(A, '__new__'))
    self.assertFalse(is_static_method(A, '__init__'))
    self.assertFalse(is_static_method(A, '__subclasshook__'))
    self.assertFalse(is_static_method(A, 'b'))
    self.assertTrue(is_static_method(A, 'c'))
    self.assertFalse(is_static_method(A, 'd'))

    a=A()
    self.assertFalse(is_static_method(a, 'fun'))
    self.assertTrue(is_static_method(a, '__new__'))
    self.assertFalse(is_static_method(a, '__init__'))
    self.assertFalse(is_static_method(a, '__subclasshook__'))
    self.assertFalse(is_static_method(a, 'b'))
    self.assertTrue(is_static_method(a, 'c'))
    self.assertFalse(is_static_method(a, 'd'))

    self.assertTrue(is_static_method(B, 'fun'))
    self.assertTrue(is_static_method(B, '__new__'))
    self.assertFalse(is_static_method(B, '__init__'))
    self.assertFalse(is_static_method(B, '__subclasshook__'))
    self.assertTrue(is_static_method(B, 'b'))
    self.assertFalse(is_static_method(B, 'c'))
    self.assertFalse(is_static_method(B, 'd'))

    b = B()
    self.assertTrue(is_static_method(b, 'fun'))
    self.assertTrue(is_static_method(b, '__new__'))
    self.assertFalse(is_static_method(b, '__init__'))
    self.assertFalse(is_static_method(b, '__subclasshook__'))
    self.assertTrue(is_static_method(b, 'b'))
    self.assertFalse(is_static_method(b, 'c'))
    self.assertFalse(is_static_method(b, 'd'))

  def test_is_static_methods(self):
    def fun(a):
      pass
    class A(object):
      def b(self):
        pass
      @staticmethod
      def c(d):
        pass

      @classmethod
      def d(cls):
        pass

    class B(A):
      def __new__(cls):
        return cls
      @classmethod
      def b(a):
        pass

      def c(self):
        pass

      def d(self):
        pass

    A.fun = fun
    B.fun = classmethod(fun)

    self.assertFalse(is_class_method(A, 'fun'))
    self.assertFalse(is_class_method(A, '__new__'))
    self.assertFalse(is_class_method(A, '__init__'))
    self.assertTrue(is_class_method(A, '__subclasshook__'))
    self.assertFalse(is_class_method(A, 'b'))
    self.assertFalse(is_class_method(A, 'c'))
    self.assertTrue(is_class_method(A, 'd'))

    a=A()
    self.assertFalse(is_class_method(a, 'fun'))
    self.assertFalse(is_class_method(a, '__new__'))
    self.assertFalse(is_class_method(a, '__init__'))
    self.assertTrue(is_class_method(a, '__subclasshook__'))
    self.assertFalse(is_class_method(a, 'b'))
    self.assertFalse(is_class_method(a, 'c'))
    self.assertTrue(is_class_method(a, 'd'))

    self.assertTrue(is_class_method(B, 'fun'))
    self.assertFalse(is_class_method(B, '__new__'))
    self.assertFalse(is_class_method(B, '__init__'))
    self.assertTrue(is_class_method(B, '__subclasshook__'))
    self.assertTrue(is_class_method(B, 'b'))
    self.assertFalse(is_class_method(B, 'c'))
    self.assertFalse(is_class_method(B, 'd'))

    b = B()
    self.assertTrue(is_class_method(b, 'fun'))
    self.assertFalse(is_class_method(b, '__new__'))
    self.assertFalse(is_class_method(b, '__init__'))
    self.assertTrue(is_class_method(b, '__subclasshook__'))
    self.assertTrue(is_class_method(b, 'b'))
    self.assertFalse(is_class_method(b, 'c'))
    self.assertFalse(is_class_method(b, 'd'))

  def test_arg_to_kwargs(self):
    def a(x, y, z):
      pass
    def f(x, y, z=18):
      pass
    def b(x, *args):
      pass
    def c(x=15, **kwargs):
      pass
    def d(a, y=15, *args, **kwargs):
      pass
    def e(a, **kwargs):
      pass
    def g(x=11):
      pass
    def h(*args):
      pass
    def i(**kwargs):
      pass

    class A(object):
      def __init__(self, a, b=15, *args, **kwargs):
        pass
      def fun(self, a, b=151, *args, **kwargs):
        pass
      def __call__(self, a, b=152, *args, **kwargs):
        pass
      @staticmethod
      def stat(a, b=153, *args, **kwargs):
        pass
      @classmethod
      def classy(cls, a, b=157, *args, **kwargs):
        pass

    aa=A(1)

    tests = ((a, [1,2,3], {}),
             (f, [1,2,3], {}),
             (f, [1,2], {}),
             (f, [1,2], {'z':22}),
             (b, [1], {}),
             (b, [1,2,3], {}),
             (c, [1], {'w':22}),
             (c, [], {'x':11, 'w':22}),
             (c, [], {'w':22}),
             (d, [11], {}),
             (d, [11, 12], {}),
             (d, [11, 12, 13, 14], {}),
             (d, [11], {'x':15, 'y':16}),
             (d, [], {'a':10, 'x':16}),
             (d, [11, 12, 13, 14], {'x':15, 'z':37}),
             (e, [1], {'x':14}),
             (e, [], {'a':2, 'x':14}),
             (g, [], {}),
             (g, [1], {}),
             (h, [], {}),
             (h, [100, 202, 303], {}),
             (i, [], {}),
             (i, [], {'a': 31, 'b':29}),
             (A, [11, 22, 33], {'x':14}),
             (A, [11], {}),
             (aa.fun, [13, 23, 34], {'x':16}),
             (aa.fun, [99], {}),
             (aa, [14, 24, 35], {'x':17}),
             (aa, [98], {}),
             (aa.stat, [12, 33, 44], {'y':35}),
             (aa.stat, [21], {}),
             (aa.classy, [22, 34, 45], {'y':53}),
             (aa.classy, [27], {}),
             (d, [111, 222, 333], {'xx':92, 'args':28}))#This is valid python

    answers = ({'y': 2, 'x': 1, 'z': 3},
               {'y': 2, 'x': 1, 'z': 3},
               {'y': 2, 'x': 1, 'z': 18},
               {'y': 2, 'x': 1, 'z': 22},
               {'x': 1, ARGS: ()},
               {'x': 1, ARGS: (2, 3)},
               {'x': 1, KWARGS: {'w': 22}},
               {'x': 11, KWARGS: {'w': 22}},
               {'x': 15, KWARGS: {'w': 22}},
               {'a': 11, 'y': 15, KWARGS: {}, ARGS: ()},
               {'a': 11, 'y': 12, KWARGS: {}, ARGS: ()},
               {'a': 11, 'y': 12, KWARGS: {}, ARGS: (13, 14)},
               {'a': 11, 'y': 16, KWARGS: {'x': 15}, ARGS: ()},
               {'a': 10, 'y': 15, KWARGS: {'x': 16}, ARGS: ()},
               {'a': 11, 'y': 12, KWARGS: {'x': 15, 'z': 37}, ARGS: (13, 14)},
               {'a': 1, KWARGS: {'x': 14}},
               {'a': 2, KWARGS: {'x': 14}},
               {'x': 11},
               {'x': 1},
               {ARGS: ()},
               {ARGS: (100, 202, 303)},
               {KWARGS: {}},
               {KWARGS: {'a': 31, 'b': 29}},
               {'a': 11, 'b': 22, KWARGS: {'x': 14}, ARGS: (33,)},
               {'a': 11, 'b': 15, KWARGS: {}, ARGS: ()},
               {'a': 13, 'b': 23, KWARGS: {'x': 16}, ARGS: (34,)},
               {'a': 99, 'b': 151, KWARGS: {}, ARGS: ()},
               {'a': 14, 'b': 24, KWARGS: {'x': 17}, ARGS: (35,)},
               {'a': 98, 'b': 152, KWARGS: {}, ARGS: ()},
               {'a': 12, 'b': 33, KWARGS: {'y': 35}, ARGS: (44,)},
               {'a': 21, 'b': 153, KWARGS: {}, ARGS: ()},
               {'a': 22, 'b': 34, KWARGS: {'y': 53}, ARGS: (45,)},
               {'a': 27, 'b': 157, KWARGS: {}, ARGS: ()},
               {'a': 111, 'y':222, ARGS: (333,), KWARGS: {'xx': 92, 'args':28}})

    for test, answer in zip(tests, answers):
      self.assertEqual(args_to_kwargs(test[0], test[1], test[2]), answer)
      self.assertEqual(args_to_kwargs_easy(test[0], *test[1], **test[2]), answer)

    tests = ((A, 'fun', [10, 21, 32], {'x':15}),
             (A, 'fun', [100], {}),
             (A, 'stat', [12, 33, 44], {'y':35}),
             (A, 'stat', [21], {}),
             (A, 'classy', [22, 34, 45], {'y':53}),
             (A, 'classy', [27], {}))
    answers = ({'a': 10, 'b': 21, KWARGS: {'x': 15}, ARGS: (32,)},
                {'a': 100, 'b': 151, KWARGS: {}, ARGS: ()},
                {'a': 12, 'b': 33, KWARGS: {'y': 35}, ARGS: (44,)},
                {'a': 21, 'b': 153, KWARGS: {}, ARGS: ()},
                {'a': 22, 'b': 34, KWARGS: {'y': 53}, ARGS: (45,)},
                {'a': 27, 'b': 157, KWARGS: {}, ARGS: ()})

    for test, answer in zip(tests, answers):
      self.assertEqual(args_to_kwargs_unbound(test[0], test[1], test[2], test[3]), answer)
      self.assertEqual(args_to_kwargs_unbound_easy(test[0], test[1], *test[2], **test[3]), answer)
      if sys.version_info.major == 2:
        value = getattr(test[0], test[1])
        self.assertEqual(args_to_kwargs(value, test[2], test[3]), answer)
        self.assertEqual(args_to_kwargs_easy(value, *test[2], **test[3]), answer)

  def test_arg_context(self):
    with mock.patch('sys.argv', ['arg0', 'arg1', 'arg2']):
      self.assertEqual(sys.argv, ['arg0', 'arg1', 'arg2'])
      with ArgvContext('00', '11', '22'):
        self.assertEqual(sys.argv, ['00', '11', '22'])
      self.assertEqual(sys.argv, ['arg0', 'arg1', 'arg2'])

  def test_nested_update(self):
    x={"a":1, "b": {"c": 2, "d": 3}, "d": 4}

    # Normal update
    y={"a":11, "b":{"c":22, "e":33}}
    ans={"a":11, "b": {"c": 22, "d": 3, "e":33}, "d": 4}
    z=x.copy()
    nested_update(z, y)
    self.assertEqual(z, ans)

    # Keys not there before + replace dict with int
    y={"b": 5, "e":{"c":22, "e":33}, "f": 6}
    ans={"a":1, "b": 5, "e": {"c": 22, "e":33}, "d": 4, "f":6}
    z=x.copy()
    nested_update(z, y)
    self.assertEqual(z, ans)

    y={"a": {"g": 15}}
    z=x.copy()
    with self.assertRaises(TypeError):
      nested_update(z, y)

  def test_nested_in_dict(self):
    b = {'a': 5, 'b': 6}

    self.assertTrue(nested_in_dict({'a': 5}, b))
    self.assertFalse(nested_in_dict({'a': 5, 'b':0}, b))
    self.assertFalse(nested_in_dict({'a': 5, 'c':7}, b))

    c = {'a': 5, 'b': 6, 'c': { 'd': { 'e': 1 }, 'f': 2} }
    self.assertTrue(nested_in_dict({'a': 5}, c))
    self.assertTrue(nested_in_dict({'c': {}}, c))
    self.assertFalse(nested_in_dict({'g': {}}, c))
    self.assertTrue(nested_in_dict({'c': {'d':{}}}, c))
    self.assertTrue(nested_in_dict({'c': {'d':{'e':1}}}, c))
    self.assertTrue(nested_in_dict(c, c))
