import unittest
import sys
import os

from .redirect import Redirect

class RedirectTest(unittest.TestCase):
  def test_system(self):
    ''' Test if the os.system test even WORKS '''
    r = os.system('echo stderr test 1>&2')
    self.assertEqual(r,0)

  @staticmethod
  def __simple():
    print 'aaa'
    print >>sys.stderr, 'bbb'
    dummy=os.system('echo ccc') #one of the few linux/windows commands.
    #whoami works too! but I need predictable text
    dummy=os.system('echo ddd 1>&2')
    #This won't work for csh. Maybe this will work better?
    #dummy=os.system('whoami impossibleusernamethatshoulodneverbeusedZZZ') and counts Z instead?

  def test_simpleoutJoint(self):
    ''' Test if stdout redirect works '''
    with Redirect() as r:
      self.__simple()
    #theres NO guarentee the io doesn't intermingle, so counting is best
    self.assertEqual(r.stdout_py.count('a'), 3)
    self.assertEqual(r.stdout_c.count('c'), 3)
    self.assertEqual(r.stderr_py.count('b'), 3)
    self.assertEqual(r.stderr_c.count('d'), 3)
    
    self.assertIs(r.stdout, r.stdout_c)
    self.assertIs(r.stdout, r.stdout_py)
    self.assertIs(r.stdout, r.stderr)
    self.assertIs(r.stdout, r.stderr_c)
    self.assertIs(r.stdout, r.stderr_py)

  def test_simpleDisJoint(self):
    ''' Test if stdout redirect works, when they are all separte streams'''
    with Redirect(joint=False) as r:
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
    ''' Test if stdout c only redirect works'''
    with Redirect(                stdout_py=None,
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
    ''' Test if stdout py only redirect works'''
    with Redirect(stdout_c=None,
                  stderr_c=None, stderr_py=None) as r:
      self.__simple()
    #theres NO guarentee the io doesn't intermingle, so counting is best

    self.assertEqual(r.stdout_py.count('a'), 3)
    self.assertEqual(r.stdout_c.count('c'), 0)
    self.assertEqual(r.stderr_py.count('b'), 0)
    self.assertEqual(r.stderr_c.count('d'), 0)

  def test_simpleStderrC(self):
    ''' Test if stderr c only redirect works'''
    with Redirect(stdout_c=None, stdout_py=None,
                                  stderr_py=None) as r:
      self.__simple()
    #theres NO guarentee the io doesn't intermingle, so counting is best
    print r.buffers
    self.assertEqual(r.stdout_py.count('a'), 0)
    self.assertEqual(r.stdout_c.count('c'), 0)
    #self.assertEqual(r.stderr_py.count('b'), 0)
    self.assertEqual(r.stderr_c.count('d'), 3)

  def test_simpleStderrPy(self):
    ''' Test if stderr py only redirect works'''
    with Redirect(stdout_c=None, stdout_py=None,
                  stderr_c=None                 ) as r:
      self.__simple()
    #theres NO guarentee the io doesn't intermingle, so counting is best

    self.assertEqual(r.stdout_py.count('a'), 0)
    self.assertEqual(r.stdout_c.count('c'), 0)
    self.assertEqual(r.stderr_py.count('b'), 3)
    self.assertEqual(r.stderr_c.count('d'), 0)
