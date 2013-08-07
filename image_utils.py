""" A collection of utility functions related to Image data """
import numpy as np


def rgb2gray(rgb):
    """ convert an rgb image to grayscale """
    gr = np.dot(rgb[..., :3], [0.299, 0.587, 0.144])
    return gr


