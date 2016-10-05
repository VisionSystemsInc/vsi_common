""" A collection of utility functions related to Image data """
import numpy as np
import PIL.Image as Image
from itertools import izip
import scipy.ndimage.filters
import skimage.transform


def sk_resize(img, nsize=None, nscale=None, **kwargs):
    """ make skimage.transform.resize() behave in a sane way
        nsize=[nr, nc] : resize each channel of img
    """

    assert nsize is not None or nscale is not None, 'either nsize or nscale must be set'
    if nsize is None:
        nrows, ncols = img.shape[0:2]
        nsize = round(nscale[0]*nrows), round(nscale[1]*ncols)

    # no need to resize
    # REVIEW maybe should return a copy since that is the normal behavior of
    # this function
    if (len(nsize) !=2) and (len(nsize) != len(img.shape)):
        raise Exception('Unexpected nsize ' + str(nsize))
    if np.all(np.array(img.shape[0:2]) == nsize): return img.copy()

    # resize() rescales pos integer images to between 0 and 1, however, it
    # clips neg values at 0
    in_type = img.dtype
    if issubclass(in_type.type, np.integer):
        # REVIEW dont always need to use double here...
        img = img.astype(dtype=np.double)  # copies array

    # resize() expects floating-point images to be scaled between 0 and 1
    # (otherwise it clips image!!). scale and rescale to prevent
    min_val = np.nanmin(img)
    max_val = np.nanmax(img) - min_val
    img = (img - min_val) / max_val
    # WARNING this is not equivilent to PIL.resize(), which at least downsamples
    # by selecting entire rows/cols when order=0 (nearest-neighbor interp)
    img_scaled = skimage.transform.resize(img, nsize, **kwargs)
    img_scaled = img_scaled * max_val + min_val

    if issubclass(in_type.type, np.integer):
        img_scaled = np.round(img_scaled)
        img_scaled = img_scaled.astype(dtype=in_type)  # will copy array

    return img_scaled


def rgb2gray(rgb):
    """ convert an rgb image stored as a numpy array to grayscale """
    gr = np.dot(rgb[..., :3].astype(np.float), [0.299, 0.587, 0.144])
    if rgb.dtype == np.uint8:
        gr[gr > 255] = 255
        gr[gr < 0] = 0
    return gr.astype(rgb.dtype)


def weighted_smooth(image, weights, pyramid_min_dim=50, convergence_thresh=0.01, max_its=1000):
    """ smooth the values in image using a multi-scale regularization.
        weights should be the same dimensions as image, with values in range (0,1)
    """
    # create image pyramids
    image_py = [Image.fromarray(image),]
    weight_py = [Image.fromarray(weights),]
    new_dims = (int(image_py[-1].size[0] / 2), int(image_py[-1].size[1] / 2))
    while np.min(new_dims) > pyramid_min_dim:
        image_level = image_py[-1].resize(new_dims, Image.BILINEAR)
        weight_level = weight_py[-1].resize(new_dims, Image.BILINEAR)
        image_py.append(image_level)
        weight_py.append(weight_level)
        new_dims = (int(image_py[-1].size[0] / 2), int(image_py[-1].size[1] / 2))
    num_levels = len(image_py)

    # initialize with top of pyramid
    image_smooth_prev = np.array(image_py[num_levels-1])
    # traverse all levels of pyramid
    num_its = 0
    for l in reversed(range(num_levels)):
        weights_np = np.array(weight_py[l])
        for i in range(max_its):
            num_its = i+1
            # smooth image
            image_smooth = scipy.ndimage.filters.gaussian_filter(image_smooth_prev, sigma=1.0, mode='nearest')
            # compute weighted sum of smoothed image and original
            image_smooth = weights_np*image_py[l] + (1.0 - weights_np)*image_smooth
            # test for convergence
            maxdiff = np.abs(image_smooth - image_smooth_prev).max()
            if maxdiff <= convergence_thresh:
                break
            image_smooth_prev = image_smooth
        print('level %d: %d iterations' % (l,num_its))
        # initialize next level with output from previous level
        if l > 0:
            image_smooth_prev_pil = Image.fromarray(image_smooth_prev)
            image_smooth_prev = np.array(image_smooth_prev_pil.resize(image_py[l-1].size))
    return image_smooth


def mutual_information(img1, img2, min_val, max_val, nbins):
    """ compute mutual information of img1 and img2 """
    i1 = np.array(img1).ravel().astype('float')
    i2 = np.array(img2).ravel().astype('float')
    val_range = max_val - min_val

    # fill in counts
    b1 = ((i1 - min_val) / val_range * nbins).astype('int')
    b2 = ((i2 - min_val) / val_range * nbins).astype('int')
    counts = np.zeros((nbins,nbins))
    for (v1,v2) in izip(b1,b2):
        counts[v1,v2] += 1
    total = float(len(i1))
    p0 = counts.sum(axis=0) / total
    p1 = counts.sum(axis=1) / total
    p01 = counts / total
    ind_prob = np.tile(p0.reshape(1,nbins),(nbins,1)) * np.tile(p1.reshape(nbins,1),(1,nbins))
    # avoid divide by zero
    zero_mask = (p01 == 0).astype('float')
    p01_clean = p01 + zero_mask
    ind_prob_clean = ind_prob + zero_mask
    mi_matrix = p01 * np.log(p01_clean / ind_prob_clean)
    return mi_matrix.sum() / np.log(nbins)


