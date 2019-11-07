#!/usr/bin/env bash

set -eu

#*# just/plugins/docker/just_entrypoint

#**
# .. default-domain:: bash
#
# ===================
# J.U.S.T. Entrypoint
# ===================
#
# .. file:: just_entrypoint.sh
#
# .. note::
#    This is the default entrypoint for J.U.S.T. projects. By default, docker entrypoint runs as root, which can introduce a number of obstacles and undesired side effects. Hard coding user information into images is slow and limited. :file:`just_entrypoint.sh` will setup everything needed to dynamically make the user inside the container have your desired ids (by default by querying your ids on the host).
#
# The entrypoint is designed to take care of 5 major problems for you
#
# #. Creating a user with the right UID/GID
# #. Fix NFS mounts to work with nfs mounts with squash root enabled. (Does not currently support kerberos auth)
# #. Fix initial permissions of internal volumes
# #. Remove project environment variables ending in ``_DOCKER``
# #. Remove ``//`` from the begining of environment variables to handle the mingw/cygwin expansion workaround
#
# Here's a walkthrough of how the entrypoint runs:
#
# #. The entrypoint starts running as ``root``
# #. Loads the just environment only for root according to :envvar:`JUST_SETTINGS`. These values will be removed by the time the entrypoint is executeds as the user below, to prevent unexpected variable corruption.
# #. Runs :func:`just_entrypoint_functions docker_setup_user` to set up the user with the appropriate ids. This is superior to other methods that would build an image with a UID and GID embedded in it, since you do not need to rebuild the image to have it adapt to your ids. Furthermore, it will capture all your gids by default, working correctly in more corner cases.
# #. Runs :func:`just_entrypoint_functions docker_link_mounts` in conjuntion with :func:`docker_functions.bsh Just-docker-compose` to create symlinks where nfs mounts should appear, in the case that nfs is used. :func:`docker_functions.bsh Just-docker-compose` will identify nfs mounts, and mount the root of an nfs mount point in case squash_root is used and set ``JUST_DOCKER_ENTRYPOINT_LINKS``. :func:`just_entrypoint_functions docker_link_mounts` uses the information encoded in ``JUST_DOCKER_ENTRYPOINT_LINKS`` to create symlink where there were originally supposed to be mounted.
# #. Runs :func:`just_entrypoint_functions docker_setup_data_volumes` to fix initial permission issues for internal data volumes. When an empty internal data is initially created by docker, the folder is owned and writeable by root. This changes it to match the desired user's permissions. :func:`docker_functions.bsh Just-docker-compose` automaticlly determines the list of internal data volumes and passes them in as ``JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES``, which is then passes into :func:`just_entrypoint_functions docker_setup_data_volumes` as ``JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS`` and ``JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS``
#
#   * ``JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS`` - recursively chowns all the files in the volumes listed to match the user. This could be slow with many files, but it only executes when the volumes permissions are bad, typically only first time the container is started. If you need to customized/disable this feature, pass the environment variable ``JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS`` into the container, and it will override the default of using ``JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES``.
#   * ``JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS`` - non-recursively chmod the directories listed to 777 so that any initial ownership issues are avoided. Can also be customized/disabled by passing a value in for the ``JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS`` line, but being non-recursive, this should never have a noticeable time penalty.
#   * These two features give volumes a much more desirable default behavior for non-root users.
#
# 6. Next the entrypoint (and everything else from here on) is re-executed as the user that was created in :func:`just_entrypoint_functions docker_setup_user`. If you need to give the user root privliges, the suggested method is to use ``gosu``. Giving ``gosu`` ``chmod u+s /usr/local/bin/gosu`` permissions will accomplish this, but should not be suggested for deployment situations.
# #. Loads the just environment for the user accoring to :envvar:`JUST_SETTINGS`.
# #. If :envvar:`JUSTFILE` is set, runs :func:`just_entrypoint_user_functions filter_docker_variables` to remove project variables ending in ``_DOCKER``
# #. Replace ``//`` with `/` in project variables if running on windows using mingw or cygwin. Cygwin-like systems have a habit of `expanding variables <http://mingw.org/wiki/Posix_path_conversion>`_. Extra slashes are added in project environment files using :envvar:`JUST_PATH_ESC`, which cygwin-like systems evaluate as a ``/``, else empty. An unfortunate side effect of this is the `//` is still in the container. While this is usually harmeless, there are cases when the extra slash in the variables cause code to crash.
# #. If :envvar:`JUSTFILE` was passed in, this signifies to the entrypoint that an internal just call will be used. This means ``just`` is prepended to the command to ``exec``, so you don't have to.
# #. If :envvar:`JUSTFILE` is not set, the command arguments are run using ``exec``
#
# The function ``sudo`` that calls ``gosu`` is also exported, for ease of use.
#
# If you have your own entrypoint point you want to daisy-chain with the just entrypoint, changing the ``ENTRYPOINT`` field in the docker file will allow this
#
# .. code-block:: dockerfile
#
#    ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env",
#                "bash", "/vsi/linux/just_entrypoint.sh",
#                "bash", "/my_entrypoint.sh"]
#
#    CMD some_command
#
# If a project needs to customize the behavior more than is possible, the developer is encouraged to copy the original file into their project, customize it, add it to the image, and that entrypoint instead of the one in vsi_common
#
# .. literalinclude:: just_entrypoint.auto.sh
#    :language: bash
#
# :Parameters: * :envvar:`JUST_SETTINGS` - Location of project env settings file.
#              * :envvar:`VSI_COMMON_DIR` - Optional, location of VSI dir, defaults to /vsi
# :Internal Use: * ``ALREADY_RUN_ONCE`` - Tracks if entrypoint has already sudoed to user.
#                * ``JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES`` - Passed from :func:`docker_functions.bsh Just-docker-compose`
#**

