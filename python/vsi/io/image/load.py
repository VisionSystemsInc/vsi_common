
def imread_old(filename):
  from PIL import Image
  try:
    import tifffile
    has_tifffile = True
  except ImportError:
    has_tifffile = False

  """ read the image to a numpy array """
  _, ext = os.path.splitext(filename)
  if has_tifffile and (ext == '.tiff' or ext == '.tif'):
    # if image is tiff, use tifffile module
    img_np = tifffile.imread(filename)
  else:
    img = Image.open(filename)
    # workaround for 16 bit images
    if img.mode == 'I;16':
      img_np = np.array(img.getdata(), dtype=np.uint16).reshape(img.size[::-1])
    else:
      img_np = np.array(img)
  return img_np
