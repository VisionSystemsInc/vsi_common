from boxm2_scene_adaptor import boxm2_scene_adaptor
import boxm2_adaptor
from glob import glob
import numpy as np
import pylab
import os
import argparse

from vsi.io.krt import Krt
from vsi.tools.natural_sort import natural_sorted

from itertools import combinations
from mpl_toolkits.mplot3d.axes3d import Axes3D


def draw_cube(x_min, x_max, y_min, y_max, z_min, z_max):
  pylab.hold('on') 
  for combo in combinations('xyz', 2):
    other = tuple(set('xyz') - set(combo))[0]
    exec('%c0 = [%c_min, %c_min]' % ((combo[0],)*3))
    exec('%c1 = [%c_max, %c_max]' % ((combo[0],)*3))
    exec('%c2 = %c0' % ((combo[0],)*2))
    exec('%c3 = %c1' % ((combo[0],)*2))
    exec('%c0 = [%c_min, %c_min]' % ((combo[1],)*3))
    exec('%c2 = [%c_max, %c_max]' % ((combo[1],)*3))
    exec('%c1 = %c0' % ((combo[1],)*2))
    exec('%c3 = %c2' % ((combo[1],)*2))
    exec('%c0 = [%c_min, %c_max]' % ((other,)*3))
    exec('%c1 = %c0' % ((other,)*2))
    exec('%c2 = %c0' % ((other,)*2))
    exec('%c3 = %c0' % ((other,)*2))
    for x in range(4):
      eval("pylab.plot(x%d,y%d,z%d, 'b')" % ((x,)*3))
  pylab.hold('off')  

def plot_scene(scene, cameras):
  if scene is not None:
    bbox = {k:v for (k,v) in zip(['x_min','y_min','z_min',
                                  'x_max','y_max','z_max'], 
            [x for y in scene.bbox for x in y])}

  fig = pylab.plt.figure()
  pylab.clf()
  ax = fig.add_subplot(1, 1, 1, projection='3d')

  if scene is not None:
    draw_cube(**bbox)

  camera_centers = np.array(map(lambda x:x.camera_center(), cameras))

  pylab.hold('on')
  pylab.plot(camera_centers[:,0], camera_centers[:,1], camera_centers[:,2], 'or')

  for camera in cameras:
#    if scene is not None:
#      l = (bbox['z_min'] - camera.camera_center())/camera.direction()[2]
#    else:
    l = 1
    line = np.array([camera.camera_center(), camera.camera_center() + camera.direction()*l])
    pylab.plot(line[:,0], line[:,1], line[:,2], 'k')
  pylab.hold('off')

  return fig

def parse_args():
  parser = argparse.ArgumentParser()
  aa = parser.add_argument
  aa('--scene', '-s', default=None, help="Scene file filename")
  aa('--cameras', '-c', required=True, nargs='+', 
     help='List of cameras to be plotted, can be camera filenames '
          'or glob expressions')
  aa('--device', default='gpu0', 
     help='GPU or cpu and index for multi GPU set up. default is gpu0')
  args = parser.parse_args()
  return args

def main():
  import matplotlib
  args = parse_args()
  camera_files = [x for y in map(lambda x: glob(x), args.cameras) for x in y]
  camera_files = natural_sorted(camera_files)
  cameras = []
  for camera_file in camera_files:
    krt = Krt.load(camera_file)
    cameras.append(krt)
  
  scene = args.scene
  if scene is not None:
    scene = boxm2_scene_adaptor(scene,  args.device);

  fig = plot_scene(scene, cameras)
  pylab.show()

if __name__=='__main__':
#  import vsi.tools.vdb as vdb; vdb.dbstop_if_error()
  main()