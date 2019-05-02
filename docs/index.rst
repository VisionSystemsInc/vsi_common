.. VSI Common documentation master file, created by
   sphinx-quickstart on Sun Jul 22 15:19:18 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

VSI Common documentation
========================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   just/index
   linux/index
   windows/index
   tests/index
   python/modules
   style.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

VSI Common is a set of tools and scripts that are not specific to any project, but useful to have on any project. The most significant of these tools being :ref:`just`.

.. envvar:: VSI_COMMON_DIR

  The location of the root of the VSI common code repository. Most scripts will determine :envvar:`VSI_COMMON_DIR` automatically, and use it to find other scripts in VSI Common. :envvar:`VSI_COMMON_DIR` is almost always overrideable, should you need to reference a different location/version of VSI Common.