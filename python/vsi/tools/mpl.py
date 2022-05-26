
import math

try:
  import rasterio
except:
  pass

import numpy as np
import matplotlib as mpl
from matplotlib import pylab as plt


def share_xy_custom(ax1, ax2,
                    forward=lambda x: x, backward=lambda x: x,
                    sharex=True, sharey=True,
                    **kwargs):
  '''
  Like ``Axes.sharex``/``Axes.sharey`` only it allows you to provide your own
  function instead of the 1:1 default.

  Parameters
  ----------
  ax1 : :class:`matplotlib.axes.Axes`
      The first Axes
  ax2 : :class:`matplotlib.axes.Axes`
      The second Axes
  forward : Callable
      A function that takes the arguments ``x0``, ``x1``, ``y0``, ``y1`` for
      ``ax1`` and returns ``(x0, x1, y0, y1)`` for ``ax2``. Return ``None`` to
      indicate that no update to ``ax2`` should be performed.
  backward : Callable
      Same as ``forward`` except maps ``ax2`` to ``ax1``
  sharex : :class:`bool`, optional
      Should the x axis be shared
  sharey : :class:`bool`, optional
      Should the y axis be shared
  **kwargs
      Arbitrary keyword arguments passed to ``forward`` and ``backward``
  '''

  def wrap_call(func, ax, dest_ax):
    # Unpack the bbox
    x0 = ax.viewLim.x0
    x1 = ax.viewLim.x1
    y0 = ax.viewLim.y0
    y1 = ax.viewLim.y1

    # Call the user specified function
    bbox_new = func(x0, x1, y0, y1, **kwargs)

    # If it's not None or empty
    if bbox_new:
      # Unpack the bbox
      x0_new, x1_new, y0_new, y1_new = bbox_new

      # And set the lims
      if sharex:
        if x0 > x1: # Handle x flip
          dest_ax.set_xlim(max(x0_new, x1_new), min(x0_new, x1_new), emit=False)
        else:
          dest_ax.set_xlim(min(x0_new, x1_new), max(x0_new, x1_new), emit=False)

      if sharey:
        if y0 > y1: # Handle y flip
          dest_ax.set_ylim(max(y0_new, y1_new), min(y0_new, y1_new), emit=False)
        else:
          dest_ax.set_ylim(min(y0_new, y1_new), max(y0_new, y1_new), emit=False)

  _forward = lambda ax: wrap_call(forward, ax, ax2)
  _backward = lambda ax: wrap_call(backward, ax, ax1)

  # Set up event listeners
  if sharex:
    ax1.callbacks.connect('xlim_changed', _forward)
    ax2.callbacks.connect('xlim_changed', _backward)
  if sharey:
    ax1.callbacks.connect('ylim_changed', _forward)
    ax2.callbacks.connect('ylim_changed', _backward)


def imshow_chip(axes, img, origin, size, *args, **kwargs):
  '''
  imshow's only a chip of an image, and draws the chip at the appropriate
  coordinates.

  Does not support custom transforms

  Parameters
  ----------
  axes : :class:`matplotlib.axes.Axes`
      The first Axes
  img : :class:`numpy.ndarray`
      Image array
  origin : tuple
      The origin of the chip to load, in y, x, order
  size :
      The size of the chip to load, in y, x, order
  *args :
      Additional parameters passed to :func:`matplotlib.pyplot.imshow`
  **kwargs
      Additional parameters passed to :func:`matplotlib.pyplot.imshow`
  '''
  img_chip = img[origin[0]:(origin[0]+size[0]),
                 origin[1]:(origin[1]+size[1])]

  axes.imshow(img_chip,
              extent=(origin[1]-0.5,
                      origin[1]+img_chip.shape[1]-0.5,
                      origin[0]+img_chip.shape[0]-0.5,
                      origin[0]-0.5),
              *args, **kwargs)


