import os
import sys
from vsi.iglob import glob
from glob import glob as glob_orig

from vsi.tools.dir_util import Chdir
from vsi.test.utils import TestCase

class GlobTest(TestCase):
  def setUp(self):

    super().setUp()

    basedir = self.temp_dir.name
    self.test1 = os.path.join(basedir, 'test1')
    self.test2 = os.path.join(basedir, 'TeSt2')

    os.mkdir(self.test1)
    os.mkdir(self.test2)
    open(os.path.join(basedir, 'test3'), 'w').close()
    open(os.path.join(basedir, 'TESt4'), 'w').close()

    open(os.path.join(self.test1, 'file1.txt'), 'w').close()
    open(os.path.join(self.test1, 'FILE21.TXT'), 'w').close()
    open(os.path.join(self.test1, 'file3.TxT'), 'w').close()
    open(os.path.join(self.test2, 'file1.tXt'), 'w').close()

    if os.path.normcase('test1') != os.path.normcase('TEST1'):
      self.test3 = os.path.join(basedir, 'TEST1')
      os.mkdir(self.test3)
      open(os.path.join(self.test3, 'file1.txt'), 'w').close()

    if os.path.normcase('test1') != os.path.normcase('TEST1'):
      self.extra = 1
    else:
      self.extra = 0

    self.testData = [[os.path.join(basedir, 'test*', '*'),         3,            4+self.extra, None],
                     [os.path.join(basedir, '*', '*.txt'),         1+self.extra, 4+self.extra, None],
                     [os.path.join(basedir, '?e*1', '*1*x*'),      1,            2+self.extra, None],
                     [os.path.join(basedir, '?e*', '*1*x*'),       1,            3+self.extra, None],
                     [os.path.join(basedir, 'test*'),              2,            4+self.extra, None],
                     [os.path.join(basedir, 'test*')+os.path.sep,  1,        2+self.extra, None],
                     [self.test1.upper(),                          0,            1+self.extra, None],
                     [self.test1,                                  1,            1+self.extra, None],
                     [self.test1.upper()+os.path.sep,              0,            1+self.extra, None],
                     [self.test1+os.path.sep,                      1,            1+self.extra, None],
                     [os.path.join(self.test1, 'file1.txt').upper(), 0,          1+self.extra, None],
                     [os.path.join(self.test1, 'file1.txt'),       1,            1+self.extra, None],
                     ['*',                                         3,            3,      self.test1],
                     [os.path.join(os.path.curdir, '*'),           3,            3,      self.test1],
                     [os.path.join(os.path.pardir, '*'),           5,            5,      self.test1],]

  def test_runAllTests(self):
    for (pattern, result, resultI, testDir) in self.testData:
      if testDir is not None:
        with Chdir(self.test1):
          self.run_test(pattern, result, resultI)
      else:
        self.run_test(pattern, result, resultI)

  # 2/3 compat
  def assertSortedEqual(self, actual, expected, msg=None):
    if sys.version_info.major == 2:
      self.assertItemsEqual(actual, expected, msg)
    else:
      self.assertCountEqual(actual, expected, msg)

  def run_test(self, pattern, result, resultI):
    self.assertEqual(len(glob(pattern, True)), result)
    self.assertEqual(len(glob(pattern, False)), resultI)
    self.assertSortedEqual(glob(pattern), glob_orig(pattern))

