.. default-domain:: bash

==============
J.U.S.T. Files
==============

.. _just-Justfile-file:

.. file:: Justfile

The file sourced by just. The primary purpose of the Justfile is to define the function caseify. caseify should try to match ``$1`` and the number of additional arguments used should be added to extra_args

.. rubric:: Example

.. code-block:: bash

    #!/usr/bin/env bash

    if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then # If being sourced
      set -euE
    fi
    source "${VSI_COMMON_DIR}/linux/just_env" "$(dirname "${BASH_SOURCE[0]}")"/project.env
    cd "${PROJECT_CWD}"


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

    if ! command -v justify &> /dev/null; then caseify ${@+"${@}"};fi

.. seealso::

  :func:`source_environment_files <just_functions.bsh source_environment_files>`
    Sources environment
  :func:`get_args <just_functions.bsh get_args>`
    Parses a block of arguments
  :func:`get_additional_args <just_functions.bsh get_additional_args>`
    Parses another block of arguments
  :cmd:`just help`
    Help test
  :env:`JUSTFILE <just JUSTFILE>`
    Sets :file:`Justfile` filename to load

.. _just-project-env-files:

.. _just-setup-file:

.. _just-wrap:
