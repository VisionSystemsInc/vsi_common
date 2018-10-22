import numpy as np
# NOTE as_strided is undocumented and must be used with caution:
# https://github.com/numpy/numpy/blob/v1.11.1/numpy/lib/stride_tricks.py#L38
from numpy.lib.stride_tricks import as_strided

def sub_block(data, block=3, overlap=0, subok=False):
  ''' Return an array of windows into the original data array.

      data - N-dimensional array
      block - The block size of the final blocks. Should have length N or be a single number
      overlap - The amount of overlap between windows. A value of 0 has no overlap, while positive values overlap by that much, and negative values have gaps of that size.
      subok - Passed to as_strided

      Return Values:
      windows - N + N dimensional array where the first N dimensions are the window indexes, and the next N dimension are the data dimensions. Keep in mind, all the data is linked to the original data array. Changing values in one place changes them all.
      remainders - An N length list of the number of elements not included in the windows: the remainder of the sub-blocks. Another function could use these values to sub_block over them too. In the 2D case, there would be 3 groups of windows, in 3D case 6 groups of windows, etc...

      Usage Example:

      >> qq = np.arange(25).reshape(5,5)
      >> q,r = sub_block(qq, block=3, overlap=(2,1))
      >> q

      array([[[[ 0,  1,  2],
               [ 5,  6,  7],
               [10, 11, 12]],

              [[ 2,  3,  4],
               [ 7,  8,  9],
               [12, 13, 14]]],


             [[[ 5,  6,  7],
               [10, 11, 12],
               [15, 16, 17]],

              [[ 7,  8,  9],
               [12, 13, 14],
               [17, 18, 19]]],


             [[[10, 11, 12],
               [15, 16, 17],
               [20, 21, 22]],

              [[12, 13, 14],
               [17, 18, 19],
               [22, 23, 24]]]])

      REVIEW would be nice if this were a generator...
       '''

  try:
    iter(block)
  except:
    block = np.ones(len(data.shape), dtype=np.int)*block

  try:
    iter(overlap)
  except:
    overlap = np.ones(len(data.shape), dtype=np.int)*overlap

  block = tuple(block)
  overlap = tuple(overlap)

  assert(all(o < b for o,b in zip(overlap, block)))

  stride = [b-o for b,o in zip(block, overlap)]
  #A friend version of stride in units of index per index in a single dimension

  shape = tuple([(s-b)/(b-o)+1 for s,b,o in zip(data.shape, block, overlap)]) \
        + block
  strides = tuple([s*(b-o) for s,b,o in zip(data.strides, block, overlap)]) \
          + data.strides

  remainder = [ds - b - st * (sh - 1) for ds,b,st,sh in zip(data.shape, block,\
                                                            stride, shape)]

  return as_strided(data, shape=shape, strides=strides, subok=subok),remainder