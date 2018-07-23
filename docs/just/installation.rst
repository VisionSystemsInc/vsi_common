
#####################
J.U.S.T. Installation
#####################

``just`` be installed in two different ways

* `Source code <#from-source>`_ - Installing by source is ideal for developer who want to get the latest version or fix bugs and add features.

* `Executable <#executable>`_ - A single file version of ``just`` is wrapped up and ready to download

Requirements
------------

* ``bash`` 3.2 or newer. Designed to be compatible with Linux, Git for Windows, and macos out of the box with no additional dependencies
* Core utils (``sed``, ``awk``, etc...) that are already installed in any OS (or with Git for Windows on Windows)

From source
-----------

In order to use ``just`` from source, you need to add the submodule to your project repository

The ``just`` `wizard <https://raw.githubusercontent.com/VisionSystemsInc/vsi_common/master/linux/new_just>`_ will walk you threw this setup:

.. code-block:: bash

    curl -LO https://raw.githubusercontent.com/VisionSystemsInc/vsi_common/master/linux/new_just
    bash ./new_just

.. note::

    You can not run the script and download in one call, you must call new_just as a file, not a pipe stream. ``bash <(curl -Ls https://raw.githubusercontent.com/VisionSystemsInc/vsi_common/master/linux/new_just)`` will not work

Executable
----------

Download the latest release from `github <https://github.com/VisionSystemsInc/just/releases>`_ and put the executable on your path, and then you can start using ``just`` commands, such as the wizard: ``just --new``