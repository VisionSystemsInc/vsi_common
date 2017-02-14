import unittest

from .python import args_to_kwargs, args_to_kwargs2, ARGS, KWARGS

class PythonTest(unittest.TestCase):
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
      
    tests=((a, [1,2,3], {}),
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
           (A, [11, 22, 33], {'x':14}),
           (A, [11], {}),
           (A.fun, [10, 21, 32], {'x':15}),
           (A.fun, [100], {}),
           (A.stat, [12, 33, 44], {'y':35}),
           (A.stat, [21], {}),
           (A.classy, [22, 34, 45], {'y':53}),
           (A.classy, [27], {}),
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
               {'a': 11, 'b': 22, KWARGS: {'x': 14}, ARGS: (33,)},
               {'a': 11, 'b': 15, KWARGS: {}, ARGS: ()},
               {'a': 10, 'b': 21, KWARGS: {'x': 15}, ARGS: (32,)},
               {'a': 100, 'b': 151, KWARGS: {}, ARGS: ()},
               {'a': 12, 'b': 33, KWARGS: {'y': 35}, ARGS: (44,)},
               {'a': 21, 'b': 153, KWARGS: {}, ARGS: ()},
               {'a': 22, 'b': 34, KWARGS: {'y': 53}, ARGS: (45,)},
               {'a': 27, 'b': 157, KWARGS: {}, ARGS: ()},
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
      self.assertEqual(args_to_kwargs2(test[0], *test[1], **test[2]), answer)