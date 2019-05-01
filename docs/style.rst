
===========
Style Guide
===========

Bash
----

* Two spaces per indent

* ``then`` and ``do`` on the same line

.. code-block:: bash

    for x in $(ls); do
      :
    done

    while check_something; do
      :
    done

We like to use `>&` for file descriptors (numbers), and `&>` for filenames

* Redirecting to open file

.. code-block:: bash

    echo hi 1>&2 # No extra spaces, as bash doesn't allow that


* Closing an open file

.. code-block:: bash

    exec 3>&-

    exec 3&>- #Works, but wrong style. This is dealing with descriptors

* Redirecing to a file

.. code-block:: bash

    run_some_command &> /dev/null # Spaced added arround &>

    run_some_command >& /dev/null # Works, but wrong style

* Checking to see if a variable exists

.. code-block:: bash

    if [ -z "${variable+set}" ]; then # If not set
      do_something
    fi

    if [ -n "${variable+set}" ]; then # If set
      do_something
    fi

    if [ -z "${variable:+set}" ]; then # If (not set) or (set to null)
      do_something
    fi

    if [ -n "${variable:+set}" ]; then # If set and not null
      do_something
    fi

Python
------

* Two spaces per indent