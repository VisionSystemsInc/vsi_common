
#####################
J.U.S.T. Installation
#####################

``just`` be installed in two different ways

* :ref:`just-install-source` - Installing by source is ideal for developer who want to get the latest version or fix bugs and add features.

* :ref:`just-install-exe` - A single file version of ``just`` is wrapped up and ready to download

Requirements
------------

* ``bash`` 3.2 or newer. Designed to be compatible with Linux, Git for Windows, and macos out of the box with no additional dependencies
* Core utils (``sed``, ``awk``, etc...) that are already installed in any OS (or with Git for Windows on Windows)

.. _just-install-source:

From source
-----------

In order to use ``just`` from source, you need to add the submodule to your project repository

The ``just`` `wizard <https://visionsystemsinc.github.io/vsi_common/new_just>`_ will walk you threw this setup:

.. code-block:: bash

    bash <(curl -Ls https://visionsystemsinc.github.io/vsi_common/new_just)

.. _just-install-exe:

Executable
----------

If you have a ``just`` executable on your path, simply run then you can start using ``just`` commands, such as the wizard: ``just --new``