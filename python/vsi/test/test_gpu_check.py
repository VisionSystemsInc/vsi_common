import os
import unittest
from unittest.mock import patch, MagicMock

import vsi.tools.gpu_check


# dummy class to represent the loaded libcudart.so library
class MockLibrary:
  def __init__(self, file):
    self._name = file
    self.cudaGetDeviceCount = MagicMock(return_value="cudaGetDeviceCount")


# unit tests
class GpuCheckTest(unittest.TestCase):

  def _check_logs(self, logs, logs_expected):
    '''Check for expected logs'''

    # check length
    self.assertEqual(len(logs.output), len(logs_expected),
                     f'Logs are of different length\n{logs.output=}')

    # check that expected substring is in each log item
    for idx, (item, expected) in enumerate(zip(logs.output, logs_expected)):
      self.assertIn(expected, item,
                    f'Log mismatch line {idx}\n{logs.output=}')


  @patch('vsi.tools.gpu_check.pathlib.Path.rglob')
  @patch('vsi.tools.gpu_check.ctypes.cdll.LoadLibrary', side_effect=MockLibrary)
  def test_find_cudart(self, mock_LoadLibrary, mock_rglob):
    '''Test find_cudart'''

    # rglob return for 3 search_dirs
    search_dirs = ['/foo', '/bar', '/path/to']
    mock_rglob.side_effect = [list(), list(), ['/path/to/liubcudart.so']]

    # call function & check return
    result = vsi.tools.gpu_check.find_cudart(search_dirs)
    self.assertEqual(result._name, '/path/to/liubcudart.so')


  @patch('vsi.tools.gpu_check.pathlib.Path.rglob')
  def test_find_cudart_error(self, mock_rglob):
    '''Test find_cudart without discovering a file'''

    # rglob return for 1 search_dirs
    search_dirs = ['/foo']
    mock_rglob.side_effect = [list()]

    # raise OSError
    with self.assertRaises(OSError):
      _ = vsi.tools.gpu_check.find_cudart(search_dirs)


  @patch('vsi.tools.gpu_check.ctypes.cdll.LoadLibrary', side_effect=MockLibrary)
  def test_load_cudart_file(self, mock_LoadLibrary):
    '''Test load_cudart from file'''

    # call function & check return
    result = vsi.tools.gpu_check.load_cudart('/path/to/file')
    self.assertEqual(result._name, '/path/to/file')


  @patch.dict(os.environ, {"LD_LIBRARY_PATH": ""})
  @patch('vsi.tools.gpu_check.find_cudart')
  @patch('vsi.tools.gpu_check.pathlib.Path.glob')
  def test_load_cudart_dirs(self, mock_glob, mock_find_cudart):
    '''Test load_cudart from ``/usr/local/cuda``'''

    # glob result for ['/usr/local', '/usr']
    mock_glob.side_effect = [['/usr/local/cuda'], ['/usr/cuda']]

    # find_cudart result
    def _find_cudart(search_dirs):
      for search_dir in search_dirs:
        if '/usr/local/cuda' in str(search_dir):
          return MockLibrary('/usr/local/cuda/libcudart.so')
      raise None

    mock_find_cudart.side_effect = _find_cudart

    # call function & check return
    result = vsi.tools.gpu_check.load_cudart()
    self.assertEqual(result._name, '/usr/local/cuda/libcudart.so')


  @patch.dict(os.environ, {"LD_LIBRARY_PATH": "/foo:/bar:/path/to"})
  @patch('vsi.tools.gpu_check.find_cudart')
  @patch('vsi.tools.gpu_check.pathlib.Path.glob')
  def test_load_cudart_ld(self, mock_glob, mock_find_cudart):
    '''Test load_cudart from ``/usr/local/cuda``'''

    # glob result for ['/usr/local', '/usr']
    mock_glob.side_effect = [['/usr/local/cuda'], ['/usr/cuda']]

    # find_cudart result
    def _find_cudart(search_dirs):
      for search_dir in search_dirs:
        if '/path/to' in str(search_dir):
          return MockLibrary('/path/to/libcudart.so')
      raise None

    mock_find_cudart.side_effect = _find_cudart

    # call function & check return
    result = vsi.tools.gpu_check.load_cudart()
    self.assertEqual(result._name, '/path/to/libcudart.so')


  @patch('vsi.tools.gpu_check.load_cudart', return_value=MockLibrary('libcudart.so'))
  def test_load_nvidia_uvm(self, mock_load_cudart):
    '''Test load_nvidia_uvm'''

    # call function & check logs
    with self.assertLogs(level='DEBUG') as logs:
      vsi.tools.gpu_check.load_nvidia_uvm()

    logs_expected = [
      "found libcudart.so : libcudart.so",
      "cudaGetDeviceCount : exit_code='cudaGetDeviceCount', gpu_count=-1",
    ]
    self._check_logs(logs, logs_expected)


  @patch('vsi.tools.gpu_check.glob.glob', return_value=None)
  def test_gpu_check_no_gpu(self, mock_glob):
    '''Test gpu_check with nothing in /dev/nvidia[0-9]'''

    with self.assertLogs(level='DEBUG') as logs:
      vsi.tools.gpu_check.gpu_check()

    logs_expected = ["Skip gpu_check : /dev/nvidia[0-9] missing"]
    self._check_logs(logs, logs_expected)


  @patch('vsi.tools.gpu_check.glob.glob', return_value=True)
  @patch('vsi.tools.gpu_check.os.path.exists', return_value=True)
  def test_gpu_check_uvm_exists(self, mock_exists, mock_glob):
    '''Test gpu_check with existing /dev/nvidia-uvm'''

    with self.assertLogs(level='DEBUG') as logs:
      vsi.tools.gpu_check.gpu_check()

    logs_expected = ["Skip gpu_check : /dev/nvidia-uvm already loaded"]
    self._check_logs(logs, logs_expected)


  @patch('vsi.tools.gpu_check.glob.glob', return_value=True)
  @patch('vsi.tools.gpu_check.os.path.exists')
  @patch('vsi.tools.gpu_check.load_nvidia_uvm', return_value=MockLibrary('libcudart.so'))
  def test_gpu_check_uvm_success(self, mock_load_nvidia_uvm, mock_exists, mock_glob):
    '''Test gpu_check with load_nvidia_uvm success'''

    # /dev/nvidia-uvm check fails then succeeds
    mock_exists.side_effect = [False, True]

    # run test
    with self.assertLogs(level='DEBUG') as logs:
      vsi.tools.gpu_check.gpu_check()
    logs_expected = ["/dev/nvidia-uvm has been successfully loaded"]
    self._check_logs(logs, logs_expected)

