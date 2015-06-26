import numpy as np
from collections import namedtuple
import skimage.measure
#import matplotlib.pyplot as plt
#import ipdb

# could maybe turn this into a generic mutable namedtuple
class Point2D(object):
    __slots__ = "x", "y"
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __iter__(self):
        '''iterate over fields tuple/list style'''
        for field_name in self.__slots__:
            yield getattr(self, field_name)
    def __getitem__(self, index):
        '''tuple/list style getitem'''
        return getattr(self, self.__slots__[index])

# NOTE IterateOverWindows and IterateOverSuperpixels must share the same iter() interface

# TODO create IterateOverOverlappingWindows(IterateOverWindows), which enforces
# pixel_stride <= pixels_per_cell
# 
# NOTE if pixel_stride > pixels_per_cell/2, it is possible to leave data unseen on the
# right/bottom boarder of an image
#
# this is similar to matlab's im2col
class IterateOverWindows(object):
    def __init__(self, pixels_per_cell, pixel_stride=None, image=None,
            mode='constant', cval=0,
            start_pt=(0, 0), stop_pt=(None, None)):
        ''' Sliding window iterator. 
        
        Parameters
        ----------
        pixels_per_cell: x,y - let x,y be odd so the window can be easily centered
        pixel_stride : x,y
        image : like numpy.array (ndim == 2 or 3)
        mode : Points outside the boundaries of the input are filled according
               to the given mode. Only ``mode='constant'``, ``mode='discard'`` and
               ``mode='reflect'`` are currently supported, although others could 
               be added (e.g., 'nearest' and 'wrap')
        cval : Value used for points outside the boundaries of the input if
               ``mode='constant'``. Default is 0.0
        start_pt : (x,y)
        stop_pt  : (x,y)

        >>> tot = 0; im = np.arange(100).reshape((10,10))
        >>> for i,ret in enumerate(IterateOverWindows((5,5),(2,2),cval=1).iter(im)):
        ...     tot += ret[0].sum()
        ...     #print i, ':\n', ret[0]
        >>> print tot # weak test
        22647

        >>> tot = 0; im = np.arange(81).reshape((9,9)).T
        >>> for i,ret in enumerate(IterateOverWindows((5,5),(2,2),mode='reflect').iter(im)):
        ...     tot += ret[0].sum()
        ...     #print i, ':\n', ret[0]
        >>> print tot # weak test
        25000
        '''

        assert pixels_per_cell[0] % 2 == 1 and pixels_per_cell[1] % 2 == 1, \
                'provide an odd number for pixels_per_cell so the window can be easily centered'
        self.pixels_per_cell = tuple(pixels_per_cell)
        self.pixel_stride = self.pixels_per_cell if pixel_stride is None else pixel_stride
        self.image = image
        self.mode = mode
        self.cval = cval
        self.start_pt = Point2D(*(int(s) for s in start_pt))
        self.stop_pt = Point2D(*(stop_pt))

    def setImage(self, image):
        '''
        Parameters
        ----------
        image : like numpy.array (ndim == 2 or 3)
        '''
        
        self.image = image
        return self

    def shape(self):
        if self.image is None: raise TypeError("self.image cannot be of type NoneType")

        nrows, ncols = self.image.shape[0:2]
        stop_x = ncols if self.stop_pt.x is None else int(self.stop_pt.x)
        stop_y = nrows if self.stop_pt.y is None else int(self.stop_pt.y)

        roi_height = stop_y-self.start_pt.y
        roi_width  = stop_x-self.start_pt.x
        #print roi_width, roi_height, self.pixel_stride

        nrows = np.ceil(float(roi_height)/self.pixel_stride[1]).astype(int)
        ncols = np.ceil(float(roi_width)/self.pixel_stride[0]).astype(int)

        return (nrows, ncols)

    def iter(self,image=None):
        '''Next window generator
        
        Parameters
        ----------
        image : like numpy.array (ndim == 2 or 3)

        Returns
        -------
        chip : pixels within the current window. Points outside the boundaries of the input
               are filled according to the given mode.
        mask : the binary mask of the window within the chip
        bbox : the inclusive extents of the chip (which may exceed the bounds of the image) 

        MODIFICATIONS
        sgr : turned into a class
        sgr : added mode='reflect'
        '''

        if image is not None: self.image = image
        elif self.image is None: raise TypeError("self.image cannot be of type NoneType")
        
        nrows, ncols = self.image.shape[0:2]

        # NOTE could iterate over the interior of the image without bounds checking
        # for additional speedup

        BoundingBox = namedtuple("BoundingBox", "min_x max_x min_y max_y")
        pixels_per_half_cell = self.pixels_per_cell[0]//2, self.pixels_per_cell[1]//2
        ystrides_per_image, xstrides_per_image = self.shape()
        # iterate around the boarder of the image
        for r in xrange(ystrides_per_image):
            for c in xrange(xstrides_per_image):
                # chip out pixels in this sliding window
                min_x = self.start_pt.x + self.pixel_stride[0]*c - pixels_per_half_cell[0]
                max_x = min_x+self.pixels_per_cell[0]
                min_y = self.start_pt.y + self.pixel_stride[1]*r - pixels_per_half_cell[1]
                max_y = min_y+self.pixels_per_cell[1]
                bbox = BoundingBox(min_x,max_x,min_y,max_y)
                min_x, max_x = max(0, bbox.min_x), min(ncols, bbox.max_x)
                min_y, max_y = max(0, bbox.min_y), min(nrows, bbox.max_y)
                #print 'c=%d'%c, 'r=%d'%r, min_x, max_x, min_y, max_y
                chip = self.image[min_y:max_y, min_x:max_x, ...]
                
                # couch chip in a fixed-size window
                # REVIEW I could refactor handling the boarder into pad_image(). then mode wouldn't 
                # be necessary here and I could simply loop over the image.
                # RE this is more efficient though
                if self.mode == 'constant' or self.mode == 'reflect':
                    chunk = np.empty(
                            self.pixels_per_cell + ((self.image.shape[2],) if self.image.ndim == 3 else ()),
                            dtype=self.image.dtype.type)
                    chunk[:] = self.cval
                    mask = np.zeros(self.pixels_per_cell)
                    
                    min_x = self.start_pt.x + self.pixel_stride[0]*c - pixels_per_half_cell[0]
                    max_x = min(self.pixels_per_cell[0], ncols - min_x)
                    min_x = max(0, -min_x)
                    min_y = self.start_pt.y + self.pixel_stride[1]*r - pixels_per_half_cell[1]
                    max_y = min(self.pixels_per_cell[1], nrows - min_y)
                    min_y = max(0, -min_y)
                    
                    #print 'c=%d'%c, 'r=%d'%r, min_x, max_x, min_y, max_y
                    #print
                    chunk[min_y:max_y, min_x:max_x, ...] = chip
                    mask[min_y:max_y, min_x:max_x] = 1

                    if self.mode == 'reflect':
                        nrows_chunk, ncols_chunk = chunk.shape[0:2]
                        # NOTE assume the points outside the boundaries of input can be filled from chip.
                        # this seems harder than it should be...
                        chunk[:min_y, min_x:max_x, ...] = np.flipud(np.atleast_2d(  # top border
                                chip[:min_y, :, ...]))
                        chunk[min_y:max_y, :min_x, ...] = np.fliplr(np.atleast_2d(  # left border
                                chip[:, :min_x, ...]))
                        # NOTE neg indice trikery (flipping first simplifies indexing)
                        chunk[max_y:, min_x:max_x, ...] = np.atleast_2d(            # bottom border
                                np.flipud(chip)[:nrows_chunk-max_y, :, ...])
                        chunk[min_y:max_y, max_x:, ...] = np.atleast_2d(            # right border
                                np.fliplr(chip)[:, :ncols_chunk-max_x, ...])
                        chunk[:min_y, :min_x, ...] = np.fliplr(np.flipud(np.atleast_2d( # top-left corner
                                chip[:min_y, :min_x, ...])))
                        chunk[:min_y, max_x:, ...] = np.flipud(np.atleast_2d(       # top-right corner
                                np.fliplr(chip)[:min_y, :ncols_chunk-max_x, ...]))
                        chunk[max_y:, max_x:, ...] = np.atleast_2d(                 # bottom-right corner
                                np.flipud(np.fliplr(chip))[:nrows_chunk-max_y, :ncols_chunk-max_x, ...])
                        chunk[max_y:, :min_x, ...] = np.fliplr(np.atleast_2d(       # bottom-left corner
                                np.flipud(chip)[:nrows_chunk-max_y, :min_x, ...]))
 
                elif self.mode == 'discard':
                    mask = np.ones_like(chip)
                    chunk = chip
                else: 
                    assert False, 'unrecognized mode'

                # FIXME should bbox be max-1 like in the superpixel version
                yield chunk, mask, bbox

