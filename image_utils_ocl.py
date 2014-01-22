""" A collection of GPGPU image processing utility functions """

import numpy as np
import pyopencl as cl
import skimage.transform
import os


def NCC_score_image(ocl_ctx, images_and_masks, window_radius):
    """ compute a sliding NCC score based on a set of images with masks """

    cl_queue = cl.CommandQueue(ocl_ctx)

    num_images = len(images_and_masks)
    img_dims = images_and_masks[0][0].size

    # create large buffers of concatentated images and masks
    image_stack = np.zeros((num_images*img_dims[1], img_dims[0]),np.float32)
    mask_stack = np.zeros((num_images*img_dims[1], img_dims[0]),np.uint8)
    for i in range(num_images):
        image_stack[i*img_dims[1]:(i+1)*img_dims[1],:] = np.array(images_and_masks[i][0]).astype(np.float32)
        mask_stack[i*img_dims[1]:(i+1)*img_dims[1],:] = np.array(images_and_masks[i][1]).astype(np.uint8)

    mf = cl.mem_flags
    image_buff = cl.Buffer(ocl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=image_stack)
    mask_buff = cl.Buffer(ocl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=mask_stack)

    score_img = np.zeros((img_dims[1], img_dims[0]),np.float32)
    output_buff = cl.Buffer(ocl_ctx, mf.WRITE_ONLY, score_img.nbytes)

    cl_dir = os.path.dirname(__file__)
    cl_filename = cl_dir + '/cl/NCC_score_multi.cl'
    with open(cl_filename, 'r') as fd:
        clstr = fd.read()

    prg = cl.Program(ocl_ctx, clstr).build()
    prg.NCC_score_multi(cl_queue, (img_dims[1], img_dims[0]), None,
                        image_buff, mask_buff, output_buff, np.int32(num_images),
                        np.int32(img_dims[0]), np.int32(img_dims[1]), np.int32(window_radius))

    cl.enqueue_copy(cl_queue, score_img, output_buff)
    cl_queue.finish()
    return score_img


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
    prg.sliding_ncc(cl_queue, img1_np.shape, None,
                    i1_buf, i2_buf, dest_buf,
                    np.int32(img1_np.shape[1]), np.int32(img1_np.shape[0]), np.int32(window_radius))

    ncc_img = np.zeros_like(img1_np)
    cl.enqueue_copy(cl_queue, ncc_img, dest_buf)
    cl_queue.finish()

    return ncc_img


def sliding_SSD(ocl_ctx, img1, img2, window_radius):
    """ perform sum of squared differences on a window centered around every pixel """

    cl_queue = cl.CommandQueue(ocl_ctx)

    img1_np = np.array(img1).astype(np.float32)
    img2_np = np.array(img2).astype(np.float32)

    mf = cl.mem_flags
    i1_buf = cl.Buffer(ocl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=img1_np)
    i2_buf = cl.Buffer(ocl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=img2_np)
    dest_buf = cl.Buffer(ocl_ctx, mf.WRITE_ONLY, img1_np.nbytes)

    cl_dir = os.path.dirname(__file__)
    cl_filename = cl_dir + '/cl/sliding_ssd.cl'
    with open(cl_filename, 'r') as fd:
        clstr = fd.read()

    prg = cl.Program(ocl_ctx, clstr).build()
    prg.sliding_ssd(cl_queue, img1_np.shape, None,
                    i1_buf, i2_buf, dest_buf,
                    np.int32(img1_np.shape[1]), np.int32(img1_np.shape[0]), np.int32(window_radius))

    ssd_img = np.zeros_like(img1_np)
    cl.enqueue_copy(cl_queue, ssd_img, dest_buf)
    cl_queue.finish()

    return ssd_img


def score_rectified_row(ocl_ctx, img1, img2, window_radius, row, method='NCC'):
    """ compute a matrix containing score for pairs i,j of column coordinates
        from corresponding rows in img1 and img2
        method should be one of {'NCC','SSD'}
        NCC: Normalized Cross Correlation of local patches
        SSD: Sum of Squared Difference of local patches
    """
    cl_queue = cl.CommandQueue(ocl_ctx)

    img1_np = np.array(img1).astype(np.float32)
    img2_np = np.array(img2).astype(np.float32)

    nrows = img1.shape[0]
    if img2.shape[0] != nrows:
        raise Exception('Expecting same number of rows in img1 and img2')

    mf = cl.mem_flags
    i1_buf = cl.Buffer(ocl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=img1_np)
    i2_buf = cl.Buffer(ocl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=img2_np)

    output_shape = (img1.shape[1], img2.shape[1])
    score_img = np.zeros(output_shape, np.float32)
    dest_buf = cl.Buffer(ocl_ctx, mf.WRITE_ONLY, score_img.nbytes)

    cl_dir = os.path.dirname(__file__)
    if method == 'NCC':
        cl_filename = cl_dir + '/cl/score_rectified_row_ncc.cl'
    elif method == 'SSD':
        cl_filename = cl_dir + '/cl/score_rectified_row_ssd.cl'
    else:
        raise Exception('Unrecognized method string ' + method)

    with open(cl_filename, 'r') as fd:
        clstr = fd.read()

    prg = cl.Program(ocl_ctx, clstr).build()
    prg.score_rectified_row(cl_queue, output_shape, None,
                            i1_buf, i2_buf, dest_buf,
                            np.int32(row), np.int32(nrows),
                            np.int32(img1_np.shape[1]), np.int32(img2_np.shape[1]),
                            np.int32(window_radius))

    cl.enqueue_copy(cl_queue, score_img, dest_buf)
    cl_queue.finish()

    return score_img


