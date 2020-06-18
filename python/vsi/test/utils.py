from unittest import mock, TestCase as TestCaseOriginal
from unittest.util import safe_repr
import tempfile
from tempfile import (
  NamedTemporaryFile as NamedTemporaryFileOrig,
  TemporaryDirectory
)
import os
import sys
import types


class TestCase(TestCaseOriginal):
  '''
  TestCase class for common tests

  * Auto creates ``self.temp_dir``, a self deleting temporary directory for
    each test
  * Initialized ``self.patches`` to an empty list, so you can append patches
  * On ``setUp``, auto starts all ``self.patches``
  * On tearDown, auto stops all ``self.patches``

  .. rubric:: Example

  .. code-block:: python

      class TestSomething(vsi.test.utils.TestCase):
        def setUp(self):
          self.patches.append(mock.patch.object(settings, '_wrapped', None))
          super().setUp()
          settings.configure({'foo': 15})
        def test_something(self):
          print(self.temp_dir.name)
          self.assertEqual(settings.foo, 15)
  '''

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.patches = []
    self._temp_dir = None

  @property
  def temp_dir(self):
    '''
    Automatically creates a temporary directory for any unittest that needs it

    Cleanups automatically in :func:`tearDown`
    '''
    if self._temp_dir is None:
      self._temp_dir = TemporaryDirectory()
    return self._temp_dir

  def setUp(self):
    '''
    A basic setup that starts ``self.patches`` ``unittest.mock.patch`` objects

    A lot of the time, using the decorator is not possible as values are not
    available at load time that are needed for a patch
    '''
    for patch in self.patches:
      patch.start()

  def tearDown(self):
    '''
    Stops any patches in ``self.patches`` and cleanups up ``self.temp_dir``
    '''
    if self._temp_dir is not None:
      self._temp_dir.cleanup()
    while self.patches:
      self.patches.pop().stop()

  def assertExist(self, filename, msg=None, is_dir=None):
    '''
    Fails if the filename does not exist

    Can take an optional argument ``is_dir`` to assert that it is a directory
    or not. The default ``None`` does not check.
    '''
    if not os.path.exists(filename):
      msg = self._formatMessage(msg,
                                '%s does not exist' % (safe_repr(filename)))
      raise self.failureException(msg)

    if is_dir is not None:
      if is_dir:
        if not os.path.isdir(filename):
          msg = self._formatMessage(
              msg, '%s is not a directory' % (safe_repr(filename)))
          raise self.failureException(msg)
      elif os.path.isdir(filename):
        msg = self._formatMessage(
            msg, '%s is a directory' % (safe_repr(filename)))
        raise self.failureException(msg)

  def assertNotExist(self, filename, msg=None):
    '''
    Fails if the filename does not exist
    '''

    if os.path.exists(filename):
      msg = self._formatMessage(msg, '%s does exist' % (safe_repr(filename)))
      raise self.failureException(msg)


# https://stackoverflow.com/a/54653137/4166604
def make_traceback(depth=1):
  '''
  Create a phony traceback

  Useful for testing calls that need a traceback object, such as
  ``sys.excepthook``
  '''
  tb = None
  while True:
    try:
      frame = sys._getframe(depth)
      depth += 1
    except ValueError:
      break

    tb = types.TracebackType(tb, frame, frame.f_lasti, frame.f_lineno)

  return tb


def NamedTemporaryFileFactory(test_self):
  '''
  Mock function for NamedTemporaryFile that will create all temporary file in
  the test's ``temp_dir``.

  Example::

      >>> import tempfile
      >>> self.patches.append(mock.patch.object(tempfile, 'NamedTemporaryFile',
              NamedTemporaryFileFactory(self)))

  See Also
  --------
  TestCase : Test Case class with some bells and whistles.
  '''
  def NamedTemporaryFile(**kwargs):
    kwargs['dir'] = test_self.temp_dir.name
    rv = NamedTemporaryFileOrig(**kwargs)
    return rv
  return NamedTemporaryFile


class TestNamedTemporaryFileCase(TestCase):
  def setUp(self):
    self.patches.append(mock.patch.object(tempfile, 'NamedTemporaryFile',
                                          NamedTemporaryFileFactory(self)))
    super().setUp()
