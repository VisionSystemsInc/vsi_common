from vsi.tools import Try
import numpy as np
import os

class Register(object):
  def __init__(self):
    self.readers = []
  def register(self, reader):
    if reader not in self.readers:
      self.readers.append(reader)
registered_readers=Register()
registered_writers=Register()


# @@@ Generic classes @@@
class Reader(object):
  def __init__(self, filename, autoload=False, *args, **kwargs):
    self.filename = filename
    if autoload:
      self.load(*args, **kwargs)
Reader.extensions = None #Default all


class Writer(object):
  def __init__(self, array, dtype=None):
    if dtype:
      self.dtype = dtype
      self.array = np.asarray(array, self.dtype)
    else:
      self.array = array
      self.dtype = array.dtype

# @@@ tifffile classes @@@

with Try(ImportError):
  import tifffile

  class TifffileReader(Reader):
    #Assume series 0, this if for multiple files being treated as a series
    #Not currently considered
    def load(self, **kwargs):
      self.object = tifffile.TiffFile(self.filename, **kwargs)

    def raster(self, segment=0,**kwargs):
      return self.object.asarray(key=segment, **kwargs)

    def shape(self, segment=0):
      return tuple(self.object.pages[segment]['shape'])

    def dtype(self, segment=0):
      return self.object.series[0]['dtype']

    def bpp(self, segment=0):
      return self.dtype(segment).itemsize*8

    def band_names(self):
      raise Exception('Unimplemented. Used PilReader')

    def endian(self):
      return self.object.byteorder    

    def bands(self, segment=0):
      if len(self.object.pages[segment].shape)>2:
        return self.object.pages[segment].shape[2]
      else:
        return 1

    @property
    def segments(self):
      return len(self.object.pages)

  TifffileReader.extensions=['tif', 'tiff']
  registered_readers.register(TifffileReader)

  #Monkey patching to add JPEG compress TIFF support via PIL
  with Try(ImportError):
    from PIL import Image
    def decode_jpeg(encoded, tables=b'', photometric=None,
              ycbcr_subsampling=None, ycbcr_positioning=None):
      ''' ycbcr resampling is missing in both tifffile and PIL '''
      from StringIO import StringIO
      from PIL import JpegImagePlugin
      
      return JpegImagePlugin.JpegImageFile(StringIO(tables + encoded)).tobytes()
    tifffile.TIFF_DECOMPESSORS['jpeg'] = decode_jpeg
    tifffile.decodejpg = decode_jpeg

  class TifffileWriter(Writer):
    def save(self, filename, **kwargs):
      tifargs = {}
      for key in ('byteorder', 'bigtiff', 'software', 'writeshape'):
          if key in kwargs:
              tifargs[key] = kwargs[key]
              del kwargs[key]

      if 'writeshape' not in kwargs:
          kwargs['writeshape'] = True
      if 'bigtiff' not in tifargs and self.array.size*self.array.dtype.itemsize > 2000*2**20:
          tifargs['bigtiff'] = True

      self.object = tifffile.TiffWriter(filename, **tifargs)
      
      self.object.save(self.array, **kwargs)

  TifffileWriter.extensions=['tif', 'tiff']
  registered_writers.register(TifffileWriter)

# @@@ PIL classes @@@

with Try(ImportError):
  from PIL import Image

  class PilReader(Reader):
    def load(self, mode='r'):
      self.object = Image.open(self.filename, mode)

    def _get_mode_info(self, segment=0):
      ''' TODO: Cache this if it's being called a lot and slowing down'''
      self.object.seek(segment)
      mode = Image._MODE_CONV[self.object.mode]
      mode = {'endian':mode[0][0],
              'type':mode[0][1],
              'bpp':int(mode[0][2])*8,
              'bands':mode[1]}
      if mode['type'] == 'b':
        mode['bpp'] = 1
      if mode['bands'] is None:
        mode['bands'] = 1
      if mode['type'] == 'b':
        mode['type'] = np.bool
      elif mode['type'] == 'u':
        mode['type'] = getattr(np, 'uint%d' % mode['bpp'])
      elif mode['type'] == 'i':
        mode['type'] = getattr(np, 'int%d' % mode['bpp'])
      elif mode['type'] == 'f':
        mode['type'] = getattr(np, 'float%d' % mode['bpp'])
      else:
        raise Exception('Unknown mode type')
      return mode

    def endian(self, segment=0):
      return self._get_mode_info(segment)['endian']    

    def raster(self, segment=0):
      self.object.seek(segment)
      return np.array(self.object)

    def bpp(self, segment=0):
      self.object.seek(segment)
      return self._get_mode_info()['bpp']

    def dtype(self, segment=0):
      self.object.seek(segment)
      return self._get_mode_info()['type']

    def bands(self, segment=0):
      self.object.seek(segment)
      return self._get_mode_info()['bands']

    def band_names(self, segment=0):
      self.object.seek(segment)
      try:
        band_names = Image._MODEINFO[self.object.mode][2]
        if len(band_names) == 1:
          return ('P',)
        return band_names
      except KeyError:
        return ('P',) #Panchromatic
    

    def shape(self, segment=0):
      self.object.seek(segment)
      shape = self.object.size
      return (shape[1], shape[0])+shape[2:]
    
  registered_readers.register(PilReader)

  class PilWriter(Writer):
    def __init__(self, array, dtype=None, *args, **kwargs):
      super(PilWriter, self).__init__(array, dtype)
      self.object = Image.fromarray(self.array, *args, **kwargs)
    def save(self, filename, *args, **kwargs):
      self.object.save(filename, *args, **kwargs)
  registered_writers.register(PilWriter)

