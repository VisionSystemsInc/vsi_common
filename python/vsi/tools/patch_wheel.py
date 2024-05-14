#!/usr/bin/env python

from pathlib import Path
import os
import argparse
import tempfile
import subprocess
import re
from wheel.wheelfile import WHEEL_INFO_RE

def get_parser():
  parser = argparse.ArgumentParser(
    description="Patch a wheel to change the package name or version in the "
                "wheel metatdata. Note: This will also change any filenames or "
                "versions in the rest of the file namess (e.g. dist-info "
                "directory name) but will not change versions strings "
                "hardcodeded in .py files")
  parser.add_argument('filename', help="Wheel (.whl) file")
  parser.add_argument('--name', help="The package name")
  group = parser.add_mutually_exclusive_group()
  group.add_argument('--version', help="Version number to change to")
  group.add_argument('--add-local',
                     help="Add to the local version segment without having to "
                          "specify the full version")
  return parser


def main(filename, name=None, version=None):
  filename = Path(filename)

  parsed_name = WHEEL_INFO_RE.match(filename.name)
  original_name, original_version = parsed_name.group('name', 'ver')

  # These values will be replaced
  patch = {}
  if name is not None:
    patch['Name'] = f'Name: {name}\n'
  else:
    name = original_name
  if version is not None:
    patch['Version'] = f'Version: {version}\n'
  else:
    version = original_version

  # https://peps.python.org/pep-0491/#escaping-and-unicode
  normalized_name = re.sub(r"[^\w\d.]+", "_", name).lower()
  normalized_version = re.sub(r"[^\w\d.+]+", "_", version).lower()

  if name == original_name and version == original_version:
    raise Exception('No change detected. Package name and version are '
                    'identical')

  with tempfile.TemporaryDirectory() as temp_extract:
    # Extract Wheel
    subprocess.Popen(['wheel', 'unpack', '--dest', temp_extract,
                      filename]).wait()

    # Patch metadata
    metadata = (Path(temp_extract) /
                f'{original_name}-{original_version}' /
                f'{original_name}-{original_version}.dist-info/METADATA')
    with open(metadata, 'r+') as fid:
      meta_lines = (patch[key]
                    if (key := line.split(':',1)[0]) in patch.keys()
                    else line
                    for line in fid.readlines())
      fid.seek(0)
      fid.writelines(meta_lines)


    # Rename  files
    os.rename(Path(temp_extract) /
              f'{original_name}-{original_version}' /
              f'{original_name}-{original_version}.dist-info',
              Path(temp_extract) /
              f'{original_name}-{original_version}' /
              f'{normalized_name}-{normalized_version}.dist-info')
    os.rename(Path(temp_extract) /
              f'{original_name}-{original_version}',
              Path(temp_extract) /
              f'{normalized_name}-{normalized_version}')

    # Save new wheel
    with tempfile.TemporaryDirectory() as temp_wheel:
      subprocess.Popen(['wheel', 'pack', '--dest', temp_wheel,
                        Path(temp_extract) / f'{name}-{version}']).wait()

      new_wheel = next(Path(temp_wheel).glob('*.whl'))

      # Replace wheel
      os.rename(new_wheel, filename.parent / new_wheel.name)

      # It would be possible for the package name/version  to change but the
      # whl name to rename unchanged due to filename normalization (e.g.: -➡️_)
      if new_wheel != filename:
        os.remove(filename)

if __name__ == '__main__':
  parser = get_parser()
  args = parser.parse_args()

  version = args.version
  filename = Path(args.filename)

  if args.add_local is not None:
    version = WHEEL_INFO_RE.match(filename.name).group('ver')
    if '+' in version:
      # https://packaging.python.org/en/latest/specifications/version-specifiers/#local-version-identifiers
      # "each segment of the local version [is] divided by a ."
      version = f'{version}.{args.add_local}'
    else:
      version = f'{version}+{args.add_local}'

  main(filename, version=version)