def normalized_cross_correlation(img1, img2):
    """ compute the normalized cross correlation of img1 and img2 """
    i1 = np.array(img1,'float').ravel()
    i2 = np.array(img2,'float').ravel()
    i1 -= i1.mean()
    norm1 = np.sqrt(np.sum(i1 * i1))
    if norm1 > 0:
        i1 /= norm1
    i2 -= i2.mean()
    norm2 = np.sqrt(np.sum(i2 * i2))
    if norm2 > 0:
        i2 /= norm2
    return np.dot(i1, i2)


def sample_point(image, pt):
    """ return the pixel value, or None if the point is outside image bounds """
    if pt[0] >= 0 and pt[0] < image.size[0] and pt[1] >= 0 and pt[1] < image.size[1]:
        return image.getpixel(tuple(pt))
    return None


def sample_patch(image, corners, patch_size, check_bounds=True):
    """ return an Image of size patch_size, or None if the patch is outside image bounds """
    if check_bounds:
        if any([c[0] < 0 or c[0] >= image.size[0] or c[1] < 0 or c[1] >= image.size[1] for c in corners]):
            return None
    corner_verts = (corners[0][0], corners[0][1],
                    corners[1][0], corners[1][1],
                    corners[2][0], corners[2][1],
                    corners[3][0], corners[3][1])
    # transform is counting on patch_size to be a tuple, not numpy array
    patch_size_tuple = (patch_size[0], patch_size[1])
    return image.transform(patch_size_tuple, Image.QUAD, corner_verts, Image.NEAREST)


def sample_plane_inverse(planar_patch, plane_origin, plane_x, plane_y, img_shape, camera):
    """ return the projection of a planar patch into the image
        planar_patch: The planar patch to project into the image (as a 2-d numpy array)
        plane_origin: 3-d point corresponding to the upper left of the patch
        plane_x: 3-d vector from origin to extent of patch in the "x" direction
        plane_y: 3-d vector from origin to extent of patch in the "y" direction: assumed perpendicular to plane_x
        img_shape: the dimensions (rows, cols) of the image to project into
        camera: a PinholeCamera
    """
    plane_xlen = np.linalg.norm(plane_x)
    plane_ylen = np.linalg.norm(plane_y)
    image2plane = camera.image2plane(plane_origin, plane_x, plane_y)
    plane2patch = np.array(((planar_patch.shape[1]/plane_xlen, 0, 0),(0, planar_patch.shape[0]/plane_ylen, 0),(0,0,1)))
    img2patch = np.dot(plane2patch, image2plane)

    return sample_patch_projective(planar_patch, img2patch, img_shape)


def sample_plane(image, camera, plane_origin, plane_x, plane_y, patch_shape):
    """ return a sampled patch based on the 3-d plane defined by plane_origin, plane_x, and plane_y
        plane_origin: 3-d point corresponding to the upper left of the patch
        plane_x: 3-d vector from origin to extent of patch in the "x" direction
        plane_y: 3-d vector from origin to extent of patch in the "y" direction: assumed perpendicular to plane_x
    """
    plane_xlen = np.linalg.norm(plane_x)
    plane_ylen = np.linalg.norm(plane_y)
    plane2image = camera.plane2image(plane_origin, plane_x, plane_y)

    patch2plane = np.array(((plane_xlen/patch_shape[1], 0, 0),(0, plane_ylen/patch_shape[0], 0),(0,0,1)))
    patch2img = np.dot(plane2image, patch2plane)

    return sample_patch_projective(image, patch2img, patch_shape)


def sample_patch_projective(image, inv_xform_3x3, patch_shape):
    """ return a warped image as a numpy array with dtype float64 of size patch_size.
        if input image is not already of type float64, it will be converted """
    P = skimage.transform.ProjectiveTransform(inv_xform_3x3)
    # skimage clips values to range [0,1] for floating point images.  do scale and unscale here.
    do_scale = False
    og_dtype = image.dtype
    if image.dtype in (np.float32, np.float64, np.float128, np.float16):
        minval = np.nanmin(image)
        maxval = np.nanmax(image)
        # if range is good, no need to rescale
        if minval < 0.0 or maxval > 1.0:
            do_scale = True
            # make a copy of image so as not to corrupt original data
            image = image.copy()
            scale_factor = maxval - minval
            image -= minval
            if scale_factor != 0:
                image /= scale_factor

    # do the warping
    patch = skimage.transform.warp(image, P, output_shape=patch_shape, mode='constant', cval=np.nan)

    # revert to original type if necessary
    if og_dtype != patch.dtype:
        if og_dtype == np.uint8:
            patch = skimage.img_as_ubyte(patch)
        elif og_dtype == np.bool:
            patch = skimage.img_as_bool(patch)
        elif og_dtype == np.uint16:
            patch = skimage.img_as_uint(patch)
        elif og_dtype == np.int16:
            patch = skimage.img_as_int(patch)
        else:
            # just to straight cast, hope for the best
            patch_out = np.zeros(patch.shape, og_dtype)
            np.copyto(patch_out,patch)
            patch = patch_out
    # unscale if necessary
    if do_scale:
        patch *= scale_factor
        patch += minval

    return patch


def sample_patch_perspective(image, inv_xform_3x3, patch_size):
    """ return an Image of size patch_size """
    patch_size_tuple = (patch_size[0], patch_size[1])
    inv_xform_array = inv_xform_3x3.reshape(9,) / inv_xform_3x3[2,2]
    patch = image.transform(patch_size_tuple, Image.PERSPECTIVE, inv_xform_array, Image.NEAREST)

    ones_img = Image.new('L', image.size, 255)
    mask = ones_img.transform(patch_size_tuple, Image.PERSPECTIVE, inv_xform_array, Image.NEAREST)
    return patch, mask

