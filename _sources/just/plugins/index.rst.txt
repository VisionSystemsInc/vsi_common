
.. _just-plugins:

================
J.U.S.T. Plugins
================

.. default-domain:: bash

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :glob:

   docker/index
   singularity/index
   *.auto

J.U.S.T. has a number of useful plugins included. A plugin is a ``bash`` script that can be sourced by a :file:`Justfile` and typically adds targets to :file:`just`

It's also pretty similar to add a plugin yourself. Similar to a :file:`Justfile`, but typically names ``just_{name}_functions.bsh``, and defines a modified :func:`Justfile caseify` that is instead names ``{name}_defaultify``

.. code-block:: bash
   :caption: just_example_functions.bsh

   if [[ $- != *i* ]]; then
     source_once &> /dev/null && return 0
   fi

   JUST_DEFAULTIFY_FUNCTIONS+=(example_defaultify)
   JUST_HELP_FILES+=("${BASH_SOURCE[0]}")

   function example_defaultify()
   {
     local just_arg=$1
     shift 1
     case $just_arg in
       example) # Just an example
         echo "Example plugin!"
         ;;
       *)
         plugin_not_found=1
         ;;
     esac
     return 0
   }

* First we prevent the file from being sourced multiple times with :file:`source_once.bsh`, purely for efficiency reasons
* We update :envvar:`JUST_DEFAULTIFY_FUNCTIONS` and :envvar:`JUST_HELP_FILES` so that the plugin is called, and parsed for :cmd:`just help`
* Then we dive into the plugin's defaultify (named uniquely for that plugin).
* And instead of calling :func:`just_functions.bsh defaultify` in the case's else, we set ``plugin_not_found=1`` instead. This is required so that other plugins can continue the search.

Now to use this new plugin, you simply add ``source "${VSI_COMMON_DIR}/linux/just_example_functions.bsh"`` (or similar) to your :file:`Justfile`

Most vsi_common plugins have docker images to support them. This requires a few more steps to setup

#. Create a new docker file in ``${VSI_COMMON_DIR}/docker/vsi_common/{name}.Dockerfile``. This Dockerfile usually needs to be setup like a :file:`new_just` Docker project's docker file, using vsi_common's entrypoint so that user permissions match.
#. Add the docker to ``${VSI_COMMON_DIR}/docker/vsi_common/docker-compose.yml``

  .. code-block:: yaml
     :caption: docker-compose.yml

     ...

       example:
         build:
           context: .
           dockerfile: example.Dockerfile
         image: ${EXAMPLE_IMAGE-vsiri/example:latest}
         environment:
           <<: *plugin_environment
           # Any custom env variables
           # EXAMPLE_VAR: value
           # EXAMPLE_COPY_VALUE: # This will auto copy the exported variable value EXAMPLE_COPY_VALUE
         volumes:
           - <<: *vsi_common_volume
           # Add any EXAMPLE dirs here
           # - type: bind
           #   source: ${EXAMPLE_SOURCE_DIR-}
           #   target: /src

3. Add some addition logic to ``{name}_defaultify`` to make calling docker easier

  .. code-block:: bash
     :caption: just_example_functions.bsh

     # ...
     function example_defaultify()
     {
       local id_project_cwd="${JUST_PROJECT_PREFIX}_CWD"

       # Export variables for docker-compose file
       local EXAMPLE_COPY_VALUE="${JUST_PROJECT_PREFIX}_EXAMPLE_COPY_VALUE"
       export EXAMPLE_COPY_VALUE="${!EXAMPLE_COPY_VALUE:-${!id_project_cwd}}"

       # These are part of the "plugin_environment" section
       local tmp="${JUST_PROJECT_PREFIX}_UID"
       local VSI_COMMON_UID="${!tmp-1000}"
       export VSI_COMMON_UID
       tmp="${JUST_PROJECT_PREFIX}_GIDS"
       local VSI_COMMON_GIDS="${!tmp-1000}"
       export VSI_COMMON_GIDS
       local JUST_SETTINGS="${JUST_PATH_ESC}/src/$(basename "${JUST_SETTINGS}")"
       export JUST_SETTINGS

       local COMPOSE_FILE="${VSI_COMMON_DIR}/docker/vsi_common/docker-compose.yml"
       export COMPOSE_FILE
     # ...