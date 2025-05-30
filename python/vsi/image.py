import json
import math
import numpy as np
import numpy.typing as npt
import scipy.signal

from collections.abc import Iterable
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple, TypeVar, Union


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


def find_template_offset(template: np.floating, image: np.floating,
                         debug_dir: Optional[str]=None) \
                         -> Tuple[int, int, float]:
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
  debug_dir: :obj:`str`
    Optional directory to write debugging visualization images to.

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
  y_peak, x_peak = np.nonzero(xc == fit)

  # if there are duplicate peak values, take the first
  y_peak = y_peak[0]
  x_peak = x_peak[0]

  y_offset = y_peak - template.shape[0] + 1
  x_offset = x_peak - template.shape[1] + 1

  if debug_dir:
    visualize_cross_correlation(debug_dir, template, image, xc,
                                (y_peak, x_peak), fit, (y_offset, x_offset))

  return y_offset, x_offset, fit


def visualize_cross_correlation(debug_dir: str, template: np.floating,
                                image: np.floating, xc: np.floating,
                                peak: Tuple[int, int], peak_magnitude: float,
                                offset: Tuple[int, int]) -> None:
  """
  Save out visualization images to the provided debugging directory.

  Parameters
  ----------
  debug_dir: :obj:`str`
    Debugging directory to write visualization images to.
  template: :obj:`numpy.ndarray`
    N-D array of template or filter used for cross-correlation. Array should be
    floating point numbers between 0 and 1.
  image: :obj:`numpy.ndarray`
    Image array should be floating point numbers between 0 and 1.
  xc: :obj:`numpy.ndarray`
    The 2-D normalized cross correlation of the template and image.
  peak: :obj:`tuple`
    The (y, x) pixel coordinate of the peak of the correlation surface.
  peak_magnitude: :obj:`float`
    The scalar magnitude of the correlation peak.
  offset: :obj:`tuple`
    The (y, x) offset to translate the image by to match the image.

  Returns
  -------
  None
  """

  import matplotlib.pyplot as plt

  # file paths
  debug_dir = Path(debug_dir)
  template_image_file = debug_dir / 'template.png'
  image_file = debug_dir / 'image.png'
  xc_file = debug_dir / 'cross_correlation.png'
  cc_file = debug_dir / 'cross_correlation_data.json'

  # save out images
  plt.imsave(template_image_file, template, cmap='gray')
  plt.imsave(image_file, image, cmap='gray')
  plt.imsave(xc_file, xc)

  # convert numpy data types to primitives which are JSON serializable
  peak = [int(idx) for idx in peak]
  peak_magnitude = float(peak_magnitude)
  offset = [int(idx) for idx in offset]

  # save out JSON
  cc_data = {'peak': peak,
             'peak_magnitude': peak_magnitude,
             'offset': offset}
  with open(cc_file, 'w') as fp:
    json.dump(cc_data, fp, indent=2)


def find_template_offset_centered(template_image: np.floating,
                                  image: np.floating,
                                  template_center: Tuple[int, int],
                                  image_center: Tuple[int, int],
                                  template_radius: Union[int, Tuple[int,int]]=50,
                                  image_radius: Union[int, Tuple[int,int]]=200,
                                  adjust_template: Optional[Callable[[np.ndarray, int, int, int, int],
                                                                     Tuple[int, int, int, int]]]=None,
                                  debug_dir: Optional[str]=None):

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
  adjust_template: :obj:`Callable`
    Function to call to warp the template image before correlation.
  debug_dir: :obj:`str`
    Optional directory to write debugging visualization images to.


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

  def out_of_bounds(img, xmin, xmax, ymin, ymax):
    return (xmin < 0 or xmin > img.shape[1] or
            xmax < 0 or xmax > img.shape[1] or
            ymin < 0 or ymin > img.shape[0] or
            ymax < 0 or ymax > img.shape[0])

  if out_of_bounds(template_image, min_x1, max_x1, min_y1, max_y1):
    raise ValueError(f"Bounds ({min_y1}:{max_y1}, {min_x1}:{max_x1}) fall "
                     "outside of template image with shape "
                     f"{template_image.shape}")
  if out_of_bounds(image, min_x2, max_x2, min_y2, max_y2):
    raise ValueError(f"Bounds ({min_y2}:{max_y2}, {min_x2}:{max_x2}) fall "
                     f"outside of image with shape {image.shape}")

  offset_y, offset_x, fit = find_template_offset(
      template_image[min_y1:max_y1, min_x1:max_x1, ...],
      image[min_y2:max_y2, min_x2:max_x2, ...], debug_dir)

  offset_y = offset_y - image_center[0] + min_y2 - min_y1 + template_center[0]
  offset_x = offset_x - image_center[1] + min_x2 - min_x1 + template_center[1]

  return offset_y, offset_x, fit