# @@@ GDAL classes @@@

with Try(ImportError):
  from osgeo import gdal
  class GdalReader(Reader):
    def __init__(self, *args, **kwargs):
      #default
      self._segment = 0

      super(GdalReader, self).__init__(*args, **kwargs)

    def _change_segment(self, segment=0, mode=gdal.GA_ReadOnly):
      if segment != self._segment:
        self._dataset = gdal.Open(self.object.GetSubDatasets()[segment][0], mode)
        self._segment = segment

    def load(self, mode=gdal.GA_ReadOnly, *args, **kwargs):
      self.object = gdal.Open(self.filename, mode, *args, **kwargs)
      self._dataset = self.object

    def raster(self, segment=0, *args, **kwargs):
      #return self.object.GetRasterBand(band).ReadAsArray()
      self._change_segment(segment)
      raster = self._dataset.ReadAsArray()
      if len(raster.shape)==3:
        return raster.transpose((1,2,0))
      else:
        return raster

    def raster_roi(self, segment=0, *args, **kwargs):
      '''This isn't written yet'''
      self._change_segment(segment)
      band = self.object.GetRasterBand(band)
      scanline = band.ReadRaster( 0, 0, band.XSize, 1, \
                                     band.XSize, 1, GDT_Float32 )      
      import struct
      tuple_of_floats = struct.unpack('f' * b2.XSize, scanline)
      #(use a numpy array instead of unpack)

    def bands(self, segment=0):
      self._change_segment(segment)
      return self._dataset.RasterCount

    def shape(self, segment=0):
      self._change_segment(segment)
      if self.object.RasterCount > 1:
        return (self.object.RasterYSize, self.object.RasterXSize, self.object.RasterCount)
      else:
        return (self.object.RasterYSize, self.object.RasterXSize)

    #def saveas(self, filename, strict=False): THIS IS CRAP
    #  ''' Copy the current object and save it to disk as a different file '''
    #
    #  destination = self.object.GetDriver().CreateCopy(filename, self.object, strict)

    #There is a LOT unimplemented here. I do NOT know GDAL enough to fill in the gaps

  registered_readers.register(GdalReader)

  from osgeo.gdal_array import codes as gdal_codes

  class GdalWriter(Writer):
    gdal_array_types = {v:k for k,v in gdal_codes.iteritems()}
    def save(self, filename, driver=None, *args, **kwargs):

      if driver is None:
        ext = os.path.splitext(filename)[1][1:]
        if ext.lower() in ['tif', 'tiff']:
          driver = gdal.GetDriverByName('GTiff')
        else:
          raise Exception('Unkown extension. Can not determine driver')
      
      bands = self.array.shape[2] if len(self.array.shape)>2 else 1

      self.object = driver.Create(filename, self.array.shape[1], 
          self.array.shape[0], bands, GdalWriter.gdal_array_types[self.dtype])

      if bands==1:
        self.object.GetRasterBand(1).WriteArray(self.array)
      else:
        for band in range(bands):
          self.object.GetRasterBand(band+1).WriteArray(self.array[:,:,band])

      #del self.object
      #Need to be deleted to actually save

      # dst_ds.SetGeoTransform( [ 444720, 30, 0, 3751320, 0, -30 ] )
      
      # srs = osr.SpatialReference()
      # srs.SetUTM( 11, 1 )
      # srs.SetWellKnownGeogCS( 'NAD27' )
      # dst_ds.SetProjection( srs.ExportToWkt() )



# @@@ Common feel functions @@@

def imread(filename, *args, **kwargs):
  extension = os.path.splitext(filename)[1][1:]
  for reader in registered_readers.readers:
    if not reader.extensions or extension in reader.extensions:
      try:
        return reader(filename, autoload=True)
      except:
        pass
  return None


def imwrite(img, filename, *args, **kwargs):
    """ write the numpy array as an image """
    _, ext = os.path.splitext(filename)
    is_multiplane = len(img.shape) > 2
    if has_tifffile and (ext == '.tiff' or ext == '.tif') and is_multiplane:
        # if image is tiff, use tifffile module
        tifffile.imsave(filename, img)
    else:
        pilImg = Image.fromarray(img)
        if pilImg.mode == 'L':
            pilImg.convert('I')  # convert to 32 bit signed mode
        pilImg.save(filename)
    return

def imwrite_byte(img, vmin, vmax, filename):
  """ write the 2-d numpy array as an image, scale to byte range first """
  img_byte = np.uint8(np.zeros_like(img))
  img_norm = (img - vmin)/(vmax-vmin)
  img_norm = img_norm.clip(0.0, 1.0)
  img_byte[:] = img_norm * 255
  imwrite(img_byte, filename)
