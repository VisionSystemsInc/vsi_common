#! /usr/bin/env python
""" Generate a boxm2-style scene.xml file """
import argparse
import generate_scene_xml
import mesh_utils
import sys
import numpy as np

def generate_scene_xml_from_mesh(mesh_filename, output_filename, model_dir_rel, num_blocks, max_num_subblocks, appearance_models, num_bins, max_level, lvcs_origin ):
    """ generate the scene.xml to fit geometry defined in the ply or obj file """
    # get the mesh vertices in numpy matrix form
    verts = mesh_utils.get_mesh_vertices(mesh_filename)
    # compute subblock size needed to contain all vertices
    bbox_size = verts.max(axis=1) - verts.min(axis=1)
    # add some padding to avoid points right on the boundary of the volume
    pad_amount = 0.1*bbox_size
    bbox_size += 2.0*pad_amount
    # local origin is the minimum of the vertices
    local_origin = verts.min(axis=1) - pad_amount
    max_total_num_subblocks = np.array(num_blocks) * max_num_subblocks
    subblock_size = np.max(bbox_size / max_total_num_subblocks )
    block_size = bbox_size / np.array(num_blocks)
    num_subblocks = np.ceil(block_size / subblock_size)
    print('local_origin = ' + str(local_origin))
    print('block_size = ' + str(block_size))
    print('subblock_size = ' + str(subblock_size))
    print('num_subblocks = ' + str(num_subblocks))

    output_fd = open(output_filename, 'w')
    generate_scene_xml.generate_scene_xml(output_fd, model_dir_rel, num_blocks, num_subblocks, subblock_size, appearance_models, num_bins, max_level, lvcs_origin, local_origin)

def main():
    """ main """
    parser = argparse.ArgumentParser()
    parser.add_argument('mesh_filename', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('output_filename', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('--model_dir_rel', default='.')
    parser.add_argument('--num_blocks', nargs=3, type=int, default=(1,1,1))
    parser.add_argument('--num_subblocks', nargs=3, type=int, default=(100,100,100))
    parser.add_argument('--appearance_models', nargs='+', default=('boxm2_mog3_grey',))
    parser.add_argument('--num_bins', type=int, default=1)
    parser.add_argument('--max_level', type=int, default=3)
    parser.add_argument('--lvcs_origin', nargs=3, type=float, help='LVCS origin in form lon lat hae', default=None)
    args = parser.parse_args()


    generate_scene_xml_from_mesh(args.mesh_filename, args.output_file, args.model_dir_rel, args.num_blocks, args.num_subblocks, args.appearance_models, args.num_bins, args.max_level, args.lvcs_origin)


if __name__ == '__main__':
    main()
