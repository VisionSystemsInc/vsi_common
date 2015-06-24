'''
@created: Nov, 2014
@author: srichardson
Script to generate a scene file given corner coordinates (lat, lon, height), 
GSD, and number of refinements. This will generate a scene with blocks that 
will, in the wrost case, fit within the identified GPU's memory.

terminology:
a world is composed of blocks
blocks are used to cope with limited GPU memory
blocks are composed of sub-blocks
a sub-block has an octree
an octree can be refined three times
the leaf cells of a sub-block are voxels

Due to a windows stdout redirect bug, if calling from CLI, you must redirect
stdout. python ... > nil will do
'''

import sys,os
import re
from subprocess import Popen, PIPE
import math

from .generate_scene_xml import generate_scene_xml
import vpgl_adaptor
from boxm2_adaptor import create_scene_and_blocks, ocl_info
from StringIO import StringIO

import argparse

from vsi.tools import Redirect

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('output_file', nargs='?', type=argparse.FileType('w'), 
      default=sys.stdout,
      help="Filename to write scene.xml to. Default is stdout")
  parser.add_argument('-a', '--appearance', nargs='+', 
      default=('boxm2_mog3_grey','boxm2_num_obs'),
      help="""List of appearance models to use. Default is boxm2_mog3_grey and
              boxm2_num_obs""")
  parser.add_argument('-b', '--bins', default=1, type=int, 
     help='Number of illumination bins')
  parser.add_argument('-m', '--modeldir', default='.', help='Model directory')
  parser.add_argument('-d', '--device', default='gpu0', 
      help='OpenCL Device to process on')
  parser.add_argument('-r', '--refine', default=3, choices=range(4), type=int, 
      help="""Promise: a scene will be refined at most [0,3] times is fully 
              refined after three subdivisions, although, because a cell must 
              pass a certain threshold to be eligible for subdivision,
              additional passes may continue to refine the scene """)
  parser.add_argument('-s', '--gsd', default=1.0, type=float, 
      help="""GSD in meters of a voxel (leaf cell in the octree) in a fully 
              refined world""")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('--lla1', nargs=3, type=float, default=None,
      help="""Longitude, Latitude, and Altitude in degrees and meters of the 
              west,south,floor corner of the world. Note: NOT Latitude, 
              Longitude order""")
  group.add_argument('--lvcs1', nargs=3, type=float, default=None,
      help="""X Y Z in arbitrary units of the west,south,floor corner of the
              world""")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('--lla2', nargs=3, type=float, default=None,
      help="""Longitude, Latitude, and Altitude in degrees and meters of the
              east,north,ceiling corner of the world. Note: NOT Latitude, 
              Longitude order""")
  group.add_argument('--lvcs2', nargs=3, type=float, default=None,
      help="""X Y Z in arbitrary units of the east,north,ceiling corner of the
              world""")
  parser.add_argument('-o', '--origin', nargs=3, type=float, default=None, 
      help="""Optional origin for scene file, default is to use lla Longitude, 
              Latitude, and Altitude in degrees and meters  of the 
              east,north,ceiling corner of the world. Note: NOT Latitude, 
              Longitude order""")
  args = parser.parse_args()
  
  #Force all output to stderr so that if the output_file is stdout, it's clean
  #with Redirect(all=sys.stderr):
  create_scene_xml(args.device, args.refine, args.gsd, lla1=args.lla1, 
                     lla2=args.lla2, lvcs1=args.lvcs1, lvcs2=args.lvcs2,
                     origin=args.origin, output_file=args.output_file, 
                     model_dir=args.modeldir,
                     appearance_models=args.appearance, number_bins=args.bins)

# INTERNAL ---------
def gpu_memory(gpu_device):
  stdout = StringIO()
  with Redirect(stdout_c=stdout):
    ocl_info()
    import time; time.sleep(1)
  stdout.seek(0,0)
  stdout = stdout.read()

  # cpu devices are possible, but don't look for them
  gpu_id_re = re.compile('gpu(\d\d?)')
  # cpu devices are possible, but don't look for them
  device_id_re = re.compile('gpu(\d\d?),  Device Description:')
  device_name_re = re.compile(' Device Name : (.+)')
  global_memory_re = re.compile('\s*Total global memory: (\S+) ([GM]Bytes)')

  match = gpu_id_re.match(gpu_device)
  if match:
    gpu_id = int(match.group(1))
  else:
    assert False, 'unrecognized gpu_device: %s'%str(gpu_device)

  it = iter(stdout.split('\n'))
  for line in it:
    match = device_id_re.match(line)
    if match:
      device_id = int(match.group(1))
      if device_id == gpu_id:
        for line in it:
          match = device_name_re.match(line)
          if match:
            device_name = match.group(1)
          match = global_memory_re.match(line)
          if match:
            gpu_mem = match.group(1)
            gpu_mem_units = match.group(2)

            if gpu_mem_units == 'GBytes': n_bytes_gpu = float(gpu_mem)*1024**3
            if gpu_mem_units == 'MBytes': n_bytes_gpu = float(gpu_mem)*1024**2
            break
        break
  print >>sys.stderr, "GPU Device ID:", device_id
  print >>sys.stderr, "GPU Name:", device_name
  print >>sys.stderr, "GPU Memory (bytes):", n_bytes_gpu

  return n_bytes_gpu


