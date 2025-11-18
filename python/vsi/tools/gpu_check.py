import argparse
import ctypes
import glob
import logging
import os
import pathlib

logger = logging.getLogger(__name__)


def find_cudart(search_dirs):
  '''
  Find, load, and return the ``libcudart.so`` library.

  Paramters
  ---------
  search_dirs : :obj:`list`
    List of directories to search
  '''
  for search_dir in search_dirs:
    for file in pathlib.Path(search_dir).rglob('libcudart.so*'):
      try:
        return ctypes.cdll.LoadLibrary(file)
      except OSError:
        continue

  raise OSError("Failed to find & load libcudart.so")


def load_cudart(file=None):
  '''
  Load ``libcudart.so`` library.  If not provided as an input, search
  standard locations for the library.

  Paramters
  ---------
  file : :obj:`str`
    Location of ``libcudart.so``
  '''

  # load directly
  if file:
    return ctypes.cdll.LoadLibrary(file)

  # list of directories to search (via recursive glob)
  # - /usr/local/cuda*
  # - /usr/cuda*
  # - ${LD_LIBRARY_PATH}
  # - /usr
  search_dirs = list()

  search_dirs.extend(pathlib.Path('/usr/local').glob('cuda*'))
  search_dirs.extend(pathlib.Path('/usr').glob('cuda*'))

  LD_LIBRARY_PATH = os.getenv('LD_LIBRARY_PATH')
  if LD_LIBRARY_PATH:
    search_dirs.extend(LD_LIBRARY_PATH.split(os.pathsep))

  search_dirs.append('/usr')

  # ensure all search directories are pathlib
  search_dirs = [pathlib.Path(d) for d in search_dirs]

  # search for cudart
  return find_cudart(search_dirs)


def load_nvidia_uvm(file=None):
  '''
  A function to load the nvidia uvm device

  Some (older) Linux Operating systems do not load ``/dev/nvidia-uvm`` on boot
  to runlevel 3 (headless). This results in the ``nvidia-uvm`` module not being
  loaded.

  Unfortunately, a simple modprobe does not fix the issue, but a CUDA call on
  the host (not in a container) will.

  This scripts attempts to locate a ``libcudart.so`` library and calls the
  ``cudaGetDeviceCount`` function, which loads the ``/dev/nvidia-uvm`` driver.
  If it cannot locate the cuda runtime, you can give it the location as an
  argument.

  The CUDA Runtime is required on the host.
  '''

  # check file exists
  if file:
    file = pathlib.Path(file)
    if not file.is_file():
      raise OSError(f"File does not exist {file}")

  # load libcudart.so
  try:
    cudart = load_cudart(file)
  except OSError:
    if file:
      raise OSError(f"Failed to load cuda runtime from {file}")
    else:
      raise OSError("Failed to find & load cuda runtime. Try passing the "
                    "full path of cuda runtime as an argument.")

  # report
  logger.debug(f"found libcudart.so : {cudart._name}")

  # run cudaGetDeviceCount
  cudart.cudaGetDeviceCount.argtypes = (ctypes.POINTER(ctypes.c_int), )
  gpu_count = ctypes.c_int(-1)
  exit_code = cudart.cudaGetDeviceCount(ctypes.pointer(gpu_count))

  # report
  logger.debug(f"cudaGetDeviceCount : {exit_code=}, gpu_count={gpu_count.value}")


def gpu_check(file=None):
  '''Try to load nvidia-uvm if not already loaded'''

  # # Only bother checking if there are any nvidia cards present
  # if not glob.glob('/dev/nvidia[0-9]'):
  #   logger.debug('Skip gpu_check : /dev/nvidia[0-9] missing')
  #   return

  # is nvidia-uvm already loaded
  if os.path.exists('/dev/nvidia-uvm'):
    logger.debug('Skip gpu_check : /dev/nvidia-uvm already loaded')
    return

  # call load_nvidia_uvm
  try:
    load_nvidia_uvm(file)
  except OSError as err:
    logger.warning(f'load_nvidia_uvm failure : {err}')

  # nvidia-uvm report
  if os.path.exists('/dev/nvidia-uvm'):
    logger.debug("/dev/nvidia-uvm has been successfully loaded")
  else:
    logger.critical("load_nvidia_uvm ran but /dev/nvidia-uvm is still not loaded")


def main():
  '''
  Command line interface to :func:`gpu_check`
  '''

  # argument parser
  parser = argparse.ArgumentParser()
  parser.add_argument('--file', type=pathlib.Path,
                      default=None, required=False,
                      help="Path to libcudart.so")

  args = parser.parse_args()

  # basic logging when called from command line
  log_format = "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s : %(message)s"
  logging.basicConfig(level='DEBUG', format=log_format)

  # run gpu_check
  gpu_check(args.file)


if __name__ == '__main__':
  main()
