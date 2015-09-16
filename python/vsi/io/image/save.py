
def imwrite(img, filename):
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
