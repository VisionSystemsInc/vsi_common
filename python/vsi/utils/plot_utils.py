""" A set of utility functions related to plotting
"""
import matplotlib as mpl
import matplotlib.cm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
from PIL import Image


def imshow_with_colorbar(ax, *args, **kwargs):
  '''Display an image with properly sized colorbar

  Parameters
  ----------
  ax : matplotlib Axis
      The axis on which to draw the image and colorbar

  All remaining arguments (including the image) are passed on to ax.imshow()
  '''
  im = ax.imshow(*args, **kwargs)
  divider = make_axes_locatable(ax)
  cax = divider.append_axes("right", size="5%", pad=0.05)
  plt.colorbar(im, cax=cax)


def grouped_bar(features, bar_labels=None, group_labels=None, ax=None, colors=None):
  ''' features.shape like np.array([n_bars, n_groups])

  Parameters
  ----------
  features : numpy.array
      An array of the features


  Example::

  >>> bars = np.random.rand(5,3)
  >>> grouped_bar(bars)

  >>> group_labels = ['group%d' % i for i in range(bars.shape[1])]
  >>> bar_labels = ['bar%d' % i for i in range(bars.shape[0])]
  >>> grouped_bar(bars, group_labels=group_labels, bar_labels=bar_labels)

  '''

  n_bars, n_groups = features.shape[0:2]

  if ax is None:
    fig, ax = plt.subplots()
    fig.set_size_inches(9,6)
  else:
    fig = ax.get_figure()

  if colors is None:
    colors = mpl.cm.spectral(np.linspace(0, 1, n_bars))

  index = np.arange(n_groups)
  bar_width = 1.0/(n_bars) * 0.75

  for j,group in enumerate(features):
    label = bar_labels[j] if bar_labels is not None else None
    ax.bar(index + j*bar_width - bar_width*n_bars/2.0,
      group, bar_width, color=colors[j], label=label, alpha=0.4)
    ax.margins(0.05,0.0) # so the bar graph is nicely padded

  if bar_labels is not None:
    ax.legend(loc='upper left', bbox_to_anchor=(1.0,1.02), fontsize=14)

  if group_labels is not None:
    ax.set_xticks(index + (n_bars/2.)*bar_width - bar_width*n_bars/2.0)
    ax.set_xticklabels(group_labels, rotation=0.0)
    for item in (ax.get_xticklabels() + ax.get_yticklabels()):
      item.set_fontsize(14)

def groupedBar(*args, **kwargs):
  grouped_bar(*args, **kwargs)

def lblshow(label_img, labels_str=None, f=None, ax=None, cmap=None, *args, **kwargs):
  ''' display a labeled image with associated legend

  Parameters
  ----------
  label_img : array_like
      labeled image [nrows, ncols] = numpy.array.shape
  labels_str : list, optional
      a complete list of labels
  f : array_like, optional
      (optional) a figure handle
  cmap : array_like, optional
      the color of each label (optional). like a list of colors, e.g.,
      ['Red','Green',...] or a matplotlib.colors.ListedColormap)
  *args
      Variable length argument list.
  **kwargs
      Arbitrary keyword arguments.

  Returns
  -------
  array_like

  '''

  if labels_str is None:
    labels_str = [str(i) for i in np.unique(label_img)]

  if ax is None:
    if f is None:
      f,ax = plt.subplots(1,1)
      f.set_size_inches(9,6)
    else:
      ax = f.gca()
  elif f is None:
    f = ax.get_figure()


  nlabels = len(labels_str)
  if type(cmap) is mpl.colors.ListedColormap:
    pass
  elif hasattr(cmap, '__iter__'):
    if not kwargs.has_key('norm'):
      bounds = range(0,len(cmap)+1)
      kwargs['norm'] = mpl.colors.BoundaryNorm(bounds, len(cmap)) # HACKY
    cmap = mpl.colors.ListedColormap(cmap)
  elif cmap is None:
    colors = mpl.cm.spectral(np.linspace(0, 1, nlabels))
    cmap = mpl.colors.ListedColormap(colors)
  else:
    assert False, 'invalid color map'


  im = ax.imshow(label_img, cmap=cmap, *args, **kwargs); ax.axis('off')

  # create an axes on the right side of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.05 inch.
  divider = make_axes_locatable(ax)
  cax = divider.append_axes("right", size="5%", pad=0.05)
  cbar = plt.colorbar(im, cax=cax)

  cbar.ax.get_yaxis().set_ticks([])
  for j, lab in enumerate(labels_str):
    cbar.ax.text(1.3, float(2 * j + 1) / (nlabels*2), lab, ha='left', va='center')

  return f

