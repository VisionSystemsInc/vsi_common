# from Christoph Gohlke's tifffile.py of all places, with modifications

import re

def natural_sorted(iterable, key=None, *args, **kwargs):
    """Return sorted list of strings according to (sub)string numerical value.

    >>> natural_sorted(['f10', 'f2', 'f1'])
    ['f1', 'f2', 'f10']

    >>> natural_sorted([('f10',2), ('f2',5), ('f1',1), ('f1a',3)], key=lambda x: x[0])
    [('f1', 1), ('f1a', 3), ('f2', 5), ('f10', 2)]
    """
    if key is None: key = lambda x: x

    def sortkey(x):
        return [(int(c) if c.isdigit() else c) for c in re.split(numbers, key(x))]
    numbers = re.compile('(\d+)')
    return sorted(iterable, key=sortkey, *args, **kwargs)