def imshow_chip_from_raster(axes, raster, origin, size, *args, **kwargs):
  '''
  Loads and imshow's a chip of an image, and draws the chip at the
  appropriate coordinates.

  Does not support custom transforms

  Parameters
  ----------
  axes : :class:`matplotlib.axes.Axes`
      The first Axes
  raster : :class:`rasterio.io.DatasetReader`
      rasterio dataset object
  origin :
      The origin of the chip to load, in y, x, order
  size :
      The size of the chip to load, in y, x, order
  *args :
      Additional parameters passed to :func:`matplotlib.pyplot.imshow`
  **kwargs
      Additional parameters passed to :func:`matplotlib.pyplot.imshow`
  '''

  img_chip = raster.read(1,
      window=rasterio.windows.Window(origin[1], origin[0], size[1], size[0]))

  axes.imshow(img_chip,
              extent=(origin[1]-0.5,
                      origin[1]+img_chip.shape[1]-0.5,
                      origin[0]+img_chip.shape[0]-0.5,
                      origin[0]-0.5),
              *args, **kwargs)

def surf(z, cmap='jet', ax=None, x=None, y=None, c=None, **kwargs):
  '''
  Creates an equivalent "surf" plot, like in matlab

  Parameters
  ----------
  z : :class:`numpy.ndarray`
      The z data
  cmap :
      The colormap used to color based on z height. Default: jet
  ax : :class:`matplotlib.axes.Axes`
      The axes to draw on. Default: gca()
  x : :class:`numpy.ndarray`, optional
      The x coordinate used to draw. Default uses :func:`numpy.meshgrid`
  y : :class:`numpy.ndarray`, optional
      The y coordinate used to draw. Default uses :func:`numpy.meshgrid`
  c : :class:`numpy.ndarray`, optional
      A custom array that is fed into the colormap for coloring. Default uses
      ``z``
  **kwargs : dict
      Additional parameters passed to :meth:`mpl_toolkits.mplot3d.axes3d.Axes3D.plot_surface`


  By default, :meth:`mpl_toolkits.mplot3d.axes3d.Axes3D.plot_surface` does not
  draw the entire mesh, it downsamples it to 50 points instead (for
  efficiency). To disable downsampling, consider setting ``rstride`` and
  ``cstride`` to ``1``.

  Shading is also disabled by default
  '''
  if x is None and y is None:
    x, y = np.meshgrid(range(np.shape(z)[1]), range(np.shape(z)[0]))
  elif x is None:
    x, _ = np.meshgrid(range(np.shape(z)[1]), range(np.shape(z)[0]))
  elif y is None:
    _, y = np.meshgrid(range(np.shape(z)[1]), range(np.shape(z)[0]))

  if c is None:
    c = z

  kwargs['shade'] = kwargs.pop('shade', False)

  if ax is None:
    ax = plt.gca(projection='3d')

  scalarMap = mpl.cm.ScalarMappable(norm=plt.Normalize(vmin=c.min(), vmax=c.max()), cmap=cmap)

  # outputs an array where each C value is replaced with a corresponding color value
  c_colored = scalarMap.to_rgba(c)

  surf = ax.plot_surface(x, y, z, facecolors=c_colored, **kwargs)

  return surf


