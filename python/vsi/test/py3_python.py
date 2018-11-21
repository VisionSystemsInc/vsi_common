import unittest

class PythonTest3(unittest.TestCase):
  def test_keyword_only_args(self):

    from vsi.tools.python import (args_to_kwargs,
                                  args_to_kwargs_unbound,
                                  args_to_kwargs_easy,
                                  args_to_kwargs_unbound_easy)

    def test3(a, b=15, *args, c, d=27, **kwargs):
      pass

    tests = ((test3, [1,2], {'c':3}),)

    answers = ({'a': 1, 'b': 2, 'c': 3, 'd': 27},)

    for test, answer in zip(tests, answers):
      self.assertEqual(args_to_kwargs(test[0], test[1], test[2]), answer)
      self.assertEqual(args_to_kwargs_easy(test[0], *test[1], **test[2]), answer)
