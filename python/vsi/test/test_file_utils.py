import json
import glob
import os
from stat import S_IREAD
from tifffile import imwrite

from vsi.utils import file_utils
from vsi.test.utils import TestCase

sub_foo_dirs = {'tmp_subdir_0':['tmp_file0.txt','file1.txt','tmp_file2.txt'], 'tmp_subdir_1':['file0.txt','tmp_file1.txt'], 'tmp_sub_dir2':['tmp_file0.txt']}
foo_dirs = ['foo_file_dir', 'foo_f_dir']
foo_files = ['foo_file0.txt', 'foo_file1.txt', 'foo_file2.txt', 'foo_f0.txt','foo_f1.txt', 'f2.txt']
foo_pattern_files = ['foo_08_04_2023.txt', 'foo_08_04_23.txt']

class TestFileUtils(TestCase):

  def test_rmtree(self):
    # test remove tree with the ability to keep the top dir

    # write temp subdirectories to a temp directory
    foo_dir = self.temp_dir.name
    for key, value in sub_foo_dirs.items():
      sub_foo_dir = os.path.join(foo_dir,key)

      # Make the subdirectory
      os.makedirs(sub_foo_dir)

      # create some files in the subdirectory
      for f in value:
        foo_file = os.path.join(sub_foo_dir, f)
        # write to each file
        with open(foo_file,'w') as foo:
          foo.write('test')
        # create a read only file to test the ignore_errors variable
        if key == 'sub_dir2':
          os.chmod(foo_file, S_IREAD)

    # Check that the temp directory exists.
    if not os.path.isdir(foo_dir):
      raise ValueError (
        '{} does not exist! It is a temporary directory that is deleted once it is out of scope.'
        .format(foo_dir))
    else:
      # remove directory recursively but keep the top dir
      file_utils.rmtree(foo_dir, ignore_errors=False, rmdir=False)
      if not os.path.isdir(foo_dir):
        raise ValueError ('{} should still exist since rmdir is False.'.format(foo_dir))
      # now remove the top dir
      else:
        file_utils.rmtree(foo_dir)
      # This directory should no longer exist.
      if os.path.isdir(foo_dir):
        raise ValueError ('{} should no longer exist.'.format(foo_dir))


  def test_get_files_with_extension_from_dir(self):
    # tests finding files with the specified extension(s)

    # first create a temp directory
    foo_dir = self.temp_dir.name

    with self.subTest("Verify no files are found"):
      # temp files
      foo_files = []
      # an empty list is returned if no files with the given extension exist.
      extensions = ['tif', 'tiff']
      files = file_utils.get_files_with_extension_from_dir(foo_dir, extensions)
      self.assertEqual(files, foo_files)

    with self.subTest("Verify text files are found"):
      for key, value in sub_foo_dirs.items():
        sub_foo_dir = os.path.join(foo_dir,key)

        # Make the subdirectory
        os.makedirs(sub_foo_dir)
        # create some files in the subdirectory
        for f in value:
          foo_file = os.path.join(sub_foo_dir, f)
          # write to each file
          with open(foo_file,'w') as foo:
            foo.write('test')
          foo_files.append(foo_file)

      # sort the list of foo files
      foo_files.sort()
      # test finding the files with the specified extension(s)
      extensions = ['txt']
      files = file_utils.get_files_with_extension_from_dir(foo_dir, extensions)
      # sort the list of expected files
      files.sort()
      self.assertEqual(files, foo_files)


  def test_get_neighbor_files_with_extension(self):

    # tests finding files in the same directory,
    # with the same name, but have different extensions
    # first create a subdirectory
    foo_dir = self.temp_dir.name

    # create some foo files with the same name, but different extensions
    # a text file
    foo_text_file = os.path.join(foo_dir, 'temp1.txt')
    with open(foo_text_file, 'w') as foo:
      foo.write('test')

    # an image file
    foo_image_file = os.path.join(foo_dir, 'temp1.tif')
    open(foo_image_file, 'w').close()

    # a json file
    foo_json_file = os.path.join(foo_dir, 'temp1.json')
    foo_dict = {1: 'test'}
    with open(foo_json_file, 'w') as fp:
      json.dump(foo_dict, fp)

    # test for image neighbors of json file
    with self.subTest("Verify image neighbor is found"):
      src_file = foo_json_file
      image_extensions = ('tif', 'tiff')
      support_files = file_utils.get_neighbor_files_with_extension(src_file, image_extensions)
      expected_file = [foo_image_file]
      self.assertEqual(support_files, expected_file)

    # test for text file neighbors of json file
    with self.subTest("Verify text neighbor is found"):
      text_extension = ('txt',)
      support_files = file_utils.get_neighbor_files_with_extension(src_file, text_extension)
      expected_file = [foo_text_file]
      self.assertEqual(support_files, expected_file)

    # test for meta data neighbors of the image file
    # since there are no meta data files, this is expected to return an empty list
    with self.subTest("Verify no metadata neighbor is found"):
      src_file = foo_image_file
      meta_extensions = ('imd', 'pvl')
      support_files = file_utils.get_neighbor_files_with_extension(src_file, meta_extensions)
      self.assertEqual(support_files, [])
