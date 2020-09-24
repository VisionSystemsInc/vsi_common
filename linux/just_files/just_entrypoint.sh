#!/usr/bin/env sh

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
#    This is the default entrypoint for J.U.S.T. projects. By default, the docker entrypoint runs as root, which can introduce a number of obstacles and undesired side effects. Hard coding user information into images is slow and limited. :file:`just_entrypoint.sh` will setup everything needed to dynamically make the user inside the container have your desired ids (by default, by querying your ids on the host).
#
# The entrypoint is designed to take care of 5 major problems for you
#
# #. Creating a user with the right UID/GID such that
#
#   * Files created in directories (volumes) mounted from the host will have the correct permissions
#   * The container, if given access to the X11 daemon, will be allowed to draw windows (e.g., display figures)
#
# #. Fix initial permissions of internal volumes
# #. Workaround NFS mounts when squash root is enabled. (Does not currently support kerberos auth)
# #. Remove project environment variables ending in ``_DOCKER``
# #. Remove ``//`` from the beginning of environment variables to handle the mingw/cygwin expansion workaround
#
# Here's a walkthrough of how the entrypoint runs:
#
# #. The entrypoint starts running as ``root``
# #. Loads the just environment for root according to :envvar:`JUST_SETTINGS`. These variables will be removed by the time the entrypoint is executed as the user below, to prevent unexpected variable corruption.
# #. Any files in :envvar:`JUST_ROOT_PATCH_DIR` will be executed (in alphabetical order) if they have the execute flag set, else they are sourced.
# #. Runs :func:`just_entrypoint_functions docker_setup_user` to set up the user with the appropriate ids. This is superior to other methods that would build an image with a UID and GID embedded in it, since you do not need to rebuild the image to have it adopt a different id. Furthermore, it will capture *all* your gids by default, which allows more corner cases to work correctly.
# #. In the case that nfs is used, runs :func:`just_entrypoint_functions docker_link_mounts` in conjunction with :func:`docker_functions.bsh Just-docker-compose` to create symlinks where nfs mounts should appear. First, :func:`docker_functions.bsh Just-docker-compose` will identify nfs mounts and mount the root of an nfs mount point (assuming squash_root is typically enabled) to a secondary location, and add the mount point to ``JUST_DOCKER_ENTRYPOINT_LINKS``. Then, :func:`just_entrypoint_functions docker_link_mounts` uses the information encoded in ``JUST_DOCKER_ENTRYPOINT_LINKS`` to create symlinks to the nfs subdirectories in the locations they were originally supposed to be mounted.
# #. Runs :func:`just_entrypoint_functions docker_setup_data_volumes` to fix initial permission issues for internal data volumes. When an empty internal data volume is initially created by docker, the folder is owned and writable by root. This changes the folder to match the desired user's permissions. :func:`docker_functions.bsh Just-docker-compose` automatically determines the list of internal data volumes and passes them in as ``JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES``, which it then passes into :func:`just_entrypoint_functions docker_setup_data_volumes` as ``JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS`` and ``JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS``
#
#   * ``JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS`` - recursively chowns all the files in the volumes listed to match the user. This could be slow with many files, but it only executes when the volumes permissions are bad, typically only the first time the container is started. If you need to customized/disable this feature, set and pass the environment variable ``JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS`` into the container to specify which directories to chown. This will override the default of ``JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES``.
#   * ``JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS`` - non-recursively chmod the directories listed to 777 so that any initial ownership issues are avoided. Can also be customized/disabled by passing a value in for ``JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS``, but being non-recursive, this should never have a noticeable time penalty.
#   * These two features give volumes a much more desirable default behavior for non-root users.
#
# 7. Next, the entrypoint (and everything else from here on) is re-executed as the user that was created in :func:`just_entrypoint_functions docker_setup_user`. If you need to give the user root privileges, the suggested method is to give ``gosu`` special permissions (``chmod u+s /usr/local/bin/gosu``) and use ``gosu root {command}``. However, this is not suggested when deploying.
# #. Loads the settings for the project/user according to :envvar:`JUST_SETTINGS`.
# #. If :envvar:`JUST_PROJECT_PREFIX` is set, runs :func:`just_entrypoint_user_functions.bsh filter_docker_variables` to remove project variables ending in ``_DOCKER``. This can be disabled by setting ``JUST_FILTER_DOCKER`` to ``0``
# #. Replace ``//`` with `/` in project variables if running on Windows using mingw or cygwin. Cygwin-like systems have a habit of `expanding variables <http://mingw.org/wiki/Posix_path_conversion>`_. Extra slashes are added in project environment files using :envvar:`JUST_PATH_ESC`, which cygwin-like systems evaluate as a ``/``, else empty. An unfortunate side effect of this is the `//` is still in the container. While this is usually harmless, there are cases when the extra slash in the variables cause code to crash.
# #. Any files in :envvar:`JUST_USER_PATCH_DIR` will be executed if they have the execute flag set, else they are sourced.
# #. If :envvar:`JUSTFILE` was passed in, this signifies to the entrypoint that an internal just call will be used. This means ``just`` is prepended to the command to ``exec``, so you don't have to.
# #. If :envvar:`JUSTFILE` is not set, the command arguments are run using ``exec``
#
# The function ``sudo`` that calls ``gosu`` is also exported, for ease of use.
#
# If you have your own entrypoint that you want to daisy-chain with the just entrypoint, changing the ``ENTRYPOINT`` field in the docker file will allow this.
#
# .. code-block:: dockerfile
#
#    ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env",
#                "bash", "/vsi/linux/just_files/just_entrypoint.sh",
#                "bash", "/my_entrypoint.sh"]
#
#    CMD some_command
#
# If a project needs to customize the behavior more than is possible, the developer is encouraged to copy the original file into their project, customize it, add it to the image, and call that entrypoint instead of the one in vsi_common.
#
# .. literalinclude:: just_entrypoint.auto.sh
#    :language: bash
#
# :Parameters: * :envvar:`JUST_SETTINGS` - Location of project env settings file.
#              * :envvar:`VSI_COMMON_DIR` - Optional, location of VSI dir, defaults to /vsi
#              * ``DOCKER_USERNAME`` - Optional, username for new user, defaults to user
# :Internal Use: * ``ALREADY_RUN_ONCE`` - Tracks if entrypoint has already sudo'd to user.
#                * ``JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES`` - Passed from :func:`docker_functions.bsh Just-docker-compose`
#
# .. envvar:: JUST_ROOT_PATCH_DIR
#
# :file:`just_entrypoint.sh` will source or execute (if the execute bit is set) every file in this directory as root on container start. In singularity, this step is skipped. The default is: ``/usr/local/share/just/root_run_patch``.
#
# .. envvar:: JUST_USER_PATCH_DIR
#
# :file:`just_entrypoint.sh` will source or execute (if the execute bit is set) every file in this directory as the user on container start. The default is: ``/usr/local/share/just/user_run_patch``
#
# .. note::
#
#    The intended use of :envvar:`JUST_ROOT_PATCH_DIR` and :envvar:`JUST_USER_PATCH_DIR` is to add files to them from either docker recipes or in the Dockerfile. While you can mount a folder or volume to this location, that is not the intent. For example, on Windows all files may appear to have execute permissions, which may not be what you want.
#**

