
'''
@created: Dec, 2014
@author: ydong & srichardson
Script to convert a scene.xml file to a scene.kml file, which can be loaded in Google Earth
'''

import sys, os.path
import argparse

import boxm2_adaptor as adaptor
from boxm2_scene_adaptor import boxm2_scene_adaptor


def main(args=None):
  # handle inputs #
  parser = argparse.ArgumentParser()
  parser.add_argument("-s", "--scene", metavar='FILE', default="./model/scene.xml",
      help="XML scene file defining the model")
  parser.add_argument('output_file', nargs='?', default=None,
                      help="Filename to write scene.kml to. Default is scene.kml in same dir")
  options = parser.parse_args(args)
  scene_xml, scene_kml = options.scene, options.output_file

  scene = boxm2_scene_adaptor(scene_xml, "cpp")
  description = adaptor.describe_scene(scene.scene)
  for key, value in description.iteritems():
    print(" key = {}, value = {}".format(key, value))
  if scene_kml is None:
    scene_kml = os.path.join(description["dataPath"], "scene.kml")
  adaptor.write_scene_to_kml(scene.scene, scene_kml)

  scene.clear_cache()


if __name__ == '__main__':
  main()
