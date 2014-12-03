#! /usr/bin/env python
""" Generate a boxm2-style scene.xml file """
import argparse
import sys, os.path


def generate_scene_xml(output_file, model_dir_rel, num_blocks, num_subblocks, subblock_size, appearance_models=None, num_bins=1, max_level=3, lvcs_og=None, local_og=None):
    """ write the scene.xml file
    lvcs_og is a tuple stored as (lon, lat, hae)  (hae -> height above ellipsoid)
    """

    if appearance_models is None:
        appearance_models = ('boxm2_mog3_grey','boxm2_num_obs')

    if lvcs_og is None:
        lvcs_og = (0,0,0)

    if local_og is None:
        local_og = (0,0,0)

    output_file.write('<scene>\n')
    output_file.write('  <lvcs cs_name="wgs84" origin_lat="' + str(lvcs_og[1]) + '" origin_lon="' + str(lvcs_og[0]) + '" origin_elev="' + str(lvcs_og[2]) + '" local_XYZ_unit="meters" geo_angle_unit="degrees">\n')
    output_file.write('  </lvcs>\n')
    output_file.write('  <local_origin x="' + str(local_og[0]) + '" y="' + str(local_og[1]) + '" z="' + str(local_og[2]) +'">\n')
    output_file.write('  </local_origin>\n')
    output_file.write('  <scene_paths path="' + os.path.join(model_dir_rel,'') + '" is_model_local="true">\n')
    output_file.write('  </scene_paths>\n')
    output_file.write('  <version number="2">\n')
    output_file.write('  </version>\n')
    for appearance_model in appearance_models:
        output_file.write('  <appearance apm="' + appearance_model + '">\n')
        output_file.write('  </appearance>\n')
    output_file.write('  <appearance num_illumination_bins="'+str(num_bins)+'">\n')
    output_file.write('  </appearance>\n')

    for i in range(0, num_blocks[0]):
        for j in range(0, num_blocks[1]):
            for k in range(0, num_blocks[2]):
                block_og_x = local_og[0] + (i * num_subblocks[0] * subblock_size)
                block_og_y = local_og[1] + (j * num_subblocks[1] * subblock_size)
                block_og_z = local_og[2] + (k * num_subblocks[2] * subblock_size)
                output_file.write('  <block id_i="' +str(i) + '" id_j="' + str(j) + '" id_k="' + str(k) + '" ')
                output_file.write('origin_x="' + str(block_og_x) + '" origin_y="' + str(block_og_y) + '" origin_z="' + str(block_og_z) + '" ')
                output_file.write('dim_x="' + str(subblock_size) + '" dim_y="' + str(subblock_size) + '" dim_z="' + str(subblock_size) + '" ')
                output_file.write('num_x="' + str(num_subblocks[0]) + '" num_y="' + str(num_subblocks[1]) + '" num_z="' + str(num_subblocks[2]) + '" ')
                output_file.write('init_level="1" max_level="' + str(max_level) + '" max_mb="1200.0" p_init="0.001000" random="0"/>\n')
    output_file.write('</scene>')


def main():
    """ main """
    parser = argparse.ArgumentParser()
    parser.add_argument('output_file', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('--model_dir_rel', default='.')
    parser.add_argument('--num_blocks', nargs=3, type=int, default=(1,1,1))
    parser.add_argument('--num_subblocks', nargs=3, type=int, default=(100,100,100))
    parser.add_argument('--subblock_size', type=float, default=1.0)
    parser.add_argument('--appearance_model', nargs='*', default=['boxm2_mog3_grey','boxm2_num_obs'])
    parser.add_argument('--num_bins', type=int, default=1)
    parser.add_argument('--max_level', type=int, default=3)
    parser.add_argument('--lvcs_origin', nargs=3, type=float, help='LVCS origin in form lon lat hae', default=None)
    parser.add_argument('--local_origin', nargs=3, type=float, help='Local origin in form x y z', default=None)
    args = parser.parse_args()

    generate_scene_xml(args.output_file, args.model_dir_rel, args.num_blocks, args.num_subblocks, args.subblock_size, args.appearance_model, args.num_bins, args.max_level, args.lvcs_origin, args.local_origin)


if __name__ == '__main__':
    main()
