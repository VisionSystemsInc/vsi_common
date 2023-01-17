#!/usr/bin/env python
'''
A script to load the nvidia uvm device

Some (older) Linux Operating systems do not load ``/dev/nvidia-uvm`` on boot to
runlevel 3 (headless). This results in the ``nvidia-uvm`` module not being
loaded.

Unfortunately, a simple modprobe does not fix the issue, but a CUDA call on the
host (not in a container) will.

This scripts attempts to locate a ``libcudart.so`` library and calls the
``cudaGetDeviceCount`` function, which loads the ``/dev/nvidia-uvm`` driver. If
it cannot locate the cuda runtime, you can give it the location as an argument.

The CUDA Runtime is required on the host.
'''

import ctypes as c
import os
from glob import glob
import sys

def find_cudart(search_dirs):
  cuda_runtimes=[]

  for search_dir in search_dirs:
    for root, dirs, files in os.walk(search_dir, followlinks=False):
      for cuda_runtime in [os.path.join(root, rt) \
                           for rt in files \
                           if rt.startswith('libcudart.so')]:
        try:
          return c.cdll.LoadLibrary(cuda_runtime)
        except OSError:
          continue

  return None

def main(args=[]):

  if args:
    cudart = c.cdll.LoadLibrary(args[0])
  else:
    # Attempt to discover cuda runtime
    common_dirs = glob('/usr/local/cuda*') + glob('/usr/cuda*') + ['/usr'] \
                  + [os.path.dirname(__file__)]
    if os.environ.get('LD_LIBRARY_PATH'):
      common_dirs += os.environ['LD_LIBRARY_PATH'].split(os.pathsep)
    cudart = find_cudart(common_dirs)

  if not cudart:
    print("Could not find cuda runtime. "
          "Please pass the full path of a cuda runtime as an argument")
    print("Try running:")
    print("  python " + __file__ + " path_to_libcudart.so")
    exit(1)

  cudart.cudaGetDeviceCount.argtypes = (c.POINTER(c.c_int),)

  gpu_count = c.c_int(-1)
  result = cudart.cudaGetDeviceCount(c.pointer(gpu_count))

  print("result", result)
  print("gpu_count", gpu_count.value)

if __name__ == '__main__':
  main(sys.argv[1:])