: ${VSI_COMMON_DIR=/vsi}
: ${DOCKER_USERNAME=user}

source "${VSI_COMMON_DIR}/linux/elements.bsh"

# Disable the special docker magic except in docker, no need in singularity
# TODO: what does podman need?
if [ -d /.singularity.d ] || [ ! -f "/.dockerenv" ] || [ "$(id -u)" != "0" ]; then
  export ALREADY_RUN_ONCE=1
fi

function load_just_settings()
{
  local JUST_SETTINGSS
  local just_settings

  MIFS="${JUST_SETTINGS_SEPARATOR-///}" split_s JUST_SETTINGSS ${JUST_SETTINGS+"${JUST_SETTINGS}"}
  for just_settings in ${JUST_SETTINGSS[@]+"${JUST_SETTINGSS[@]}"}; do
    source "${VSI_COMMON_DIR}/linux/just_files/just_env" "${just_settings}"
  done
}

if [ "${ALREADY_RUN_ONCE+set}" != "set" ]; then

  if [ -n "${BASH_SOURCE+set}" ]; then
    file="${BASH_SOURCE[0]}"
  else
    file="${0}" # sh compatibility
  fi

  (
    # TODO: This will not source local.env if the src directory were on an nfs
    # Not sure ADDing the local files in the Dockerfile is the "right" solution
    load_just_settings

    # Sorted: https://serverfault.com/a/122743/321910
    for patch in "${JUST_ROOT_PATCH_DIR-/usr/local/share/just/root_run_patch}"/*; do
      if [ -x "${patch}" ]; then
        "${patch}"
            # https://www.endpoint.com/blog/2016/12/12/bash-loop-wildcards-nullglob-failglob
            # check -e incase glob doesn't expand
      elif [ -e "${patch}" ]; then
        source "${patch}"
      fi
    done

    # Create the user and associated groups and handle nfs symlinks
    # Setup the container to be more friendly to non-root users and
    # add other advanced J.U.S.T. features
    JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS="${JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS-${JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES-}}" \
    JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS="${JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS-${JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES-}}" \
    /usr/bin/env bash "${VSI_COMMON_DIR}/linux/just_files/just_entrypoint_functions"
  )
  # Rerun entrypoint as user now, (skipping the root part via ALREADY_RUN_ONCE)
  ALREADY_RUN_ONCE=1 exec gosu ${DOCKER_USERNAME} /usr/bin/env bash "${file}" ${@+"${@}"}
fi

function sudo()
{
  gosu root ${@+"${@}"}
}
export -f sudo

if [ -n "${JUSTFILE:+set}" ]; then
  run_just=1
else
  run_just=0
fi

load_just_settings

# Remove _DOCKER variables and undo // expansion
source "${VSI_COMMON_DIR}/linux/just_files/just_entrypoint_user_functions.bsh"
if [ -n "${JUST_PROJECT_PREFIX+set}" ]; then
  # Remove duplicate ${JUST_PROJECT_PREFIX}_*_DOCKER variables
  filter_docker_variables
fi
docker_convert_paths

for patch in "${JUST_USER_PATCH_DIR-/usr/local/share/just/user_run_patch}"/*; do
  if [ -x "${patch}" ]; then
    "${patch}"
          # https://www.endpoint.com/blog/2016/12/12/bash-loop-wildcards-nullglob-failglob
          # check -e incase glob doesn't expand
  elif [ -e "${patch}" ]; then
    source "${patch}"
  fi
done

# Unexport it
unset shell

if [ "${run_just}" = "1" ]; then
  exec "${VSI_COMMON_DIR}/linux/just" "${@}"
else
  exec "${@}"
fi