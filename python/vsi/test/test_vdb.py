import unittest

import warnings

class GlobTest(unittest.TestCase):
  def test_import(self):
    with warnings.catch_warnings():
      warnings.filterwarnings("ignore", category=DeprecationWarning,
                              module='rpdb2')

      import vsi.tools.vdb
      import vsi.tools.vdb_rpdb2
      import vsi.tools.vdb_rpdb
