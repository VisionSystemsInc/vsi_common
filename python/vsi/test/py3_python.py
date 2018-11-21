import unittest

class PythonTest3(unittest.TestCase):
  def test_keyword_only_args(self):

    from vsi.tools.python import (args_to_kwargs,
                                  args_to_kwargs_unbound,
                                  args_to_kwargs_easy,
                                  args_to_kwargs_unbound_easy,
                                  KWARGS,
                                  ARGS)

    def test1(a, b=15):
      pass
    def test2(a, b=15, **kwargs):
      pass
    def test5(**kwargs):
      pass
    def test3(a, b=15, *args, c, d=27, **kwargs):
      pass
    def test4(a, b=15, *args, c, d=27):
      pass

    tests = ((test3, [1], {'c':3}),
             (test3, [1,2], {'c':3}),
             (test3, [1,2], {'c':3, 'd':4}),
             (test3, [1,2], {'c':3, 'e':5}),
             (test4, [1], {'c':3}),
             (test4, [1,2], {'c':3}),
             (test4, [1,2], {'c':3, 'd':4}),
             )

    answers = ({'a': 1, 'b': 15, 'c': 3, 'd': 27, KWARGS: {}, ARGS: ()},
               {'a': 1, 'b': 2, 'c': 3, 'd': 27, KWARGS: {}, ARGS: ()},
               {'a': 1, 'b': 2, 'c': 3, 'd': 4, KWARGS: {}, ARGS: ()},
               {'a': 1, 'b': 2, 'c': 3, 'd': 27, KWARGS: {'e':5}, ARGS: ()},
               {'a': 1, 'b': 15, 'c': 3, 'd': 27, ARGS: ()},
               {'a': 1, 'b': 2, 'c': 3, 'd': 27, ARGS: ()},
               {'a': 1, 'b': 2, 'c': 3, 'd': 4, ARGS: ()},
               )

    for test, answer in zip(tests, answers):
      self.assertEqual(args_to_kwargs(test[0], test[1], test[2]), answer)
      self.assertEqual(args_to_kwargs_easy(test[0], *test[1], **test[2]), answer)


    # Technically invalid tests
    # Missing positional arg or kwonly arg
    tests = ((test3, [1, 3, 4, 5], {}),
             (test3, [1], {}),
             (test3, [], {}),
             (test3, [], {'c': 11}),
             (test4, [1, 3, 4, 5], {}),
             (test4, [1], {}),
             (test4, [], {}),
             (test4, [], {'c': 11}),
             (test4, [], {'c':3, 'e':5}),
             )

    answers = ({'a': 1, 'b': 3, 'd': 27, KWARGS: {}, ARGS: (4, 5)},
               {'a': 1, 'b': 15, 'd': 27, KWARGS: {}, ARGS: ()},
               {'b': 15, 'd': 27, KWARGS: {}, ARGS: ()},
               {'b': 15, 'c': 11, 'd': 27, KWARGS: {}, ARGS: ()},
               {'a': 1, 'b': 3, 'd': 27, ARGS: (4, 5)},
               {'a': 1, 'b': 15, 'd': 27, ARGS: ()},
               {'b': 15, 'd': 27, ARGS: ()},
               {'b': 15, 'c': 11, 'd': 27, ARGS: ()},
               {'b': 15, 'c': 3, 'd': 27, 'e': 5, ARGS: ()},
               )

    for test, answer in zip(tests, answers):
      with self.assertLogs('vsi.tools.python', level='WARNING') as cm:
        self.assertEqual(args_to_kwargs(test[0], test[1], test[2]), answer)
      self.assertTrue(any('missing required arguments' in x for x in cm.output))
      with self.assertLogs('vsi.tools.python', level='WARNING') as cm:
        self.assertEqual(args_to_kwargs_easy(test[0], *test[1], **test[2]), answer)
      self.assertTrue(any('missing required arguments' in x for x in cm.output))

    # Too many kwargs
    tests = (
             (test1, [], {'a':11, 'b':22, 'c': 33}),
             (test1, [21], {'b':22, 'c': 33}),
             (test4, [1,2], {'c':3, 'e':5}),
             (test4, [], {'c':3, 'e':5}),
            )
    answers = (
               {'a': 11, 'b': 22, 'c': 33},
               {'a': 21, 'b': 22, 'c': 33},
               {'a': 1, 'b': 2, 'c': 3, 'd': 27, 'e':5, ARGS: ()},
               {'b': 15, 'c': 3, 'd': 27, 'e': 5, ARGS: ()},
               )

    for test, answer in zip(tests, answers):
      with self.assertLogs('vsi.tools.python', level='WARNING') as cm:
        self.assertEqual(args_to_kwargs(test[0], test[1], test[2]), answer)
      self.assertTrue(any('Unspecified keyword argument' in x for x in cm.output))
      with self.assertLogs('vsi.tools.python', level='WARNING') as cm:
        self.assertEqual(args_to_kwargs_easy(test[0], *test[1], **test[2]), answer)
      self.assertTrue(any('Unspecified keyword argument' in x for x in cm.output))

    # Too many positional args
    tests = ((test1, [1, 2, 3], {}),
             (test2, [1, 2, 3], {}),
             (test5, [1], {}),
             (test5, [1], {'a':15}),
            )
    answers = ({'a':1, 'b':2},
               {'a':1, 'b':2, KWARGS:{}},
               {KWARGS: {}},
               {KWARGS: {'a':15}},
               )

    for test, answer in zip(tests, answers):
      with self.assertLogs('vsi.tools.python', level='WARNING') as cm:
        self.assertEqual(args_to_kwargs(test[0], test[1], test[2]), answer)
      self.assertTrue(any('Too many positional arguments specified' in x for x in cm.output))
      with self.assertLogs('vsi.tools.python', level='WARNING') as cm:
        self.assertEqual(args_to_kwargs_easy(test[0], *test[1], **test[2]), answer)
      self.assertTrue(any('Too many positional arguments specified' in x for x in cm.output))