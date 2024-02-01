import yaml
import sys

# Not quite right

def yarp(doc, prefix=''):
  lines = []
  extra = []

  if isinstance(doc, dict):
    lines.append('{}={{}}'.format(prefix))
    for (key, value) in doc.items():
      if prefix:
        line = '{}.{}'.format(prefix, key)
      else:
        line = key
      lines += yarp(value, line)
  elif isinstance(doc, list):
    lines.append('{}=[]'.format(prefix))
    for i, value in enumerate(doc):
      lines += yarp(value, '{}[{}]'.format(prefix, i))
  elif isinstance(doc, (str, int)):
    lines.append('{} = {}'.format(prefix, doc))
  elif doc is None:
    lines.append('{}=None'.format(prefix))
  else:
    raise Exception('Unknown type {}'.format(type(doc)))

  return lines

if __name__ == "__main__":
  print('\n'.join(yarp(yaml.safe_load(sys.stdin))))