def create_scene_xml(gpu_device, refinements, gsd, 
                     lla1=None, lla2=None, lvcs1=None, lvcs2=None,
                     origin=None, output_file=sys.stdout, model_dir = ".", 
                     appearance_models=None, number_bins=1):
  ''' Create a scene xml file based off of input parameters

      Required arguments:
      gpu_device - The GPU device used for the block size calculation. The 
                   scene will be made to fit specifically on that gpu device
      refinements - Number of refinement passes. Max should be 3, even if you
                    refine more times than 3 times.
      gsd - The desired voxel size. This is in meters when using lla notation

      Mutually exclusive arguments:
      lla1,lla2 - The min and max (in order) longitude, latitude, altitude 
                  coordinates for bounding box of the scene. Will be expanded
                  to the next sublock
      lvcs1, lvcs2 - The min and max (in order) x, y, z coordinates for
                     bounding box of the scene. Will be expanded to the next
                     sublock

      Optional arguments:
      origin - Origin of scene. Default: lla1 or (0,0,0) if lvcs1 is used
      output_file - Output file object. Must support .write. 
                    Default: sys.stdout
      model_dir - The model dir used. is_model_local="true" is always used
                  Default: "."
      appearance_models - Tuple of appearance models to be used. 
                          Default: ('boxm2_mog3_grey','boxm2_num_obs')
      number_bins - Sets the num_illumination_bins. Default: 1
      '''
  
  #impose mutually exclusive constraint
  assert(lla1 is None or lvcs1 is None)
  assert(lla2 is None or lvcs2 is None)

  if origin is None:
    if lla1 is None:
      origin = (0,0,0)
    else:
      origin = lla1


  if lvcs1 is None or lvcs2 is None:
    lvcs = vpgl_adaptor.create_lvcs(lat=origin[1], lon=origin[0], el=origin[2],
                                    csname="wgs84")

  # transform the coordinate system from lat/lon/height to a lvcs (meters) with
  # the origin at one corner of the scene
  if lvcs1 is None:
    lvcs1 = vpgl_adaptor.convert_to_local_coordinates2(lvcs, 
        lla1[1], lla1[0], lla1[2])

  if lvcs2 is None:
    lvcs2 = vpgl_adaptor.convert_to_local_coordinates2(lvcs, 
        lla2[1], lla2[0], lla2[2])

  lvcs_size = map(lambda x,y:y-x, lvcs1, lvcs2)

  (n_blocks, n_subblocks, subblock_len) = calculate_block_parameters(
      gpu_device, refinements, gsd, lvcs_size)

  generate_scene_xml(output_file, model_dir,
      num_blocks=n_blocks, num_subblocks=n_subblocks, 
      subblock_size=subblock_len, appearance_models=appearance_models, 
      num_bins=number_bins, max_level=refinements+1, lvcs_og=origin,
      local_og=lvcs1)


def bytes_per_subblock(n_refinement_passes):
  # storage requirement for the sub-block's octree

  # number of cells in the sub-blocks's octree
  n_cells_per_subblock = sum([8**n for n in range(0,n_refinement_passes+1)])
  # alpha:4, mog3/gauss:8, num_obs:8, aux:16
  n_bytes_per_subblock = 36*n_cells_per_subblock

  return n_bytes_per_subblock


def subblocks_per_block(n_refinement_passes, n_bytes_gpu):
  n_bytes_subb = bytes_per_subblock(n_refinement_passes)
  max_bytes_block = n_bytes_gpu/2.0 # leave room for other operations
  # max sub-blocks per block
  total_subblocks_per_block = max_bytes_block / n_bytes_subb

  # number of sub-blocks per dimension in a block (grid pattern); depends on
  # the amount of GPU memory
  max_n_subblocks_xyz = math.floor(total_subblocks_per_block**(1.0/3.0))

  return max_n_subblocks_xyz, max_bytes_block


