import math
from typing import TypeVar, Union, Sequence, Tuple
from collections.abc import Iterable

import numpy as np
import numpy.typing as npt
import scipy.signal


# Annotation crap
T = TypeVar("T", bound=npt.NBitBase)


def normalized_cross_correlation_2d(template: "np.floating[T]",
                                    image: "np.floating[T]",
                                    mode: str="full"): # ->  "np.floating[T]":
  """
  Computes the 2-D normalized cross correlation (Aka: ``normxcorr2``) between
  the template and image.

  Parameters
  ----------
  template: :obj:`numpy.ndarray`
    N-D array of template or filter you are using for cross-correlation. Length
    of each dimension must be less than equal to the corresponding dimension of
    the image. Array should be floating point numbers.
  image: :obj:`numpy.ndarray`
    Image array should be floating point numbers.
  mode: :obj:`str`, optional
    * `full` (Default): The output of fftconvolve is the full discrete linear
      convolution of the inputs. Output size will be image size + 1/2 template
      size in each dimension.
    * `valid`: The output consists only of those elements that do not rely on
      the zero-padding.
    * `same`: The output is the same size as image, centered with respect to
      the "full" output.

  Returns
  -------
  :obj:`numpy.ndarray`
    N-D array of same dimensions as image. Size depends on mode parameter.
  """

  # If this happens, it is probably a mistake
  if np.ndim(template) > np.ndim(image):
    raise ValueError("Template has more dimensions than image. "
                     "Arguments probably need to be swapped.")
  if len([i for i in range(np.ndim(template))
                     if template.shape[i] > image.shape[i]]) > 0:
    raise ValueError("Template is larger than image. "
                     "Arguments probably need to be swapped.")

  template = template - np.mean(template)
  image = image - np.mean(image)

  a1 = np.ones(template.shape)
  # Faster to flip up down and left right then use convolve (fft domain)
  # instead of scipy's correlate in the space domain
  ar = np.flipud(np.fliplr(template))
  out = scipy.signal.fftconvolve(image, ar.conj(), mode=mode)

  image = scipy.signal.fftconvolve(np.square(image), a1, mode=mode) - \
          np.square(scipy.signal.fftconvolve(image, a1, mode=mode)) / \
          (np.prod(template.shape))

  # Remove small machine precision errors after subtraction
  image[np.where(image < 0)] = 0

  template = np.sum(np.square(template))
  out = out / np.sqrt(image * template)

  # Remove any divisions by 0 or very close to 0
  out[np.where(np.logical_not(np.isfinite(out)))] = 0

  return out


def find_template_offset(template: np.floating,
                         image: np.floating) -> Tuple[int, int, float]:
  """
  Uses 2-D normalized cross correlation to find the offset of the upper right
  corners of the template and image

  Parameters
  ----------
  template: :obj:`numpy.ndarray`
    N-D array of template or filter you are using for cross-correlation. Must
    be less or equal dimensions to image. Length of each dimension must be less
    than length of image. Array should be floating point numbers.
  image: :obj:`numpy.ndarray`
    Image array should be floating point numbers.

  Returns
  -------
  :obj:`int`
    y offset in pixels
  :obj:`int`
    x offset in pixels
  :obj:`float`
    The quality of the fit (scale of -1 to 1), where ``1`` is a perfect 100%
    match, and ``-1`` is a perfect negative match. ``0`` is no match
  """
  xc = normalized_cross_correlation_2d(template, image)

  fit = xc.max()
  y_peak, x_peak = np.nonzero(xc==fit)

  y_offset = y_peak[0]-template.shape[0]+1
  x_offset = x_peak[0]-template.shape[1]+1

  return y_offset, x_offset, fit


def find_template_offset_centered(template_image: np.floating,
                                  image: np.floating,
                                  template_center: Tuple[int, int],
                                  image_center: Tuple[int, int],
                                  template_radius: Union[int, Tuple[int,int]]=50,
                                  image_radius: Union[int, Tuple[int,int]]=200,
                                  adjust_template=None):

  """
  Uses 2-D normalized cross correlation to find the offset of a point of
  interest between in two images. This is a convenient form of the
  :func:`find_template_offset` function, that will handle boundary conditions
  and do the math to tell you the offset of specific point of interest at the
  centers

  Parameters
  ----------
  template_image: :obj:`numpy.ndarray`
    The image containing the template patch
  image: :obj:`numpy.ndarray`
    Image array should be floating point numbers.
  template_center: :obj:`tuple`
    The location of the POI in the template image, (y,x) coordinate
  image_center::obj:`tuple`
    The location of the POI in the image, (y,x) coordinate
  template_radius: :obj:`int` or :obj:`tuple`, optional
    The radius around the template used for the cross correlation. Can be a
    single number (in which case the same number is used in both the x and y
    direction), or a tuple of two numbers (y radius, x radius). E.g.: ``50``
    will create a patch 101 by 101, unless it is too close to the edge in which
    case it will be smaller. Default is ``50``, and must be smaller than
    image_radius.
  image_radius: :obj:`int` or :obj:`tuple`, optional
    The radius around the image. Default: ``200``


  Returns
  -------
  :obj:`int`
    y offset in pixels
  :obj:`int`
    x offset in pixels
  :obj:`float`
    The quality of the fit (scale of -1 to 1), where ``1`` is a perfect 100%
    match, and ``-1`` is a perfect negative match. ``0`` is no match
  """

  if not isinstance(template_radius, Iterable):
    template_radius = (template_radius, template_radius)
  if not isinstance(image_radius, Iterable):
    image_radius = (image_radius, image_radius)

  def get_bounds(image, center, radius):
    min_y = center[0] - radius[0]
    max_y = center[0] + radius[0]
    min_x = center[1] - radius[1] + 1
    max_x = center[1] + radius[1] + 1

    min_y = math.ceil(max(0, min_y))
    min_x = math.ceil(max(0, min_x))

    max_y = math.floor(min(image.shape[0], max_y))
    max_x = math.floor(min(image.shape[1], max_x))

    return min_y, max_y, min_x, max_x

  min_y1, max_y1, min_x1, max_x1 = get_bounds(template_image, template_center, template_radius)
  min_y2, max_y2, min_x2, max_x2 = get_bounds(image, image_center, image_radius)

  if adjust_template:
    adjustment = adjust_template(template_image, min_y1, max_y1, min_x1, max_x1)
    min_y1 += adjustment[0]
    max_y1 -= adjustment[1]
    min_x1 += adjustment[2]
    max_x1 -= adjustment[3]

  offset_y, offset_x, fit = find_template_offset(
      template_image[min_y1:max_y1, min_x1:max_x1, ...],
      image[min_y2:max_y2, min_x2:max_x2, ...])

  offset_y = offset_y - image_center[0] + min_y2 - min_y1 + template_center[0]
  offset_x = offset_x - image_center[1] + min_x2 - min_x1 + template_center[1]

  return offset_y, offset_x, fit
