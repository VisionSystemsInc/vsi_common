.. default-domain:: bash

==============
J.U.S.T. Files
==============

.. _just-Justfile-file:

--------
Justfile
--------

.. file:: Justfile

Your :file:`Justfile` is the main file sourced by just that defines a just project. The primary purpose of the Justfile is to define the function :func:`caseify`.

.. function:: caseify

:func:`caseify` is a user defined function that parses and handle one call (:ref:`just` will handle multiple calls by calling caseify multiple times for you, so you must not use a while loop and try to parse multiple calls). This should be done using a ``case`` statement, or else the :cmd:`just help` parsing will not identify targets correctly. If you choose not to use a ``case`` statement, comments in the form of ``# target) # Help text here`` can still be utilized to satisfy :cmd:`just help`'s parsing.

:func:`caseify` should try to match the first argument (``$1``) and keep count of the number of additional arguments used and stored the tally in ``extra_args``.

.. rubric:: Example

.. code-block:: bash
   :caption: Justfile

    #!/usr/bin/env bash

    if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then # If being sourced
      set -euE
    fi
    source "${VSI_COMMON_DIR}/linux/just_env" "$(dirname "${BASH_SOURCE[0]}")/cyclops.env"

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
          extra_args=2
          ;;
        # When a target starts with an _, it is hidden and is not included in
        # tab complete. It remains hidden from help unless a help comment is
        # added
        _hidden)
          echo Shhhhh
          ;;
        *)
          defaultify "${just_arg}" ${@+"${@}"}
          ;;
      esac
    }

    if ! command -v justify &> /dev/null; then caseify ${@+"${@}"};fi

.. seealso::

  :func:`just_functions.bsh source_environment_files`
    Sources environment
  :func:`just_functions.bsh get_args`
    Parses a block of arguments
  :func:`just_functions.bsh get_additional_args`
    Parses another block of arguments
  :cmd:`just help`
    Help test
  ``just JUSTFILE``
    Sets :file:`Justfile` filename to load

.. _just-setup-file:

.. file:: setup.env

The :file:`setup.env` is a necessary evil that must be sourced every time you start a terminal session. It mainly contains the relative location of the ``vsi_common`` repo and adds just to the path using that. It should look like:

.. code-block:: bash
   :caption: setup.env

   export JUST_SETUP_SCRIPT="$(basename "${BASH_SOURCE[0]}")"
   source "$(dirname "${BASH_SOURCE[0]}")/external/vsi_common/env.bsh"
   unset JUSTFILE

* The first line is a place holder for a feature that has yet to be created
* The third line fixes a bug when you are switching between projects and don't want to accidentally use the wrong Justfile. If you are using a custom Justfile, this would be the place to set it.
* The second line is the important line that sets up vsi_common on the path so that typing ``just`` works

.. _just-project-env-files:

-------------------------
Project Environment Files
-------------------------

A good :file:`Justfile` and just project should have no hard coded paths or values in it, but should work out of the box with their defaults. But if that's the case, the defaults need to come from somewhere, and a way to override those values locally need to go somewhere. These values come from the project environment files.

.. file:: project.env

Your default settings go in your project settings env file. Unlike the :file:`Justfile`, you are encouraged to customize the name of this file. The name of your settings file is passed to ``just_env`` in your :file:`Justfile` and is automatically stored in :envvar:`JUST_SETTINGS`. In the example above, you can see the name ``cyclops.env`` was used.

.. code-block:: bash
   :caption: cyclops.env

   # Required field
   JUST_PROJECT_PREFIX=CYCLOPS
   # Highly recommended field. Just uses this to detect changes in just version.
   JUST_VERSION="0.2.2"
   # Recommended field
   if [ -z "${CYCLOPS_CWD+set}" ]; then
     CYCLOPS_CWD="$(\cd "$(\dirname "${BASH_SOURCE[0]}")"; \pwd)"
   fi

There are three fields you should always define in just file

* :envvar:`JUST_PROJECT_PREFIX` - Designates that environment variables that start with this prefix are special to your project. Some of the advanced :ref:`just-plugins` use this for automatic features, and just will refuse to work without this being set.
* :envvar:`JUST_VERSION` is recommended so that just can detect when your :file:`Justfile` is behind in version, so you will get a warning to updated it before updating this version number.
* ``${JUST_PROJECT_PREFIX}_CWD`` - Some of the advanced :ref:`just-plugins` use this for automatic features, to know where the root of your source directory is.

After this, you are free to define any variables you like, provided they allow themselves to be overridden. A special feature of just is that all variables in this file are automatically exported for any command called by just. (Arrays are never exported because arrays simply cannot be exported to children processes). There is no need to ever says ``export CYCLOPS_HI_FILE``, since it is already exported. All you have to do is start setting variables to be overridable. The bash notation for variables vs arrays are different for this.

.. code-block:: bash
   :caption: cyclops.env continued

   # How to set variables
   : ${CYCLOPS_HI_FILE=${CYCLOPS_CWD}/hi.cpp}
   : ${CYCLOPS_UID=$(id -u)}

   # How to set arrays
   set_array_default CYCLOPS_ARCH x86_64 i686 arm6

Both notations mean "If this variable is not set, then set it to this value. In the case of the variable:

* The ``=`` expansion in bash means "If the variable name on the left is not set, then set the variable to the value on the right".
* The ``=`` expansion, like all expansions in bash, is returned as a "command" or "argument" to be executed. Well we want to neither execute the value of the variable nor pass it to a command. So we use the ``:`` character which is a shorthand for "true". So while this is like calling true with an argument that is ignored, this is a short and concise way to "set a variable if it doesn't exist.