def compute_scale_image_ssd(ocl_ctx, img, thresh=0.2):
    """ compute local scale at each pixel in the image """
    num_levels = 6
    scale_img = np.zeros_like(img,dtype=np.uint8)
    levels = [lvl for lvl in skimage.transform.pyramid_gaussian(img, max_layer=num_levels, mode='nearest' )]
    num_levels = len(levels)
    for i in range(1,num_levels):
        lvl_img = skimage.transform.resize(levels[i],img.shape)
        diff_img = sliding_SSD(ocl_ctx, img, lvl_img, window_radius=2**i)
        prediction_good = diff_img < thresh
        scale_img[prediction_good] = i
    return scale_img


def compute_scale_image_entropy(ocl_ctx, img, entropy_thresh=100, num_bins=8):
    """ compute local scale at each pixel in the image entropy_thresh as units bits """
    num_levels = 7
    window_rads = [2**l for l in range(num_levels)]
    scale_img = np.zeros_like(img,dtype=np.uint8)
    scale_img[:] = num_levels
    ents = [local_entropy(ocl_ctx, img, wr, num_bins) for wr in window_rads]
    for i in reversed(range(num_levels)):
        good = ents[i] > entropy_thresh
        scale_img[good] = i
    return scale_img


def compute_scale_image_gradx(ocl_ctx, img, grad_sum_thresh=1.0):
    """ compute local scale at each pixel based on the absolute gradient (x component) """
    num_levels = 7
    window_radii = [2**l for l in range(num_levels)]
    scale_img = np.zeros_like(img,dtype=np.uint8)
    scale_img[:] = num_levels
    _, gx = np.gradient(img)
    gsums = [local_sum(ocl_ctx, np.abs(gx), wr) for wr in window_radii]
    for i in reversed(range(num_levels)):
        good = gsums[i] > grad_sum_thresh
        scale_img[good] = i
    return scale_img


def compute_scale_image(ocl_ctx, img, entropy_thresh=100, num_bins=8):
    """ compute local scale at each pixel in the image entropy_thresh as units bits """
    num_levels = 7
    window_rads = [2**l for l in range(num_levels)]
    scale_img = np.zeros_like(img,dtype=np.uint8)
    scale_img[:] = num_levels
    ents = [local_entropy(ocl_ctx, img, wr, num_bins) for wr in window_rads]
    for i in reversed(range(num_levels)):
        good = ents[i] > entropy_thresh
        scale_img[good] = i
    return scale_img


def local_sum(ocl_ctx, img, window_radius):
    """ compute the sum of all pixels in an encompassing window """
    mf = cl.mem_flags
    cl_queue = cl.CommandQueue(ocl_ctx)
    img_np = np.array(img).astype(np.float32)
    img_buf = cl.Buffer(ocl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=img_np)
    sum_img = np.zeros_like(img,dtype=np.float32)
    dest_buf = cl.Buffer(ocl_ctx, mf.WRITE_ONLY, sum_img.nbytes)
    cl_dir = os.path.dirname(__file__)
    cl_filename = cl_dir + '/cl/local_sum.cl'
    with open(cl_filename, 'r') as fd:
        clstr = fd.read()
    prg = cl.Program(ocl_ctx, clstr).build()
    prg.local_sum(cl_queue, sum_img.shape, None,
                  img_buf, dest_buf,
                  np.int32(img.shape[1]), np.int32(img.shape[0]),
                  np.int32(window_radius))

    cl.enqueue_copy(cl_queue, sum_img, dest_buf)
    cl_queue.finish()

    return sum_img


def local_entropy(ocl_ctx, img, window_radius, num_bins=8):
    """ compute local entropy using a sliding window """
    mf = cl.mem_flags
    cl_queue = cl.CommandQueue(ocl_ctx)
    img_np = np.array(img).astype(np.float32)
    img_buf = cl.Buffer(ocl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=img_np)
    min_val = np.nanmin(img)
    max_val = np.nanmax(img)
    entropy = np.zeros_like(img,dtype=np.float32)
    dest_buf = cl.Buffer(ocl_ctx, mf.WRITE_ONLY, entropy.nbytes)
    cl_dir = os.path.dirname(__file__)
    cl_filename = cl_dir + '/cl/local_entropy.cl'
    with open(cl_filename, 'r') as fd:
        clstr = fd.read()
    prg = cl.Program(ocl_ctx, clstr).build()
    prg.local_entropy(cl_queue, entropy.shape, None,
                      img_buf, dest_buf,
                      np.int32(img.shape[1]), np.int32(img.shape[0]),
                      np.int32(window_radius), np.int32(num_bins),
                      np.float32(min_val), np.float32(max_val))

    cl.enqueue_copy(cl_queue, entropy, dest_buf)
    cl_queue.finish()

    return entropy

