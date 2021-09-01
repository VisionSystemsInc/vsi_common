import os
import unittest

from vsi.tools.dir_util import (
  find_file_in_path, is_subdir
)
from vsi.test.utils import TestCase

class DirTest(TestCase):
  pass


class FindFileInPath(DirTest):
  def test_path_argument(self):
    # Empty lists
    self.assertIsNone(find_file_in_path('foo.txt', ''))
    self.assertIsNone(find_file_in_path('foo.txt', os.pathsep))

    open(os.path.join(self.temp_dir.name, 'bar.txt',), 'wb').close()

    # Just the dir
    self.assertIsNone(find_file_in_path('foo.txt', self.temp_dir.name))
    self.assertEqual(find_file_in_path('bar.txt', self.temp_dir.name),
        os.path.join(self.temp_dir.name, 'bar.txt'))

    # Multiple
    self.assertEqual(find_file_in_path('bar.txt',
        os.pathsep.join([
            os.path.join(self.temp_dir.name, '1'),
            os.path.join(self.temp_dir.name, '2'),
            self.temp_dir.name,
            os.path.join(self.temp_dir.name, '3')
        ])),
        os.path.join(self.temp_dir.name, 'bar.txt'))


  def test_env(self):
    # Empty lists
    with unittest.mock.patch.dict(os.environ, {'PATH': ""}):
      self.assertIsNone(find_file_in_path('foo.txt'))
    with unittest.mock.patch.dict(os.environ, {'PATH': os.pathsep}):
      self.assertIsNone(find_file_in_path('foo.txt'))

    open(os.path.join(self.temp_dir.name, 'bar.txt',), 'wb').close()

    # Just the dir
    with unittest.mock.patch.dict(os.environ, {'PATH': self.temp_dir.name}):
      self.assertIsNone(find_file_in_path('foo.txt'))
      self.assertEqual(find_file_in_path('bar.txt'),
          os.path.join(self.temp_dir.name, 'bar.txt'))

    # Multiple dirs
    with unittest.mock.patch.dict(os.environ, {'PATH':
        os.pathsep.join([
            os.path.join(self.temp_dir.name, '1'),
            os.path.join(self.temp_dir.name, '2'),
            self.temp_dir.name,
            os.path.join(self.temp_dir.name, '3')])}):
      self.assertEqual(find_file_in_path('bar.txt'),
          os.path.join(self.temp_dir.name, 'bar.txt'))

  def test_is_subdir(self):
    os.makedirs(os.path.join(self.temp_dir.name, 'a', 'b'))
    os.makedirs(os.path.join(self.temp_dir.name, 'c', 'd'))

    ans = is_subdir(os.path.join(self.temp_dir.name, 'a', 'b'),
                    self.temp_dir.name)
    self.assertTrue(ans[0])
    self.assertEqual(ans[1], os.path.join('a', 'b'))

    ans = is_subdir(os.path.join(self.temp_dir.name, 'a', '.', 'b'),
                    self.temp_dir.name)
    self.assertTrue(ans[0])
    self.assertEqual(ans[1], os.path.join('a', 'b'))

    ans = is_subdir(os.path.join(self.temp_dir.name, 'q', '..', 'a', 'b'),
                    self.temp_dir.name)
    self.assertTrue(ans[0])
    self.assertEqual(ans[1], os.path.join('a', 'b'))


    ans = is_subdir(os.path.join(self.temp_dir.name, 'a'),
                    self.temp_dir.name)
    self.assertTrue(ans[0])
    self.assertEqual(ans[1], 'a')

    ans = is_subdir(self.temp_dir.name,
                    self.temp_dir.name)
    self.assertTrue(ans[0])
    self.assertEqual(ans[1], ".")

    ans = is_subdir(self.temp_dir.name,
                    os.path.join(self.temp_dir.name, 'a'))
    self.assertFalse(ans[0])
    self.assertEqual(ans[1], "..")

    ans = is_subdir(os.path.join(self.temp_dir.name, 'a', 'b'),
                    os.path.join(self.temp_dir.name, 'c', 'd'))
    self.assertFalse(ans[0])
    self.assertEqual(ans[1], os.path.join('..', '..', 'a', 'b'))


    if os.name != 'nt':
      os.symlink(os.path.join(self.temp_dir.name, 'a', 'b'),
                 os.path.join(self.temp_dir.name, 'e'))

      ans = is_subdir(os.path.join(self.temp_dir.name, 'e'),
                      os.path.join(self.temp_dir.name, 'a'))
      self.assertTrue(ans[0])
      self.assertEqual(ans[1], 'b')

      ans = is_subdir(os.path.join(self.temp_dir.name, 'e'),
                      os.path.join(self.temp_dir.name, 'a'), False)
      self.assertFalse(ans[0])
      self.assertEqual(ans[1], os.path.join('..', 'e'))
