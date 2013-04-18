import matplotlib.pyplot as plt

def plot_box(x, y, width, height, *args, **kwargs):
  xvec = [x, x+width, x+width, x, x]
  yvec = [y, y, y+height, y+height, y]
  plt.plot(xvec,yvec, *args, **kwargs)

