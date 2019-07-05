from __future__ import print_function
import unittest
import sys
import os

from vsi.tools.redirect import Redirect, Capture

# class CaptureTest(unittest.TestCase): # TODO: Find out why this is all broken in python 3
class CaptureTest:
  def test_system(self):
    ''' Test if the os.system test even WORKS '''
    r = os.system('echo stderr test 1>&2')
    self.assertEqual(r,0)

  @staticmethod
  def __simple():
    print('aaa')
    print('bbb', file=sys.stderr)
    dummy=os.system('echo ccc') #one of the few linux/windows commands.
    #whoami works too! but I need predictable text
    dummy=os.system('echo ddd 1>&2')
    #This won't work for csh. Maybe this will work better?
    #dummy=os.system('whoami impossibleusernamethatshoulodneverbeusedZZZ') and counts Z instead?

  def test_redirect(self):
    from io import StringIO
    stdout_c = StringIO()
    stdout_py = StringIO()
    stderr_c = StringIO()
    stderr_py = StringIO()

    with Redirect(stdout_c=stdout_c, stderr_c=stderr_c, stdout_py=stdout_py, stderr_py=stderr_py):
      self.__simple()

    stdout_c.seek(0, 0)
    stderr_c.seek(0, 0)
    stdout_py.seek(0, 0)
    stderr_py.seek(0, 0)

    print(1, repr(stdout_c.read()))
    print(2, repr(stderr_c.read()))
    print(3, repr(stdout_py.read()))
    print(4, repr(stderr_py.read()))

  def test_simpleoutGroup(self):
    ''' Test if stdout capture works '''
    with Capture() as r:
      self.__simple()
    #theres NO guarentee the io doesn't interleave, so counting is best
    self.assertEqual(r.stdout_py.count('a'), 3)
    self.assertEqual(r.stdout_c.count('c'), 3)
    self.assertEqual(r.stderr_py.count('b'), 3)
    self.assertEqual(r.stderr_c.count('d'), 3)

    self.assertIs(r.stdout, r.stdout_c)
    self.assertIs(r.stdout, r.stdout_py)
    self.assertIs(r.stdout, r.stderr)
    self.assertIs(r.stdout, r.stderr_c)
    self.assertIs(r.stdout, r.stderr_py)

  def test_simpleUngroup(self):
    ''' Test if stdout capture works, when they are all separte streams'''
    with Capture(group=False) as r:
      self.__simple()
    #theres NO guarentee the io doesn't intermingle, so counting is best

    self.assertEqual(r.stdout_py.count('a'), 3)
    self.assertEqual(r.stdout_c.count('a'), 0)
    self.assertEqual(r.stdout_c.count('c'), 3)
    self.assertEqual(r.stdout_py.count('c'), 0)
    self.assertEqual(r.stderr_py.count('b'), 3)
    self.assertEqual(r.stderr_c.count('b'), 0)
    self.assertEqual(r.stderr_c.count('d'), 3)
    self.assertEqual(r.stderr_py.count('d'), 0)

    self.assertIsNot(r.stdout_c, r.stdout_py)
    self.assertIsNot(r.stderr_c, r.stderr_py)
    self.assertIsNot(r.stdout_c, r.stderr_c)
    self.assertIsNot(r.stdout_py, r.stderr_py)

  def test_simpleStdoutC(self):
    ''' Test if stdout c only capture works'''
    with Capture(               stdout_py=None,
                  stderr_c=None, stderr_py=None) as r:
      self.__simple()
    #theres NO guarentee the io doesn't intermingle, so counting is best

    #self.assertEqual(r.stdout_py.count('a'), 0)
    #Depending on if this was run in python or notbook, you may get different
    #results. In otherwards, if sys.stdout is supposed to go to fd 1, then
    #stderr_py gets rerouted too. If its not, like in notebook, qtconsole,
    #etc, it shouldn't be the same.
    self.assertEqual(r.stdout_c.count('c'), 3)
    self.assertEqual(r.stderr_py.count('b'), 0)
    self.assertEqual(r.stderr_c.count('d'), 0)

  def test_simpleStdoutPy(self):
    ''' Test if stdout py only capture works'''
    with Capture(stdout_c=None,
                  stderr_c=None, stderr_py=None) as r:
      self.__simple()
    #theres NO guarentee the io doesn't intermingle, so counting is best

    self.assertEqual(r.stdout_py.count('a'), 3)
    self.assertEqual(r.stdout_c.count('c'), 0)
    self.assertEqual(r.stderr_py.count('b'), 0)
    self.assertEqual(r.stderr_c.count('d'), 0)

  def test_simpleStderrC(self):
    ''' Test if stderr c only capture works'''
    with Capture(stdout_c=None, stdout_py=None,
                                  stderr_py=None) as r:
      self.__simple()
    #theres NO guarentee the io doesn't intermingle, so counting is best
    print(r.buffers)
    self.assertEqual(r.stdout_py.count('a'), 0)
    self.assertEqual(r.stdout_c.count('c'), 0)
    #self.assertEqual(r.stderr_py.count('b'), 0)
    self.assertEqual(r.stderr_c.count('d'), 3)

  def test_simpleStderrPy(self):
    ''' Test if stderr py only capture works'''
    with Capture(stdout_c=None, stdout_py=None,
                  stderr_c=None                 ) as r:
      self.__simple()
    #theres NO guarentee the io doesn't intermingle, so counting is best

    self.assertEqual(r.stdout_py.count('a'), 0)
    self.assertEqual(r.stdout_c.count('c'), 0)
    self.assertEqual(r.stderr_py.count('b'), 3)
    self.assertEqual(r.stderr_c.count('d'), 0)
