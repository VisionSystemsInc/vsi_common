from boxm2_scene_adaptor import boxm2_scene_adaptor
import boxm2_adaptor
from glob import glob
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse

from vsi.io.krt import Krt
from vsi.tools.natural_sort import natural_sorted

from itertools import combinations
from mpl_toolkits.mplot3d.axes3d import Axes3D

class PlotScene(object):
  def __init__(self):
    self.figure = plt.figure()
    self.figure.clf()
    self.axes = self.figure.add_subplot(1, 1, 1, projection='3d')

  def set_limits(self, xmin, xmax, ymin, ymax, zmin, zmax):
    self.axes.set_xlim(xmin, xmax)
    self.axes.set_ylim(ymin, ymax)
    self.axes.set_zlim(zmin, zmax)

  def clear_plot(self):
    self.axes.clf()

  def draw_scene_box(self, scene):
    bbox = {k:v for (k,v) in zip(['x_min','y_min','z_min',
                                  'x_max','y_max','z_max'], 
            [x for y in scene.bbox for x in y])}
    self.draw_cube(**bbox)

  def draw_cameras(self, cameras, z_min=None, color='k'):
    camera_centers = np.array(map(lambda x:x.camera_center(), cameras))

    self.axes.hold('on')

    self.axes.plot(camera_centers[:,0], camera_centers[:,1], camera_centers[:,2], 'or')

    for camera in cameras:
      if z_min is not None:
        l = (z_min - camera.camera_center()[2])/camera.direction()[2]
      else:
        l = 100
      line = np.array([camera.camera_center(), camera.camera_center() + camera.direction()*l])
      self.axes.plot(line[:,0], line[:,1], line[:,2], color)

    self.axes.hold('off')

  def draw_cube(self, x_min, x_max, y_min, y_max, z_min, z_max):
    self.axes.hold('on')
    x_span = [x_min, x_max]
    x_min  = [x_min, x_min]
    x_max  = [x_max, x_max]
    y_span = [y_min, y_max]
    y_min  = [y_min, y_min]
    y_max  = [y_max, y_max]
    z_span = [z_min, z_max]
    z_min  = [z_min, z_min]
    z_max  = [z_max, z_max]

    plot = self.axes.plot

    plot(x_min, y_min, z_span, 'b')
    plot(x_min, y_max, z_span, 'b')
    plot(x_max, y_min, z_span, 'b')
    plot(x_max, y_max, z_span, 'b')

    plot(x_min, y_span, z_min, 'b')
    plot(x_min, y_span, z_max, 'b')
    plot(x_max, y_span, z_min, 'b')
    plot(x_max, y_span, z_max, 'b')

    plot(x_span, y_min, z_min, 'b')
    plot(x_span, y_min, z_max, 'b')
    plot(x_span, y_max, z_min, 'b')
    plot(x_span, y_max, z_max, 'b')
    self.axes.hold('off')

  def show(self):
    plt.show()


def parse_args():
  parser = argparse.ArgumentParser()
  aa = parser.add_argument
  aa('--scene', '-s', default=None, help="Scene file filename")
  aa('--cameras', '-c', default=None, nargs='+', 
     help='List of cameras to be plotted, can be camera filenames '
          'or glob expressions')
  aa('--diff', '-d', default=None, nargs='+', 
     help='List of cameras to be compared, can be camera filenames '
          'or glob expressions')
  aa('--limits', '-l', default=None, nargs=6, 
     help='Set axis manually, '
          'takes 6 arguments: xmin xmax ymin ymax zmin zmax')
 

  args = parser.parse_args()
  return args

def main():
  import matplotlib
  args = parse_args()

  plot_scene = PlotScene()

  if args.limits:
   xyz = [float(i) for i in args.limits]
   plot_scene.set_limits(xyz[0], xyz[1],\
                         xyz[2], xyz[3],\
                         xyz[4], xyz[5])

  z_min = None
  if args.scene:
    scene = boxm2_scene_adaptor(args.scene,  'cpp')
    plot_scene.draw_scene_box(scene)
    z_min = scene.bbox[0][2]

  if (args.limits and not z_min):
    z_min= xyz[4]

  if args.cameras:
    cameras = []
    camera_files = [x for y in map(lambda x: glob(x), args.cameras) for x in y]
    camera_files = natural_sorted(camera_files)
    for camera_file in camera_files:
      krt = Krt.load(camera_file)
      cameras.append(krt)
    plot_scene.draw_cameras(cameras, z_min)

  if args.cameras and args.diff:
    cameras = []
    camera_files = [x for y in map(lambda x: glob(x), args.diff) for x in y]
    camera_files = natural_sorted(camera_files)
    for camera_file in camera_files:
      krt = Krt.load(camera_file)
      cameras.append(krt)
    plot_scene.draw_cameras(cameras, z_min, 'g')

  plt.show()

if __name__=='__main__':
#  import vsi.tools.vdb as vdb; vdb.dbstop_if_error()
  main()