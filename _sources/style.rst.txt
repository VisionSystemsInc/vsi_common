
========================
Contributing Style Guide
========================

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
     echo bye >&2 # No extra spaces

* Closing an open file

  .. code-block:: bash

     exec 3>&-

     exec 3&>- # WRONG style. This is dealing with descriptors

* Redirecting to a file

  .. code-block:: bash

     run_some_command &> /dev/null # Spaces added around &>

     run_some_command >& /dev/null # WRONG style. This is dealing with filenames

* Checking to see if a variable exists

  .. code-block:: bash

     if [ -z "${variable+set}" ]; then # If not set
       do_something
     fi

     if [ -n "${variable+set}" ]; then # If set
       do_something
     fi

     if [ -z "${variable:+set}" ]; then # If not set OR set to null
       do_something
     fi

     if [ -n "${variable:+set}" ]; then # If set AND not null
       do_something
     fi

* Scripting file naming and shebangs

  * Files that are only meant to be sourced should have a ``.bsh`` extension, and should have the following header:

    .. code:: bash

       #!/usr/bin/env false bash

       if [[ $- != *i* ]]; then
         source_once &> /dev/null && return 0
       fi

    * ``false`` signifies this file is for sourcing only. The ``bash`` at the end of the line tricks most editors into parsing the file as bash.

    * ``source_once`` is a component that will cause the file to only be sourced one time, even if other files attempt to source the file multiple times. This improves load time and debugging as the same files are not loaded multiple times. See :file:`source_once.bsh` for more information

  * Some files need to retain ``sh`` compatibility, and should have a ``.sh`` extension instead

  * Files that should be run as executable, should have 755 permissions and the following shebang:

    .. code:: bash

       #!/usr/bin/env bash

  * Files that can be sourced or executed should follow the same rules as executable scripts in addition to:

    * Most of the code should be contained in functions

    * The main function should have the same name as the file

    * The following footer should be used:

      .. code:: bash

         if [ "${BASH_SOURCE[0]}" = "${0}" ] || [ "$(basename "${BASH_SOURCE[0]}")" = "${0}" ]; then
           the_main_function_name "${@}"
           exit $?
         fi

      * This will only execute ``the_main_function_name`` when the script is being called, not sourced.

  * **Circular imports**: While :bash:func:`source_once.bsh source_once` will prevent some circular source issues, this does not help in interactive mode. :bash:func:`source_once.bsh source_once` is disabled in interactive mode because is someone changes a file, and sources it again, they should expect to get those changes, not have it "sourced only once ever" (it is also disabled for cnf speed reasons). Circular dependencies are handled using the :bash:func:`circular_source.bsh circular_source` function instead.

    .. code:: bash

       source something_normal.bsh
       source "${VSI_COMMON_DIR}/linux/circular_source.bsh"
       circular_source "${VSI_COMMON_DIR}/linux/docker_functions.bsh" || return 0

    * ``|| return 0`` makes it so that the current file is sourced the first time in the infinite loop, and stops the loop the second go around. Otherwise it might actually get sourced a total of two times, which is not detrimental but may have undesired effects (especially for CLI's)

* Coverage: bashcov can be used to create a coverage report. In order to designation a section of code as "no coverage", use ``# :nocov:`` before and after the code you want to not be reported on. There are additional flags for that can be excluded on macos (``:nocov_mac:``), Linux (``:nocov_linux:``), and Windows (``:nocov_nt:``). You can also designate an area to not be covered based on the version of bash: ``:nocov_bash_4.1:`` for no coverage on bash 4.1 and newer, or ``:nocov_lt_bash_4.4`` for no coverage on bash 4.4 and older. Multiple flags may be combined, where ``:nocov_nt: :nocov_bash_4.0:`` means no coverage on windows OR bash 4.0 or newer.

Python
------

* We use pep8, except two spaces per indent
* (Not yet implemented) Coverage: pycoverage is used to create a coverage report. A line or branch of code can be excluded by adding a comment that includes ``pragma: no cover``. An os specific pragma can be added, such as ``pragma: no linux cover`` for only on Windows, or ``pragma: no nt cover`` for only on mac and linux.

J.U.S.T. Plugins
----------------

* Just plugins that use docker-compose should specify the ``docker-compose.yml`` file with every command, to prevent unintended consequences in case the user sets ``COMPOSE_FILE``