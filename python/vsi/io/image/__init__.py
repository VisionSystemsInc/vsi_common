from vsi.tools import Try
import numpy as np
import os

class RegisteredReaders(object):
  def __init__(self):
    self.readers = []
  def register(self, reader):
    if reader not in self.readers:
      self.readers.append(reader)
regsitered_readers=RegisteredReaders()

def imread(filename, *args, **kwargs):
  extension = os.path.splitext(filename)[1][1:]
  for reader in regsitered_readers.readers:
    if not reader.extensions or extension in reader.extensions:
      try:
        return reader(filename, autoload=True)
      except:
        pass
  return None


class Reader(object):
  def __init__(self, filename, autoload=False, *args, **kwargs):
    self.filename = filename
    if autoload:
      self.load(*args, **kwargs)
Reader.extensions = None #Default all

with Try(ImportError):
  import tifffile
  class TifffileReader(Reader):
    def load(self, **kwargs):
      self.object = tifffile.TiffFile(self.filename, **kwargs)
    def raster(self, page=0,**kwargs):
      return self.object.asarray(series=page, **kwargs)
    def shape(self, page=0):
      return tuple(self.object.series[0]['shape'])
    def dtype(self, page=0):
      return self.object.series[0]['dtype']
    def bpp(self, page=0):
      return self.dtype(page).itemsize*8

  TifffileReader.extensions=['tif', 'tiff']
  regsitered_readers.register(TifffileReader)


with Try(ImportError):
  from PIL import Image
  class PilReader(Reader):
    def load(self, mode='r'):
      self.object = Image.open(self.filename, mode)

    def raster(self):
      return np.array(self.object)

    def bpp(self):
      return self.object.bits

    def dtype(self):
      if self.object.bits == 8:
        pixel_format = np.int8
      if self.object.bits == 16:
        pixel_format = np.int16
      if self.object.bits == 32:
        if self.object.mode == "I":
          pixel_format = np.int32
        elif self.object.mode == "F":
          pixel_format = np.float32
    def shape(self):
      shape = self.object.size
      return (shape[1], shape[0])+shape[2:]
  regsitered_readers.register(PilReader)

with Try(ImportError):
  from osgeo import gdal
  class GdalReader(Reader):
    def load(self, mode=gdal.GA_ReadOnly, *args, **kwargs):
      self.object = gdal.Open(filename, mode, *args, **kwargs)

    def raster(self, band=1, *args, **kwargs):
      return self.object.GetRasterBand(band).ReadAsArray()

    def raster_roi(self, band=0, *args, **kwargs):
      '''This isn't written yet'''
      band = self.object.GetRasterBand(band)
      scanline = band.ReadRaster( 0, 0, band.XSize, 1, \
                                     band.XSize, 1, GDT_Float32 )      
      import struct
      tuple_of_floats = struct.unpack('f' * b2.XSize, scanline)
      #(use a numpy array instead of unpack)


    def get_object(self):
      return self.object;
  regsitered_readers.register(GdalReader)
