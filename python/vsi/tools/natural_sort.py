# from Christoph Gohlke's tifffile.py of all places
import re

def natural_sorted(iterable):
    """Return human sorted list of strings.

    >>> natural_sorted(['f10', 'f2', 'f1'])
    ['f1', 'f2', 'f10']

    """
    def sortkey(x):
        return [(int(c) if c.isdigit() else c) for c in re.split(numbers, x)]
    numbers = re.compile('(\d+)')
    return sorted(iterable, key=sortkey)