class IterateOverSuperpixels(object):
    def __init__(self, segmented, image=None):
        '''
        Parameters
        ----------
        segmented : superpixel labeled segmentation (like numpy.array)
                    NOTE regionprops expects labels to be sequential and start
                    at 1: {1,2,...}. label 0 is treated as unlabeled.
        image : like numpy.array (ndim == 2 or 3)
        '''
        
        self.segmented = segmented
        self.image = image

    def setImage(self, image):
        '''
        Parameters
        ----------
        image : like numpy.array (ndim == 2 or 3)
        '''
        
        self.image = image
        return self

    def iter(self, image=None):
        '''Next superpixel generator
        
        Parameters
        ----------
        image : like numpy.array (ndim == 2 or 3)

        Returns
        -------
        chip : defined by the escribed bounding box of the segment. (view into image)
        mask : the binary mask of the segment within the chip
        bbox : the inclusive extents of the chip within the original image 

        MODIFICATIONS
        sgr : optimized
        sgr : turned into a class
        '''

        if image is not None: self.image = image
        elif self.image is None: raise TypeError("self.image cannot be of type NoneType")

        # regionprops() treats label zero (0) as unlabeled and ignores it
        # TODO remove small, unconnected components
        properties = skimage.measure.regionprops(self.segmented)
        BoundingBox = namedtuple("BoundingBox", "min_x max_x min_y max_y")
        for rp in properties:
            if rp._slice is None: continue
            
            (min_y,min_x,max_y,max_x) = rp.bbox
            chip = image[min_y:max_y, min_x:max_x,...]
            mask = rp.filled_image

            bbox = BoundingBox(min_x,max_x-1,min_y,max_y-1)
            
            yield (chip, mask, bbox)
