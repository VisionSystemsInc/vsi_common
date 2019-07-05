
# Does not preserve order
def dict_diff(a, b):
  change = set()
  add = set()
  delete = set()

  for key in b.keys():
    if key not in a:
      add.add(key)
    elif a[key] != b[key]:
      change.add(key)

  for key in a.keys():
    if key not in b:
      delete.add(key)

  output = []

  all_changes = delete | change | add

  for key in all_changes:
    if key in add:
      output.extend([f'+ {key}: {b[key]}'])
    elif key in delete:
      output.extend([f'- {key}: {a[key]}'])
    else:
      output.extend([f'- {key}: {a[key]}'])
      output.extend([f'+ {key}: {b[key]}'])

  return add, \
         change, \
         delete, \
         output
