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

def main(args=[]):
  cuda_runtimes=[]

  if args:
    cuda_runtimes=args
  else:
    # Attempt to discover cuda runtime
    common_dirs = glob('/usr/local/cuda*') + glob('/usr/cuda*') + ['/usr'] \
                  + [os.path.dirname(__file__)]

    for common_dir in common_dirs:
      for root, dirs, files in os.walk(common_dir, followlinks=False):
        cuda_runtimes.extend([os.path.join(root, rt) \
                            for rt in files \
                            if rt.startswith('libcudart.so')])
        if cuda_runtimes:
          break
      if cuda_runtimes:
        break

  if not cuda_runtimes:
    print("Could not find cuda runtime. "
          "Please pass the full path of a cuda runtime as an argument")
    exit(1)

  cudart = c.cdll.LoadLibrary(cuda_runtimes[0])
  cudart.cudaGetDeviceCount.argtypes = (c.POINTER(c.c_int),)

  gpu_count = c.c_int(-1)
  result = cudart.cudaGetDeviceCount(c.pointer(gpu_count))

  print("result", result)
  print("gpu_count", gpu_count.value)

if __name__ == '__main__':
  main(sys.argv[1:])