def imshow(X, *args, **kwargs):
  """ modify the coordinate formatter to report the image "z"

  Parameters
  ----------
  X : array_like
  *args
      Variable length argument list.
  **kwargs
      Arbitrary keyword arguments.
  
  
  from http://matplotlib.org/examples/api/image_zcoord.html
  """

  _, ax = plt.subplots()
  ax.imshow(X, *args, **kwargs)

  numrows, numcols = X.shape[0:2]
  def format_coord(x, y):
    """ create string representation of x,y coords 
  
    Parameters
    ----------
    x : array_like
        The x coordinates
    y : array_like
        The y coordinates
  
    Returns
    -------
    str
        String representation of x,y coordinates
    """
    col = int(x+0.5)
    row = int(y+0.5)
    if col >= 0 and col < numcols and row >= 0 and row < numrows:
      z = X[row,col]
      return 'x=%1.4f, y=%1.4f, z=%s' % (x, y, repr(z.tolist()))
    else:
      return 'x=%1.4f, y=%1.4f' % (x, y)

  ax.format_coord = format_coord
  plt.show()

def plot_vector(x, axis, axis_order, *args, **kwargs):
  """ conveniance method for plotting 2 or 3-d data stored in numpy array """

  if len(x.shape) == 1:
    x = x.reshape((x.shape[0],1))

  if x.shape[0] == 2:
    axis.plot(x[axis_order[0],:], x[axis_order[1],:], *args, **kwargs)
  else:
    axis.plot(x[axis_order[0],:], x[axis_order[1],:], x[axis_order[2],:], *args, **kwargs)

def plot_rectangle(min_pt, max_pt, axis=None, *args, **kwargs):
  """ plot a 2-d box

  Parameters
  ----------
  min_pt : array_like
      The minimum point
  max_pt : array_like
      The maximum point
  *args
      Variable length argument list.
  **kwargs
      Arbitrary keyword arguments.
  """
  x,y = min_pt
  width, height = max_pt - min_pt
  xvec = [x, x+width, x+width, x, x]
  yvec = [y, y, y+height, y+height, y]
  if axis is None:
    axis = plt.gca()
  axis.plot(xvec, yvec, *args, **kwargs)

def plot_cube(x, y, z, width, height, depth, *args, **kwargs):
  """ plot a 3-d cube """
  # TODO
  pass

def plot_camera(cam, img_dims=(1280,720), axis=None, axis_order=(0,1,2), img_plane_depth=1.0):
  """ plot a 3-d representation of a perspective camera with image plane

  Parameters
  ----------
  cam :
  
  """
  if axis == None:
    axis = plt.gca()
  # plot camera center
  #axis.plot((cam.center[ao[0]],),(cam.center[ao[1]],),(cam.center[ao[2]],),'b.',markersize=10)
  plot_vector(cam.center, axis, axis_order, 'b.', markersize=10 )
  # compute backprojected corners of image plane
  img_corners = (np.array((0,0)), np.array((img_dims[0],0)),
           np.array((img_dims[0],img_dims[1])), np.array((0,img_dims[1])))
  corners_3d = cam.backproject_points(img_corners, [img_plane_depth,]*4)
  c3d_np = np.array(corners_3d).T
  c3d_np = np.hstack((c3d_np, c3d_np[:,0:1]))
  # plot the image plane
  #axis.plot(c3d_np[ao[0],:], c3d_np[ao[1],:], c3d_np[ao[2],:],'k-')
  plot_vector(c3d_np, axis, axis_order, 'k-')
  # plot connecting lines from the center to the image plane
  for x in corners_3d:
    plot_vector(np.array((cam.center, x)).T, axis, axis_order, 'k-')