: ${VSI_COMMON_DIR=/vsi}

if [ -n "${SINGULARITY_NAME+set}" ]; then
  # Disable the special docker magic in singularity
  export ALREADY_RUN_ONCE=1
fi

if [ "${ALREADY_RUN_ONCE+set}" != "set" ]; then
  # create the user and associated groups and handle nfs symlinks

  (
    # TODO: This will not source local.env if the src directory were on an nfs
    # Not sure ADDing the local files in the Dockerfile is the "right" solution
    source "${VSI_COMMON_DIR}/linux/just_env" "${JUST_SETTINGS-/dev/null}"
    # Setup the container to be more friendly to non-root users and
    # add other advanced J.U.S.T. features
    JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS="${JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS-${JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES-}}" \
    JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS="${JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS-${JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES-}}" \
    /usr/bin/env bash "${VSI_COMMON_DIR}/linux/just_entrypoint_functions"
  )


  if [ -n "${BASH_SOURCE+set}" ]; then
    file="${BASH_SOURCE[0]}"
  else
    file="${0}" #sh compatibility
  fi

  # Rerun entrypoint as user now, (skipping the root part via ALREADY_RUN_ONCE)
  ALREADY_RUN_ONCE=1 exec gosu ${DOCKER_USERNAME} /usr/bin/env bash "${file}" ${@+"${@}"}
fi


function sudo()
{
  gosu root ${@+"${@}"}
}
export -f sudo

if [ -n "${JUSTFILE+set}" ]; then
  run_just=1
else
  run_just=0
fi

source "${VSI_COMMON_DIR}/linux/just_env" "${JUST_SETTINGS-/dev/null}"

# Remove _DOCKER variables and undo // expansion
source "${VSI_COMMON_DIR}/linux/just_entrypoint_user_functions"
if [ -n "${JUST_PROJECT_PREFIX+set}" ]; then
  # Remove duplicate ${JUST_PROJECT_PREFIX}_*_DOCKER variables
  filter_docker_variables
fi
docker_convert_paths

if [ "${run_just}" = "1" ]; then
  exec /vsi/linux/just "${@}"
else
  exec "${@}"
fi