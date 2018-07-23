
========
J.U.S.T.
========

.. module:: just

When working on a project, it often becomes necessary to run many long commands. Similar to how a makefile connects `targets` with a string of commands, `just` gives an easy way to create a set of targets to execute easily. Unlike a makefile, it has two key distinctions

* It's not a makefile. Bash is easier than make for simple tasks
* It works on Windows (when bash is installed via Git for Windows or similar), macOS (which uses bash 3.2) and Linux with no additional dependencies.

.. rubric:: Features

* Tab completion (:mod:`.just`)
* Comment generated help
* Subcommands
* Executing multiple targets in one call

.. seealso::

  :mod:`Justfile`
    Blah justfile

  :mod:`.just`
    Tab completion for bash

========
Justfile
========

.. module:: Justfile

The file sourced by just. The primary purpose of the Justfile is to define the function caseify. caseify should try to match ``$1`` and the number of additional arguments used should be added to extra_args

.. rubric:: Example

.. code-block:: bash

    #!/usr/bin/false
    source_environment_files "${CWD}/my_project_name.env"

    function caseify()
    {
      local just_arg=$1
      shift 1
      case ${just_arg} in
        foo) #ls foo files
          ls
          ;;
        two) # Target with two arguments
          echo $1 $2
          extra_args+=2
        group) # Two groups of args
          get_args ${@+"${@}"}
          echo ${args+"${args[@]}"}
          get_additional_args ${@+"${@}"}
          echo ${args+"${args[@]}"}
        # When a target starts with an _, it is hidden and is not included in
        # tab complete. It remains hidden from help unless a help comment is
        # added
        _hidden)
          ;;
        *)
          defaultify "${just_arg}" ${@+"${@}"}
          ;;
      esac
    }

.. function:: caseify(...)

Stuff

.. seealso::

  :func:`source_environment_files`
    Sources environment
  :func:`get_extra_args`
    Parses
  :data:`JUSTFILE`
    Sets :mod:`Justfile` filename to load