class OrthoAnd3DPlot:
  """ 2x2 array of plots consisting of 3 ortho views, plus one 3-d view """
  def __init__(self, fig, aligned_x_dim=0, aligned_y_dim=2, dim_labels=('X','Y','Z')):
    self.fig = fig
    self.ax_array = np.array([[None,None],[None,None]])
    self.ax_array[0][0] = fig.add_subplot(2,2,1)
    self.ax_array[0][1] = fig.add_subplot(2,2,2)
    self.ax_array[1][0] = fig.add_subplot(2,2,3)
    self.ax_array[1][1] = fig.add_subplot(2,2,4,projection='3d')
    self.aligned_x_dim = aligned_x_dim
    self.aligned_y_dim = aligned_y_dim
    self.dim_labels = dim_labels
    # figure out the third axis
    aligned_dims = (aligned_x_dim, aligned_y_dim)
    self.extra_dim = 1
    if not 0 in aligned_dims:
      self.extra_dim = 0
    elif not 2 in aligned_dims:
      self.extra_dim = 2

    self.label_axes()

  def label_axes(self):
    """ label the axes using self.dim_labels """
    self.ax_array[0][0].set_xlabel(self.dim_labels[self.aligned_x_dim])
    self.ax_array[0][0].set_ylabel(self.dim_labels[self.aligned_y_dim])

    self.ax_array[0][1].set_xlabel(self.dim_labels[self.extra_dim])
    self.ax_array[0][1].set_ylabel(self.dim_labels[self.aligned_y_dim])

    self.ax_array[1][0].set_xlabel(self.dim_labels[self.aligned_x_dim])
    self.ax_array[1][0].set_ylabel(self.dim_labels[self.extra_dim])

    self.ax_array[1][1].set_xlabel(self.dim_labels[self.aligned_x_dim])
    self.ax_array[1][1].set_ylabel(self.dim_labels[self.extra_dim])
    self.ax_array[1][1].set_zlabel(self.dim_labels[self.aligned_y_dim])

  def set_axes_equal(self):
      """ set equal scale in the x and y dimensions on the 2D plots """
      self.ax_array[0][0].axis('equal')
      self.ax_array[0][1].axis('equal')
      self.ax_array[1][0].axis('equal')

  def plot(self, items, *args, **kwargs):
    """ add a set of 3-d elements to the plot.
  
    Parameters
    ----------
    items : array_like
    *args
        Variable length argument list.
    **kwargs
        Arbitrary keyword arguments.
    """

    if len(items.shape) == 1:
        items = items.reshape(-1,1)

    self.ax_array[0][0].plot(items[self.aligned_x_dim,:],
              items[self.aligned_y_dim,:], *args, **kwargs)

    self.ax_array[0][1].plot(items[self.extra_dim,:],
              items[self.aligned_y_dim,:], *args, **kwargs)

    self.ax_array[1][0].plot(items[self.aligned_x_dim,:],
              items[self.extra_dim,:], *args, **kwargs)

    self.ax_array[1][1].plot(items[self.aligned_x_dim,:],
              items[self.extra_dim,:],
              items[self.aligned_y_dim,:], *args, **kwargs)


  def setlim(self, dim, dmin, dmax):
    """ set the axis limits on all plots for the given data dimension

    Parameters
    ----------
    dim : array_like
        The given data dimension
    dmin : array_like
        The minimum data dimension
    dmax : array_like
        The maximum data dimension
    """
    if dim == self.aligned_x_dim:
      self.ax_array[0][0].set_xlim(dmin, dmax)
      self.ax_array[1][0].set_xlim(dmin, dmax)
      self.ax_array[1][1].set_xlim3d(dmin, dmax)
    elif dim == self.aligned_y_dim:
      self.ax_array[0][0].set_ylim(dmin, dmax)
      self.ax_array[0][1].set_ylim(dmin, dmax)
      self.ax_array[1][1].set_zlim3d(dmin, dmax)
    else:
      self.ax_array[0][1].set_xlim(dmin, dmax)
      self.ax_array[1][0].set_ylim(dmin, dmax)
      self.ax_array[1][1].set_ylim3d(dmin, dmax)


  def invert_axis(self, dim):
    """ invert the display of the given data dimension

    Parameters
    ----------
    dim : array_like
        The given data dimension
    """
    if dim == self.aligned_x_dim:
      self.ax_array[0][0].invert_xaxis()
      self.ax_array[1][0].invert_xaxis()
      self.ax_array[1][1].invert_xaxis()
    elif dim == self.aligned_y_dim:
      self.ax_array[0][0].invert_yaxis()
      self.ax_array[0][1].invert_yaxis()
      self.ax_array[1][1].invert_zaxis()
    else:
      self.ax_array[0][1].invert_xaxis()
      self.ax_array[1][0].invert_yaxis()
      self.ax_array[1][1].invert_yaxis()


