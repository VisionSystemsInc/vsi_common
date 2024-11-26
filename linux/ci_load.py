#!/usr/bin/env python

# DEPRECATED #

import argparse
import tempfile
from subprocess import Popen, PIPE
import os
import re
from os import environ as env
import copy

import yaml

stage_pattern=r'^ *from +[a-zA-Z0-9:\./_${}-]* +as +([^\n]*)'

'''
## Explanation how this script works:

#. Parses the docker-compose file. The docker-compose file is fed through ``docker-compose config`` so that all variables are substituted and anchors are expanded. This means that this needed to be run within ``just`` so that all environment variables are loaded.
#. A temporary "push pull" docker-compose yaml file is auto generated. This file will push and pull the cache from dockerhub (or whatever registry you decide to use)
#. The docker cache images are pulled
#. Another temporary docker-compose file is auto generated. This file is used to restore the recipes from the cache pulled, using cache-from. So if the image is pulled as "vsi-ri/cache:recipe_gosu" and the image name should be "vsi-ri/recipe:gosu", it will let you build "vsi-ri/recipe:gosu" using "--cache-from = vsi-ri/cache:gosu". Note: this is the ONBUILD recipes, not the gosu stage (recipe "instance") that appears in your actual Dockerfile.
#. The recipes set up in step 3 are built
#. The recipes built in step 4 are re-tagged to their "cached" names, so that they are ready to be pushed at the end
#. A third docker-compose file is auto generated. The original docker-compose file is loaded, and a section for every single stage of the Dockerfile is copied based on the "main service" you specify. All of the possible "cache from" image names are added so that docker can build using the cache and the stages previously build. For example. If you build stage1 then stage2, stage2 shouldn't rebuild stage1, it should cache-from stage1, etc...
#. Unfortunately docker-compose cannot be used to build a multistage dockerfile efficiently, it will rebuild every stage for unknown reasons. So the docker-compose file is parsed and docker calls are made to build the stages in order. Finally, the main service stage (the final stage) is built, at this point all the previous stages have been built and cached, so only the last stage is built.

  * The (optional) other services are tagged from the cached images just generated (based on the target stage names found in the docker-compose file), and then the main service image is tagged too. This way the image names have been restored so that they are ready for CI to use.

#. Finally, that now updated images are push back to the registry
'''

def Popen2(*args, **kwargs):
  # import shlex
  # print('\x1b[31m'+' '.join(shlex.quote(arg) for arg in args[0])+'\x1b[0m')
  pid = Popen(*args, **kwargs)
  pid.wait()
  assert pid.returncode == 0