Why was this notation not used for ``CYCLOPS_CWD`` above? Because in bash, the right hand side is always executed, and this can result in a time penalty, especially on Windows. Since those lines are autogenerated, they use the long form of checking.

There is no clean or easy way to do the same for arrays in bash, so the function :func:`just_functions.bsh set_array_default` is provided to accomplish the same thing, and handle all the corner cases. In this case: "If ``CYCLOPS_ARCH`` is unset, then it sets it to the 3 element array ``(x86_64 i686 arm6)``

There is no simple solution for associative arrays (because they are not bash 3.2 compatible) or noncontiguous arrays (because there has never been a need for that).

An additional pattern that is commonly added to the end of a project setting file, is when there are special "Non-project specific variables that executables you use" need. For example:

* ``PYTHONPATH`` - Let's say every call to python should have a special value for ``PYTHONPATH``, then it makes sense to add that to your settings file, but only if it should be every call to python.
* ``OMP_NUM_THREADS`` - Let's say you are running some multi-threaded code and needed to limit the number of threads, this too would make sense to add to the special end of settings section
* Etc... If the answers to "Is this a variable name I didn't make up?" and "Does it make sense to set this for every program I'm going to call?" are yes, then it would be appropriate to put it here.

.. code-block:: bash
   :caption: cyclops.env continued

   : ${CYCLOPS_THING1=15}

   ###############################################################################
   # Non-CYCLOPS Settings
   ###############################################################################

   : ${OMP_NUM_THREAD=8}
   : ${TZ=/usr/share/zoneinfo/UTC}
   : ${PYTHONPATH=${CYCLOPS_CWD}/python_code}

Some things you should never do in your settings file are:

* Output on standard error or standard out (except for debugging). It will just pollute the screen.
* Set variables without checking if they are set first, except for :envvar:`JUST_PROJECT_PREFIX` and :envvar:`JUST_VERSION`
* Be fast. While you are allowed and encouraged to do anything you can do in a bash script, if you intend on taking the md5sum of a 100GB file, maybe you want to rethink when that gets done instead of doing it always (i.e. move that to a specific :file:`Justfile` target).

.. file:: local.env

.. file:: local_post.env

If the project settings contain the default values, where do the the override values go? The answer is the :file:`local.env` file. If no :file:`local.env` file exists the first time you run just, an empty file is created for you. This is where you put the values for your "local install" of the the project. There is no need to use the same fancy notation (unless you want to make them overridable by exported variables from the terminal).

.. code-block:: bash
   :caption: local.env

   TZ=/usr/share/zoneinfo/EST
   OMP_NUM_THREAD=2

The :file:`local.env` is loaded before the  project settings env file is loaded, so it is impossible to use any values evaluated in it. This is usually not a problem, but in those uncommon cases, that is why there is a :file:`local_post.env` file. This file is used so rarely, that is not created for you by default, you'll just need to create the empty file yourself.

.. code-block:: bash
   :caption: local_post.env

   CYCLOPS_HI_FILE="${CYCLOPS_CWD}/hi2.cpp"

Now :file:`local_post.env` is run after the project settings env file is loaded, so if you changed ``CYCLOPS_CWD``, any variable using its default value derived from ``CYCLOPS_CWD`` (e.g. ``PYTHONPATH``) will not have a changed value. You will either need to set the value in the :file:`local.env` file, or re-set every variable that derived from it in the :file:`local_post.env`. Usually this is never an issue.

It is suggested to use the default names for the local env files, however they can be set to custom names using the :ref:`JUST_LOCAL_SETTINGS <source_environment_files>` and :ref:`JUST_LOCAL_SETTINGS_POST <source_environment_files>` variable. These will need to either be exported in :file:`setup.env` (or even somewhere like your .bashrc, depending on your use case) or set in :file:`Justfile`.

.. note::

   The :file:`local.env` and :file:`local_post.env` should never be committed to a repository. They are part of your specific configuration. Like-wise you should not be editing the project default settings env file just to customize a project on your specific computer, that should always go in the :file:`local.env`/:file:`local_post.env` files.

---------------
Advanced setups
---------------

Chaining a multiple Justfiles
-----------------------------

Chaining a multiple Justfiles (usually using a submodule)


The main function in just is :func:`Justfile caseify`, and there can only be one. The current solution to this is to make the main repo contain the :func:`Justfile caseify` function, and treat the submodule as a :ref:`just plugin <just-plugins>`.

.. code-block:: bash
   :caption: Submodule Justfile

   #!/usr/bin/env bash

   source "${VSI_COMMON_DIR}/linux/just_env" "$(dirname "${BASH_SOURCE[0]}")"/'monocle.env'


   # Make monocle's justfile a plugin if it is not the main Justfile
   if [ "${JUSTFILE}" != "${BASH_SOURCE[0]}" ]; then
     JUST_HELP_FILES+=("${BASH_SOURCE[0]}")
   else
     cd "${MONOCLE_CWD}"
     # Allow monocle to be run as a non-plugin too
     function caseify()
     {
       defaultify ${@+"${@}"}
     }
   fi

   # Always add this to the list, because of how the caseify above works
   JUST_DEFAULTIFY_FUNCTIONS+=(monocle_caseify)

   # Main function
   function monocle_caseify()
   {
     local just_arg=$1
     shift 1
     case ${just_arg} in
       sometarget) # Do something
         ls
         ;;
       # ...
       *)
         plugin_not_found=1
         ;;
     esac
     return 0
   }

As you can see, the only thing that differentiates this from a plugin is a special if statement that will define :func:`Justfile caseify` when it's not already defined.