class SimpleBubblePicker:
  '''
  Simple class to add add a picker with your own text function

  Currently supports plots (Line2D), scatter (PathCollection), images
  (AxesImage) and PatchCollection

  With :class:`SimpleBubblePicker`, comes with a default text function that
  will display basic information about any point you click.
  '''
  def __init__(self, fig=None, text_function=None,
               x_offset=10, y_offset=15, offset_units='dots',
               bbox={'boxstyle': 'round', 'facecolor': 'wheat', 'alpha': 0.5},
               **kwargs):
    '''
    Initialize a :class:`SimpleBubblePicker` for a specific figure.

    Parameters
    ----------
        fig : :class:`matplotlib.figure.Figure`, optional
            Default to using the :func:`matplotlib.pyplot.gcf`
        text_function : :class:`py::function`, optional
            A Defaults to :func:`SimpleBubblePicker.default_text`
        x_offset : float, optional
        y_offset : float, optional
            Offset location of bubble from actual point
        offset_units : 'str', optional
            Default: ``dots``
        **kwargs :
            Additional argument to be passed to text initializer
    '''

    if fig is None:
      fig = plt.gcf()

    #: :class:`py::function`: The text generation function. Should take two
    # arguments
    self.text_function = text_function or SimpleBubblePicker.default_text

    #: float: The x offset of the currently drawing bubble
    self.x_offset = x_offset
    #: float: The y offset of the currently drawing bubble
    self.y_offset = y_offset
    #: str: The units of the offset for the current bubble offset
    self.offset_units = offset_units

    kwargs.setdefault('visible', False)
    kwargs.setdefault('x', 0)
    kwargs.setdefault('y', 0)
    kwargs.setdefault('s', 'Intentionally blank')
    kwargs['bbox'] = bbox

    self.bubble_kwarg = kwargs

    fig.canvas.mpl_connect('key_press_event', self.cleanup)
    fig.canvas.mpl_connect('pick_event', self._picker)

  def new_bubble(self, axes):

    # I don't know why I need to do this trasnform
    transform = mpl.transforms.offset_copy(axes.transData,
                                           axes.figure,
                                           x=self.x_offset,
                                           y=self.y_offset,
                                           units=self.offset_units)
    return axes.text(transform=transform, **self.bubble_kwarg)

  def get_bubbles(self, axes):
    try:
      return axes.simplebubblepicker_bubbles
    except AttributeError:
      axes.simplebubblepicker_bubbles = []
      return axes.simplebubblepicker_bubbles

  def get_bubble(self, axes, shift=False):
    bubbles = self.get_bubbles(axes)
    if len(bubbles) == 0:
      shift = True
    if shift:
      bubbles.append(self.new_bubble(axes))

    return bubbles[-1]

  def default_text(self, event):
    if isinstance(event.artist, (mpl.lines.Line2D,mpl.collections.PathCollection)):
      return '\n'.join([f'x: {self.x}',
                        f'y: {self.y}',
                        f'ind: {self.ind}'])
    elif isinstance(event.artist, mpl.image.AxesImage):
      return '\n'.join([f'x: {self.x}',
                        f'y: {self.y}',
                        f'data: {self.image[self.y, self.x, ...]}'])
    elif isinstance(event.artist, mpl.text.Text):
      return event.artist.get_text()
    elif isinstance(event.artist, mpl.collections.PatchCollection):
      return '\n'.join([f'patch: {self.patch}'])
    elif isinstance(event.artist, mpl.patches.Rectangle):
      return '\n'.join([f'x: {self.bbox.x0} - {self.bbox.x1}',
                        f'y: {self.bbox.y0} - {self.bbox.y1}'])
    else:
      return 'Todo'

  def cleanup(self, event):
    self.event2 = event
    if event.key == 'escape':
      bubbles = self.get_bubbles(event.inaxes)
      for bubble in bubbles:
        event.inaxes.texts.remove(bubble)
      bubbles.clear()

  def _picker(self, event):
    self.event = event # for debugging
    if isinstance(event, mpl.backend_bases.PickEvent) and \
       event.mouseevent.button == mpl.backend_bases.MouseButton.LEFT:
      if isinstance(event.artist, mpl.lines.Line2D):
        self.xdata = event.artist.get_xdata()
        self.ydata = event.artist.get_ydata()
        self.ind = event.ind
        # self.x = np.take(self.xdata, self.ind)[0]
        # self.y = np.take(self.ydata, self.ind)[0]
        self.x = self.xdata[self.ind[0]]
        self.y = self.ydata[self.ind[0]]

        self.text_x = self.x
        self.text_y = self.y
      elif isinstance(event.artist, mpl.image.AxesImage):
        self.image = event.artist.get_array()

        extent = event.artist.get_extent()
        x_scale = (extent[1]-extent[0]) / self.image.shape[1]
        y_scale = (extent[3]-extent[2]) / self.image.shape[0]

        if event.artist.origin == 'upper':
          y_scale = -y_scale

        if y_scale < 0:
          y_offset = max(extent[3], extent[2])
        else:
          y_offset = min(extent[3], extent[2])

        if x_scale < 0:
          x_offset = max(extent[1], extent[0])
        else:
          x_offset = min(extent[1], extent[0])

        self.x = math.floor((event.mouseevent.xdata-x_offset)/x_scale)
        self.y = math.floor((event.mouseevent.ydata-y_offset)/y_scale)

        self.text_x = (self.x + 0.5) * x_scale + x_offset
        self.text_y = (self.y + 0.5) * y_scale + y_offset

      elif isinstance(event.artist, mpl.collections.PathCollection): # scatter
        self.xdata = event.artist.get_offsets().data[:,0]
        self.ydata = event.artist.get_offsets().data[:,1]

        self.ind = event.ind
        self.x = self.xdata[self.ind[0]]
        self.y = self.ydata[self.ind[0]]

        self.text_x = self.x
        self.text_y = self.y
      elif isinstance(event.artist, mpl.collections.PatchCollection):
        self.ind = event.ind
        self.patches = event.artist.get_paths()
        self.patch = self.patches[self.ind[0]]
        self.text_x, self.text_y = self.patch.get_extents().corners().mean(axis=0)
      elif isinstance(event.artist, mpl.text.Text):
        self.x, self.y = event.artist.get_position()
        self.text_x = self.x
        self.text_y = self.y
      elif isinstance(event.artist, mpl.patches.Rectangle):
        self.bbox = event.artist.get_bbox()
        # self.x, self.y = event.artist.get_bbox()
        self.text_x = (self.bbox.x0 + self.bbox.x1)/2
        self.text_y = (self.bbox.y0 + self.bbox.y1)/2
      else:
        plt.gca().set_title('oops')
        return

      bubble = self.get_bubble(event.mouseevent.inaxes, event.mouseevent.key == "shift")
      bubble.set_visible(True)
      bubble.set_x(self.text_x)
      bubble.set_y(self.text_y)

      bubble.set_text(self.text_function(self, event))