def calculate_block_parameters(gpu_device, n_refinement_passes, gsd, 
                               scene_length):
  (lx,ly,lz) = scene_length

  n_bytes_gpu = gpu_memory(gpu_device)

  max_n_subblocks_xyz, max_bytes_block = subblocks_per_block(
      n_refinement_passes, n_bytes_gpu)

  # resolution of a leaf cell
  voxel_length = gsd
  # change to resolution of a sub-block (e.g., the root node of the sub-block's
  # octree is 16 m on a side)
  subblock_len = voxel_length * 2.0**n_refinement_passes

  # block length in meters; assume it is a cube
  max_block_len = max_n_subblocks_xyz*subblock_len

  n_blocks_x = int(math.ceil(lx / max_block_len))
  n_blocks_y = int(math.ceil(ly / max_block_len))
  n_blocks_z = int(math.ceil(lz / max_block_len))

  # clip the z height of the scene; compute the minimum number of sub-blocks
  # (which will be distributed evenly among the z blocks) needed to cover the 
  # scene
  # n_subblocks_z cannot get larger
  n_subblocks_z = int(math.ceil(lz / (n_blocks_z*subblock_len)))


  # re-estimate max_n_subblocks_xy; if n_subblocks_z was clipped,
  # then we can have more sub-blocks in xy
  n_bytes_subb = bytes_per_subblock(n_refinement_passes)
  max_n_subblocks_xy = int(math.ceil(math.sqrt(max_bytes_block / \
                                               (n_subblocks_z*n_bytes_subb))))

  # re-compute n_subblocks_{x,y}; should either have enough sub-blocks to cover
  # the scene or as possible
  n_subblocks_x = int(math.ceil(lx / (n_blocks_x*subblock_len)))
  n_subblocks_y = int(math.ceil(ly / (n_blocks_y*subblock_len)))
  n_subblocks_x = min(n_subblocks_x, max_n_subblocks_xy)
  n_subblocks_y = min(n_subblocks_y, max_n_subblocks_xy)

  # re-compute the number of blocks needed to cover the scene
  n_blocks_x = int(math.ceil(lx / (n_subblocks_x*subblock_len)))
  n_blocks_y = int(math.ceil(ly / (n_subblocks_y*subblock_len)))
  # cannot change...
  #n_blocks_z = int(math.ceil(lz / (n_subblocks_z*subblock_len)))
  block_len_x = n_subblocks_x*subblock_len
  block_len_y = n_subblocks_y*subblock_len
  block_len_z = n_subblocks_z *subblock_len


  # print summary of the scene.xml file
  print >>sys.stderr, "nblocks_x:", n_blocks_x, " y:", n_blocks_y, \
                      " z:", n_blocks_z
  print >>sys.stderr, "block_len_x (m):", block_len_x, \
                      " n_subblocks_x:", n_subblocks_x
  print >>sys.stderr, "block_len_y (m):", block_len_y, \
                      " n_subblocks_y:", n_subblocks_y
  print >>sys.stderr, "block_len z (m):", block_len_z, \
                      " n_subblocks_z:", n_subblocks_z
  print >>sys.stderr, "subblock_len (m):", subblock_len, \
                      " n_refinement_passes:", n_refinement_passes
  print >>sys.stderr, "input scene length (m) x:", lx, " blocked x:", \
        n_blocks_x*n_subblocks_x*subblock_len
  print >>sys.stderr, "input scene length (m) y:", ly, " blocked y:", \
        n_blocks_y*n_subblocks_y*subblock_len
  print >>sys.stderr, "input scene length (m) z:", lz, " blocked z:", \
        n_blocks_z*n_subblocks_z*subblock_len

  n_subb = n_subblocks_x*n_subblocks_y*n_subblocks_z
  #n_cells_subb = 1+8+64+512
  #n_bytes_subb = 36*n_cells_subb  # alpha:4, mog3/gauss:8, num_obs:8, aux:16
  n_bytes_block = n_subb*n_bytes_subb
  print >>sys.stderr, "Memory requirements for a block at finest resolution:",\
        n_bytes_block/1e6, "MB per block"
  print >>sys.stderr, "  including bit tree:", \
                      (n_bytes_block + n_subb*16)/1e6, "MB"
  print >>sys.stderr, "  entire world (worst case):", \
        (n_bytes_block + n_subb*16)*n_blocks_x*n_blocks_y*n_blocks_z/1e6, "MB"

  return (n_blocks_x, n_blocks_y, n_blocks_z), \
         (n_subblocks_x, n_subblocks_y, n_subblocks_z), subblock_len


if __name__ == '__main__':
  main()