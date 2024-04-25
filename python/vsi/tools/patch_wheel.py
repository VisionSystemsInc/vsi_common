#!/usr/bin/env python

import zipfile
import pathlib
import os
import argparse
import tempfile

def get_parser():
  parser = argparse.ArgumentParser(
    description="Patch a wheel to change the package name or version in the "
                "wheel metatdata. Note: This does not change any filenames or "
                "version in the rest of the files (e.g. dist-info directory "
                "name nor versions in .py files)")
  parser.add_argument('filename', help="Wheel name")
  # # This feature requires renaming the .dist-info files, while version number changes do not.
  # # Which should also require RECORD being regenerated. Out of scope until needed.
  # parser.add_argument('--name', help="The package name, can be different than the filename due name normalization special characters")
  group = parser.add_mutually_exclusive_group()
  group.add_argument('--version', help="Version number to change to")
  group.add_argument('--add-local', help="Add to the local version segment without having to specify the full version")
  return parser


def main(filename, version=None):
  filename = pathlib.Path(filename)

  # Split to {normalize name}-{version}-{remainder}
  normalized_name, file_version, remainder = filename.stem.split('-', 2)

  patch = {}
  # if name is not None:
  #   # https://peps.python.org/pep-0491/#escaping-and-unicode
  #   normalized_name = re.sub(r"[^\w\d.]+", "_", name).lower()
  #   patch[b'Name'] = b'Name: ' + name.encode()
  if version is not None:
    patch[b'Version'] = b'Version: ' + version.encode()
  else:
    version = file_version

  new_filename = filename.parent / ('-'.join([normalized_name,
                                              version,
                                              remainder]) + '.whl')

  with tempfile.NamedTemporaryFile(suffix='.whl',
                                   prefix='.' + filename.stem + '.',
                                   dir=filename.parent,
                                   delete=False) as temp_file:
    with zipfile.ZipFile(filename, 'r') as zin:
      with zipfile.ZipFile(temp_file, 'w') as zout:
        zout.comment = zin.comment # preserve the comment
        for item in zin.infolist():
          # Patch METADATA to match filename
          if item.filename.endswith('.dist-info/METADATA'):
            meta_lines = (patch[key]
                          if (key := line.split(b':',1)[0]) in patch.keys()
                          else line
                          for line in zin.read(item.filename).split(b'\n'))
            zout.writestr(item, b'\n'.join(meta_lines))
          else:
            zout.writestr(item, zin.read(item.filename))
  os.rename(temp_file.name, new_filename)

if __name__ == '__main__':
  parser = get_parser()
  args = parser.parse_args()

  version = args.version
  filename = pathlib.Path(args.filename)

  if args.add_local is not None:
    version = filename.stem.split('-', 2)[1]
    if '+' in filename.stem:
      version = f'{version}.{args.add_local}'
    else:
      version = f'{version}+{args.add_local}'

  main(filename, version=version)
