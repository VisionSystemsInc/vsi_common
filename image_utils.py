""" A collection of utility functions related to Image data """
import numpy as np
import PIL.Image as Image
from itertools import izip


def rgb2gray(rgb):
    """ convert an rgb image stored as a numpy array to grayscale """
    gr = np.dot(rgb[..., :3], [0.299, 0.587, 0.144]).astype(rgb.dtype)
    return gr


def mutual_information(img1, img2, min_val, max_val, nbins):
    i1 = np.array(img1).ravel()
    i2 = np.array(img2).ravel()
    """ compute mutual information of img1 and img2 """
    counts = np.zeros((nbins,nbins))
    val_range = max_val - min_val
    # fill in counts
    for (v0,v1) in izip(i1,i2):
        b0 = int((v0 - min_val) / val_range * nbins)
        b1 = int((v1 - min_val) / val_range * nbins)
        counts[b0,b1] += 1
    total = float(len(i1))
    p0 = counts.sum(axis=0) / total
    p1 = counts.sum(axis=1) / total
    p01 = counts / total
    mi = 0
    for i in range(nbins):
        for j in range(nbins):
            if p01[i,j] == 0:
                continue
            if p0[i] == 0 or p1[j] == 0:
                raise Exception
            mi += p01[i,j] * np.log(p01[i,j] / (p0[i]*p1[j]))
    return mi / np.log(nbins)


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
    if any ([c[0] < 0 or c[0] >= image.size[0] or c[1] < 0 or c[1] >= image.size[1] for c in corners]):
        return None
    corner_verts = (corners[0][0], corners[0][1],
                    corners[1][0], corners[1][1],
                    corners[2][0], corners[2][1],
                    corners[3][0], corners[3][1])
    return image.transform(patch_size, Image.QUAD, corner_verts, Image.NEAREST)