def imshow_row(images,*args,**kwargs):
  """ imshow a set of images, arranged in a row

  Parameters
  ----------
  images : array_like
      A set of images
  *args
      Variable length argument list.
  **kwargs
      Arbitrary keyword arguments.

  Returns
  -------
  array_like
      The set of images, arranged in a row
  """
  nimages = len(images)
  fig,ax = plt.subplots(1,nimages)
  for (axi, imgi) in zip(ax,images):
    axi.imshow(imgi,*args,**kwargs)
  return fig,ax


def overlay_heatmap(image, heatmap, cmap='viridis', vmin=0, vmax=1, img_ratio=0.4):
  """ create a visualization of the image with overlaid heatmap

  Parameters
  ----------
  image : array_like
      The image
  heatmap :
      The heatmap
  
  Returns
  -------
  array_like
      The heatmap overlay
  
  Raises
  ------
  Exception
      If the image is not grayscale or rgb
  """
  img_gray = np.array(image)
  if len(img_gray.shape) == 3:
    if img_gray.shape[2] not in (3,4):
      raise Exception("Image should have 3 (RGB) or 4 (RGBA) planes")
    # convert to grayscale
    if 'float' in str(img_gray.dtype):
      # convert to RGB byte image, assuming range 0-1
      img_gray = np.clip(img_gray*255, 0, 255).astype(np.uint8)

    # use PIL to convert RGB to grayscale, convert back to numpy
    img_gray = np.array(Image.fromarray(img_gray).convert('L'))
    img_gray = img_gray.astype(np.float) / 255.0

  elif len(image.shape) != 2:
    raise Exception("Image should have 2 or 3 dimensions")

  heatmap_norm = (heatmap - vmin) / (vmax - vmin)
  cmap = mpl.cm.get_cmap(cmap)
  heatmap_vis = cmap(heatmap_norm)
  img_gray_3plane = np.repeat(img_gray.reshape(np.append(img_gray.shape, 1)), 3, axis=2)
  heatmap_overlay = (1.0 - img_ratio) * heatmap_vis[:,:,0:3] + img_ratio * img_gray_3plane
  mask = np.isnan(heatmap)
  heatmap_overlay[mask] = img_gray_3plane[mask]

  return heatmap_overlay


def make_random_colormap():
  """ return a random colormap (useful for segmentation displays)
  
      Returns
      -------
      array_like
          A random colormap
  """
  return mpl.colors.ListedColormap( np.random.rand(256,3))

