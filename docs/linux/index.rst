
===============
Linux Utilities
===============

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :glob:

   *.auto
   python_scripts/modules

A set of useful linux scripts that should be on any modern Linux machine. For the most part, these are bash scripts that are either pure bash or rely on core Linux utils. These scripts are tested against a variety of Linuxes, macOS, and Windows using msys2/mingw64 (such as Git for Windows). And scripts that require something beyond these core and common utils should have these requirements called in their documentation.

Used core utils include:

* ``basename``
* ``cat``
* ``cp``
* ``cut``
* ``date``
* ``df``
* ``dirname``
* ``env``
* ``false``
* ``fold``
* ``head``
* ``id``
* ``ln``
* ``ls``
* ``mkdir``
* ``mktemp``
* ``mkfifo``
* ``pwd``
* ``rm``
* ``sort``
* ``tail``
* ``test``
* ``tr``
* ``true``
* ``touch``
* ``xargs``

In addition to other commonly included tools:

* ``awk``
* ``column`` (if available)
* ``getent`` (Linux only)
* ``grep``
* ``mount``
* ``pgrep`` (if available)
* ``ps``
* ``sed``
* ``tput`` (This should be moved to docs for specific function, not in this list)

.. note::

   Busybox based operating systems have a version of ``awk`` and ``sed`` that is not fully compatible. In a few cases, the GNU version is needed over the Busybox version. The BSD version will also work.
