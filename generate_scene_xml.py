# file: generate_scene_xml.py
# author: Daniel Crispell <dan@visionsystemsinc.com>
# 
# Generates a scene.xml file describing a boxm2 voxel model
#
################################## parameters #############################################
# base model directory
model_dir = '/home/dec/MBC/models/NTC'
# directory where the .bin files will be stored
data_path = model_dir + '/bin'
# name of file to generate
filename = model_dir + '/scene.xml'

# the appearance model type to use
appearance_model = 'boxm2_mog3_grey'
# the number of independent appearance models the model contains
num_bins = 1
# finest subdivision level (1 = no subdivision, 2=2x2x2, 3=4x4x4, 4=8x8x8, etc.)
max_level = 3

# NTC/Galactica
lvcs_og_lat = 35.3307
lvcs_og_lon = -116.5210
lvcs_og_hae = 720.0

# the south-western most point of the voxel model, in local coordinates
local_og_x = -400.0
local_og_y = -400.0
local_og_z = -20.0

# the number of blocks in the model
n_blocks_x = 8 
n_blocks_y = 8 
n_blocks_z = 1

# how many subblocks (i.e. voxels, before any subdivision) in each block 
n_subblocks_x = 50
n_subblocks_y = 50
n_subblocks_z = 50

# the size of each subblock (in meters)
subblock_size = 2.0

# Providence
"""
# the origin of the local coordinate system
#lvcs_og_lat = 41.8247
#lvcs_og_lon = -71.4127
#lvcs_og_hae = -30.0


# the south-western most point of the voxel model, in local coordinates
local_og_x = -100
local_og_y = -225.0
local_og_z = -10.0

# the number of blocks in the model
n_blocks_x = 6
n_blocks_y = 5
n_blocks_z = 1

# how many subblocks (i.e. voxels, before any subdivision) in each block 
n_subblocks_x = 50
n_subblocks_y = 50
n_subblocks_z = 75

# the size of each subblock (in meters)
subblock_size = 2.0

# Ft Drum: center of orbit site
lvcs_og_lat = 44.1264
lvcs_og_lon = -75.6389 
lvcs_og_hae = 152.0

# the south-western most point of the voxel model, in local coordinates
local_og_x = -400.0
local_og_y = -400.0
local_og_z = -10.0

# the number of blocks in the model
n_blocks_x = 8
n_blocks_y = 8
n_blocks_z = 1

# how many subblocks (i.e. voxels, before any subdivision) in each block 
n_subblocks_x = 50
n_subblocks_y = 50
n_subblocks_z = 50

# the size of each subblock (in meters)
subblock_size = 2.0
"""
#######################################################################################

fd = open(filename,'w')
fd.write('<scene>\n')
fd.write('<lvcs cs_name="wgs84" origin_lat="' + str(lvcs_og_lat) + '" origin_lon="' + str(lvcs_og_lon) + '" origin_elev="' + str(lvcs_og_hae) + '" local_XYZ_unit="meters" geo_angle_unit="degrees">\n')
fd.write('</lvcs>\n')
fd.write('<local_origin x="' + str(local_og_x) + '" y="' + str(local_og_y) + '" z="' + str(local_og_z) +'">\n')
fd.write('</local_origin>\n')
fd.write('<scene_paths path="' + data_path + '/">\n')
fd.write('</scene_paths>\n')
fd.write('<version number="2">\n')
fd.write('</version>\n')
fd.write('<appearance apm="' + appearance_model + '">\n')
fd.write('</appearance>\n')
fd.write('<appearance apm="boxm2_num_obs">\n')
fd.write('</appearance>\n')
fd.write('<appearance num_illumination_bins="'+str(num_bins)+'">\n')
fd.write('</appearance>\n')

for i in range(0,n_blocks_x):
  for j in range(0,n_blocks_y):

    for k in range(0,n_blocks_z):
      block_og_x = local_og_x + (i * n_subblocks_x * subblock_size)
      block_og_y = local_og_y + (j * n_subblocks_y * subblock_size)
      block_og_z = local_og_z + (k * n_subblocks_z * subblock_size)
      fd.write('<block id_i="' +str(i) + '" id_j="' + str(j) + '" id_k="' + str(k) + '" ')
      fd.write('origin_x="' + str(block_og_x) + '" origin_y="' + str(block_og_y) + '" origin_z="' + str(block_og_z) + '" ')
      fd.write('dim_x="' + str(subblock_size) + '" dim_y="' + str(subblock_size) + '" dim_z="' + str(subblock_size) + '" ')
      fd.write('num_x="' + str(n_subblocks_x) + '" num_y="' + str(n_subblocks_y) + '" num_z="' + str(n_subblocks_z) + '" ')
      fd.write('init_level="1" max_level="' + str(max_level) + '" max_mb="1200.0" p_init="0.001000" random="0">\n')
      fd.write('</block>\n')
fd.write('</scene>')
fd.close()
