""" A collection of GPGPU image processing utility functions """
from PIL import Image
import numpy as np
import pyopencl as cl
import os


def sliding_NCC(ocl_ctx, img1, img2, window_radius):
    """ perform normalized cross-corellation on a window centered around every pixel """

    cl_queue = cl.CommandQueue(ocl_ctx)

    img1_np = np.array(img1).astype(np.float32)
    img2_np = np.array(img2).astype(np.float32)

    mf = cl.mem_flags
    i1_buf = cl.Buffer(ocl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=img1_np)
    i2_buf = cl.Buffer(ocl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=img2_np)
    dest_buf = cl.Buffer(ocl_ctx, mf.WRITE_ONLY, img1_np.nbytes)

    cl_dir = os.path.dirname(__file__)
    cl_filename = cl_dir + '/cl/sliding_ncc.cl'
    with open(cl_filename, 'r') as fd:
        clstr = fd.read()

    prg = cl.Program(ocl_ctx, clstr).build()
    print('calling kernel')
    print('img1_np.shape = ' + str(img1_np.shape))
    prg.sliding_ncc(cl_queue, img1_np.shape, None, 
                    i1_buf, i2_buf, dest_buf,
                    np.int32(img1_np.shape[1]), np.int32(img1_np.shape[0]), np.int32(window_radius))
    print('kernel returned')

    ncc_img = np.zeros_like(img1_np)
    cl.enqueue_copy(cl_queue, ncc_img, dest_buf)
    cl_queue.finish()

    return ncc_img