class CiLoad:

  def setup(self):
    pid = Popen([self.docker_compose_exe, '-f', self.compose, 'config'],
                stdout=PIPE)
    output = pid.communicate()[0]

    self.compose_yaml = yaml.safe_load(output)
    self.compose_version = self.compose_yaml.get('version', None)

    # Get dockerfile name
    build = self.compose_yaml['services'][self.main_service]['build']
    self.dockerfile = self.get_dockerfile(build)

    dockerfile = open(self.dockerfile, 'r').read()
    # get stage names
    self.stages = re.findall(stage_pattern, dockerfile, re.I+re.MULTILINE)

    # get recipes used
    recipe_pattern = re.escape(self.recipe_repo)
    recipe_pattern = rf'^ *from +{recipe_pattern}:([^ \n]+)'
    self.recipes = re.findall(recipe_pattern, dockerfile, re.I+re.MULTILINE)

  def get_dockerfile(self, build):
    if 'context' in build:
      if 'dockerfile' in build:
        dockerfile = os.path.join(build['context'], build['dockerfile'])
      else:
        dockerfile = os.path.join(build['context'], 'Dockerfile')
    else:
      dockerfile = os.path.join(build, 'Dockerfile')

    # If it's relative, it's relative to the compose file (or project-dir,
    # not supported)
    if not os.path.isabs(dockerfile):
      dockerfile = os.path.join(self.project_dir, dockerfile)

    return os.path.normpath(dockerfile)

  def cache_image(self, *extra_tags, cache_loc=None):

    # default cache_location
    if not cache_loc:
      cache_loc = self.cache_repo

    # cache_loc of the form "vsiri/cache:tag_header"
    if ':' in cache_loc:
      cache_repo, tag = cache_loc.split(':')
      cache_tags = [tag]

    # cache_loc of the form "vsiri/cache"
    else:
      cache_repo = cache_loc
      cache_tags = [self.cache_version, self.main_service]

    # assemble cache image string
    cache_tag = '_'.join([t for t in cache_tags + list(extra_tags) if t])
    return f'{cache_repo}:{cache_tag}'

  # 1 Generate push & pull config _dynamic_docker-compose_push_pull
  def generate_push_pull_config(self, cache_id=0, cache_loc=None):

    def _service_dict(cache_id=0, cache_loc=None):
      services = dict()
      services[f'final_{self.main_service}_{cache_id}'] = {'build': '.',
          'image': self.cache_image('final', cache_loc=cache_loc)}
      for stage in self.stages:
        services[f'stage_{stage}_{cache_id}'] = {'build': '.',
            'image': self.cache_image('stage', stage, cache_loc=cache_loc)}
      for recipe in self.recipes:
        services[f'recipe_{recipe}_{cache_id}'] = {'build': '.',
            'image': self.cache_image('recipe', recipe, cache_loc=cache_loc)}
      return services

    # pull dictionary
    services = dict()
    for cache_id, cache_loc in enumerate([self.cache_repo] + self.other_repos):
      services.update(_service_dict(cache_id, cache_loc))
    self.pull_dict = {'services': services}

    # push dictionary
    self.push_dict = {'services': _service_dict()}

  # 2 pull images
  def pull_images(self):
    if self.pull:

      if self.print_push_pull:
        print('PULL CONFIGURATION:')
        print(yaml.dump(self.pull_dict))

      with tempfile.NamedTemporaryFile(mode='w') as pull_file:
        pull_file.write(yaml.dump(self.pull_dict))
        pull_file.flush()

        pull_cmd = [self.docker_compose_exe, '-f', pull_file.name, 'pull',
                    '--ignore-pull-failures']
        if self.quiet_pull:
          pull_cmd.append('-q')

        print("Pulling available images...")
        try:
          Popen2(pull_cmd)
        except AssertionError:
          print(f"<{' '.join(pull_cmd)}> failed; images may not exist yet")

  # 3. _dynamic_docker-compose_restore_recipes
  def write_restore_recipe(self):
    self.restore_recipe_file = tempfile.NamedTemporaryFile(mode='w')

    doc = {}
    compose_yaml = yaml.safe_load(open(self.recipe_compose, 'r').read())
    if self.compose_version is not None:
      doc['version'] = self.compose_version

    services = {}

    for recipe in self.recipes:
      services[recipe] = {}
      services[recipe]['build'] = {}
      services[recipe]['build']['cache_from'] = \
          [self.cache_image('recipe', recipe),
           f'{self.recipe_repo}:{recipe}']

    doc['services'] = services

    self.restore_recipe_file.write(yaml.dump(doc))
    self.restore_recipe_file.flush()

  # 4 docker-compose build
  # 5 tag recipes
  def restore_recipes(self):
    if self.build and self.recipes:
      Popen2([self.docker_compose_exe,
              '-f', self.recipe_compose,
              '-f', self.restore_recipe_file.name,
              'build', *self.recipes])

      for recipe in self.recipes:
        Popen2([self.docker_exe, 'tag', f'{self.recipe_repo}:{recipe}',
                self.cache_image('recipe', recipe)])

  def add_cache_from(self, cf):
    image = self.compose_yaml['services'][self.main_service].get('image')

    if image is not None:
      cf.append(image)
    for service in self.other_services:
      image = self.compose_yaml['services'][service].get('image')
      if image is not None:
        cf.append(image)
    for recipe in self.recipes:
      cf.append(f'{self.recipe_repo}:{recipe}')

    for cache_loc in [self.cache_repo] + self.other_repos:
      cf.append(self.cache_image('final', cache_loc=cache_loc))
      for stage_from in self.stages:
        cf.append(self.cache_image('stage', stage_from, cache_loc=cache_loc))
      for recipe in self.recipes:
        cf.append(self.cache_image('recipe', recipe, cache_loc=cache_loc))

    return cf


  # 6 _dynamic_docker-compose_add_cache_from
  def write_add_cache(self):
    self.add_stages_file = tempfile.NamedTemporaryFile(mode='w')
    # self.add_stages_cache_file = tempfile.NamedTemporaryFile(mode='w')

    for stage in self.stages:
      stage_service_name = f'{self.main_service}_auto_gen_{stage}'
      if stage_service_name in self.compose_yaml['services']:
        raise Exception(f'{stage_service_name} is already a service.')
      service = copy.deepcopy(self.compose_yaml['services'][self.main_service])
      # Set image name (for pushing)
      service['image'] = self.cache_image('stage', stage)
      # Set build target
      if 'build' not in service:
        service['build'] = {}
      if 'target' not in service['build']:
        service['build']['target'] = stage
      # Setup cache_from
      service['build']['cache_from'] = \
          self.add_cache_from(service['build'].get('cache_from', []))
      self.compose_yaml['services'][stage_service_name] = service

    # Add cache_from for services
    for service_name in [self.main_service] + self.other_services:
      if 'build' not in self.compose_yaml['services'][service_name]:
        self.compose_yaml['services'][service_name]['build'] = {}
      cf = self.add_cache_from(
          self.compose_yaml['services'][service_name]['build'].get(
              'cache_from', []))
      self.compose_yaml['services'][service_name]['build']['cache_from'] = cf

    self.add_stages_file.write(yaml.dump(self.compose_yaml,
                                         Dumper=yaml.Dumper))
    self.add_stages_file.flush()

  # 7 build
  def build_stages(self):
    yaml_content = yaml.safe_load(open(self.add_stages_file.name, 'r').read())
    main_image = self.compose_yaml['services'][self.main_service].get('image')

    if self.print_build:
      print('BUILD CONFIGURATION:')
      print(yaml.dump(yaml_content))

    def build_stage(stage_name):
      build = yaml_content['services'][f'{stage_name}']['build']
      image_name = yaml_content['services'][f'{stage_name}']['image']

      cmd = [self.docker_exe, 'build']
      cmd += ['-f', self.get_dockerfile(build)]
      if 'target' in build:
        cmd += ['--target', build['target']]
      for arg in build.get('args', []):
        # Already been expanded by config
        # value = os.path.expandvars(build["args"][arg])
        cmd += ['--build-arg', f'{arg}={build["args"][arg]}']
      for cache in build.get('cache_from', []):
        cmd += ['--cache-from', cache]
      cmd += ['-t', image_name]
      cmd += [build['context']]
      Popen2(cmd)

    if self.build:
      # Build all the stages with names in the Dockerfile
      for stage in self.stages:
        build_stage(f'{self.main_service}_auto_gen_{stage}')

      # Build the main (last) stage here
      build_stage(self.main_service)

      for service in self.other_services:
        cmd = [self.docker_exe, 'tag']

        target = yaml_content['services'][service]['build'].get('target', None)
        if target is None:
          cmd += [self.cache_image('final')]
        else:
          cmd += [self.cache_image('stage', target)]
        cmd += [yaml_content['services'][service]['image']]
        Popen2(cmd)

    Popen2([self.docker_exe,
            'tag',
            main_image,
            self.cache_image('final')])

  # 8 push
  def push_images(self):
    if self.push:

      if self.print_push_pull:
        print('PUSH CONFIGURATION:')
        print(yaml.dump(self.push_dict))

      with tempfile.NamedTemporaryFile(mode='w') as push_file:
        push_file.write(yaml.dump(self.push_dict))
        push_file.flush()
        Popen2([self.docker_compose_exe, '-f', push_file.name, 'push'])

  def setup_parser(self):
    self.parser = argparse.ArgumentParser()
    aa = self.parser.add_argument
    aa('--docker-compose-exe', type=str, default='docker-compose',
       help='Docker compose exectuable')
    aa('--docker-exe', type=str, default='docker',
       help='Docker exectuable')
    aa('--project-dir', type=str, default=None,
       help='The compose project dir. Default: docker-compose.yml dir')
    aa('--cache-repo', type=str, default='vsiri/ci_cache',
       help='Docker repo for storing cache images')
    aa('--other-repos', type=str, nargs='+', default=[],
       help='Additional docker repo(s) to check for cache images')
    aa('--cache-version', type=str, default=None,
       help='Cache version')
    aa('--recipe-repo', type=str, default='vsiri/recipe',
       help='Repo recipes (ONBUILD) images are in')
    aa('--recipe-compose', type=str,
       default=os.path.join(env["VSI_COMMON_DIR"],
                            "docker/recipes/docker-compose.yml"),
       help='Recipe compose file')

    group = self.parser.add_mutually_exclusive_group()
    group.add_argument('--pull', dest='pull', action='store_true',
                       help='Enable pulling images (default)')
    group.add_argument('--no-pull', dest='pull', action='store_false',
                       help='Disable pulling images')
    self.parser.set_defaults(pull=True)

    group = self.parser.add_mutually_exclusive_group()
    group.add_argument('--build', dest='build', action='store_true',
                       help='Enable building images (default)')
    group.add_argument('--no-build', dest='build', action='store_false',
                       help='Disable building images')
    self.parser.set_defaults(build=True)

    group = self.parser.add_mutually_exclusive_group()
    group.add_argument('--push', dest='push', action='store_true',
                       help='Enable pushing images')
    group.add_argument('--no-push', dest='push', action='store_false',
                       help='Disable pushing images (default)')
    self.parser.set_defaults(push=False)

    aa('--quiet-pull', dest='quiet_pull', action='store_true',
       default=False, help='Quiet pull (no progress bars)')

    aa('--print-push-pull', dest='print_push_pull', action='store_true',
       default=False, help='Print push/pull configuration')
    aa('--print-build', dest='print_build', action='store_true',
       default=False, help='Print build configuration')

    aa('compose', type=str, help='Docker compose yaml file')
    aa('main_service', type=str, help='Main docker-compose service')
    aa('services', type=str, nargs='*',
       help='Additional services to be tagged')

  def parse(self):
    args = self.parser.parse_args()
    self.compose = args.compose
    self.main_service = args.main_service
    self.other_services = args.services
    self.cache_repo = args.cache_repo
    self.other_repos = args.other_repos
    self.cache_version = args.cache_version
    self.recipe_repo = args.recipe_repo
    self.recipe_compose = args.recipe_compose
    self.docker_compose_exe = args.docker_compose_exe
    self.docker_exe = args.docker_exe

    self.push = args.push
    self.pull = args.pull
    self.build = args.build

    self.quiet_pull = args.quiet_pull
    self.print_push_pull = args.print_push_pull
    self.print_build = args.print_build

    if args.project_dir is None:
      self.project_dir = os.path.dirname(self.compose)
    else:
      self.project_dir = args.project_dir

    self.compose = os.path.normpath(os.path.abspath(self.compose))
    self.project_dir = os.path.normpath(os.path.abspath(self.project_dir))

if __name__ == '__main__':
  ci_load = CiLoad()
  ci_load.setup_parser()
  ci_load.parse()

  ci_load.setup()

  ci_load.generate_push_pull_config()
  ci_load.pull_images()

  ci_load.write_restore_recipe()
  ci_load.restore_recipes()

  ci_load.write_add_cache()
  ci_load.build_stages()

  ci_load.push_images()
