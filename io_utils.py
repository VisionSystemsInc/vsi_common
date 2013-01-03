import string
import numpy as np
from PIL import Image
import os

def read_list(filename):
    try:
        fd = open(filename,'r')
    except IOError:
        print('Error opening file ' + filename)
        return []
    lines = []
    for line in fd:
        lines.append(line.strip())
    return lines

def write_list(thelist, filename):
    try:
        fd = open(filename,'w')
    except IOError:
        print('Error opening file ' + filename)
        return []
    for list_el in thelist:
        fd.write(str(list_el) + '\n')
    return

def read_vector_float(filename):
  lines = read_list(filename)
  for line in lines:
    elements_str = string.split(line)
    elements = []
    for s in elements_str:
      elements.append(float(s))
  vec = np.array(elements)
  return vec

def read_vectors_float(filename):
    lines = read_list(filename)
    vectors = []
    for line in lines:
        elements_str = string.split(line)
        elements = []
        for s in elements_str:
            elements.append(float(s))
        if (len(elements) > 0):
            vec = np.array(elements)
            vectors.append(vec)
    return vectors

def write_vectors_float(vector_list, filename):
    str_list = []
    for v in vector_list:
        v_str = ''
        for x in v:
           v_str = v_str + str(x) + ' '
        str_list.append(v_str)
    write_list(str_list,filename)
    return str_list
    
            
def imread(filename):
    img = Image.open(filename)
    # workaround for 16 bit images
    if img.mode == 'I;16':
        img.mode = 'I'
    return np.array(img)

def imwrite(img, filename):
    pilImg = Image.fromarray(img)
    if pilImg.mode == 'L':
      pilImg.convert('I') # convert to 32 bit signed mode 
    pilImg.save(filename)
    return

def imwrite_byte(img, vmin, vmax, filename):
    img_byte = np.uint8(np.zeros_like(img))
    img_norm = (img - vmin)/(vmax-vmin)
    img_norm = img_norm.clip(0.0,1.0)
    img_byte[:] = img_norm * 255
    imwrite(img_byte,filename)

# remove directory and extension from filename
def filename_base(filename):
    (path,filename_wext) = os.path.split(filename)
    (base,ext) = os.path.splitext(filename_wext)
    return base

def read_vector(vec_string):
  elements_str = vec_string.split()
  elements = []
  for s in elements_str:
    elements.append(float(s))
  vec = np.array(elements)
  return vec

def read_matrix(row_strings):
  rows = []
  for line in row_strings:
    elements_str = line.split()
    elements = []
    for s in elements_str:
      elements.append(float(s))
    if (len(elements) > 0):
      vec = np.array(elements)
      rows.append(vec)
  M = np.array(rows)
  return M

def read_camera_KRT(filename):
  lines = read_list(filename)
  # remove any empty lines
  lines = filter(None,lines)
  K = read_matrix(lines[0:3])
  R = read_matrix(lines[3:6])
  T = read_vector(lines[6])
  return K, R, T


 

