""" A collection of utility functions related to Image data """
import numpy as np
import PIL.Image as Image
from itertools import izip


def rgb2gray(rgb):
    """ convert an rgb image stored as a numpy array to grayscale """
    gr = np.dot(rgb[..., :3], [0.299, 0.587, 0.144]).astype(rgb.dtype)
    return gr


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


def sample_patch(image, corners, patch_size):
    """ return an Image of size patch_size, or None if the patch is outside image bounds """
    if any([c[0] < 0 or c[0] >= image.size[0] or c[1] < 0 or c[1] >= image.size[1] for c in corners]):
        return None
    corner_verts = (corners[0][0], corners[0][1],
                    corners[1][0], corners[1][1],
                    corners[2][0], corners[2][1],
                    corners[3][0], corners[3][1])
    return image.transform(patch_size, Image.QUAD, corner_verts, Image.NEAREST)