def auto_fit_fontsize(text, width=None, height=None,
                      step_size=1, min_font_size=1, max_font_size=100):
  '''Auto-fit the fontsize of a text object.

  Args:
      text (matplotlib.text.Text)
      width (float): allowed width in data coordinates
      height (float): allowed height in data coordinates
  '''
# https://stackoverflow.com/a/61233097/4166604

  if min_font_size < 1:
    raise ValueError('The minimum font size cannot be less than 1.0')

  def fit(size):
    text.set_fontsize(size)
    renderer = text.axes.figure.canvas.get_renderer()
    bbox_text = text.get_window_extent(renderer=renderer)

    # transform bounding box to data coordinates
    bbox_text = mpl.transforms.Bbox(text.axes.transData.inverted().transform(bbox_text))

    fits_width = bbox_text.width - width if width else 0.0
    fits_height = bbox_text.height - height if height else 0.0
    # print(bbox_text.width, text.get_fontsize(), fits_width if abs(fits_width) > abs(fits_height) else fits_height)

    return fits_width if abs(fits_width) > abs(fits_height) else fits_height

  try:
    import scipy.optimize
    scipy.optimize.bisect(fit, a=min_font_size, b=max_font_size, xtol=step_size)
  # This happens when both min and max are positive which indicates no zero,
  # so the desires size is too small, so pick the min
  except ValueError:
    text.set_fontsize(min_font_size)
  except ImportError:
    # Brute force
    sz = max_font_size
    while sz > min_font_size and fit(sz) > 0:
      sz -= step_size
