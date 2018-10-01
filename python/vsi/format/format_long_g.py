# approximate some of the functionality of matlab's 'format long g' command.
# not finished
import numpy as np
import vsi.console.terminal_info as ts

def repr_g(a):
  (precision, linewidth, edgeitems) = est_options(a)
  set_options(precision, linewidth, edgeitems)

  np.set_string_function(None, repr=True)
  str = a.__repr__()
  np.set_string_function(repr_g, repr=True)

  return str

def str_g(a):
  (precision, linewidth, edgeitems) = est_options(a)
  set_options(precision, linewidth, edgeitems)

  np.set_string_function(None, repr=False)
  str = a.__str__()
  np.set_string_function(str_g, repr=False)

  return str

def est_options(a):
  if a.dtype is np.dtype('float64'):
    precision = 15
  elif a.dtype is np.dtype('float32'):
    precision = 7
  else:
    precision = 7

  linewidth = ts.get_terminal_size()[0]

  edgeitems = int(np.floor(((linewidth-8)/(1+2+precision+1+2)) / 2.))

  return (precision, linewidth, edgeitems)

def set_options(precision, linewidth, edgeitems):
  # set the percision
  np.set_printoptions(precision=precision)
  # set the linewidth based on console width
  np.set_printoptions(linewidth=linewidth)
  # set the number of enteries to print based on console width and dtype
  np.set_printoptions(edgeitems=edgeitems)

np.set_string_function(repr_g, repr=True)
np.set_string_function(str_g, repr=False)

