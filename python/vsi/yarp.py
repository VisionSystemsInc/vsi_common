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

  # lines.append(line)
  # lines += extra


  # for (key, value) in doc.items():
  #   extra = []
  #   line = '{}.{}'.format(prefix, key)
  #   if isinstance(value, dict):
  #     extra = yarp(value, line)
  #     line += ' = {}'
  #   elif isinstance(value, list):
  #     for val, i in enumerate(value):
  #       extra += yarp(value[i], '{}[{}]'.format(line, i))
  #     line += '= []'
  #   elif isinstance(value, str):
  #     line += ' = {}'.format(value)
  #   else:
  #     raise Exception('Unknown type')
  #   lines.append(line)
  #   lines += extra

  return lines

if __name__ == "__main__":
  print('\n'.join(yarp(yaml.load(sys.stdin, Loader=yaml.Loader))))
