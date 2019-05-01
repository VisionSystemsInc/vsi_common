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
# In an attempt to con
#
# .. literalinclude:: just_entrypoint.auto.sh
#    :language: bash
#**

# Note:
# -----
# This is the default entrypoint sources for J.U.S.T. projects. If a project
# needs to customize the behavior (specifically parts dealing with
# just_entrypoint_functions), then the developer should copy this file into
# their project, customize it, and add it to the image.

# Parameters
# JUST_SETTINGS - Location of project env settings file.
# VSI_COMMON_DIR - Optional, location of VSI dir, default /vsi
# Internal use
# ALREADY_RUN_ONCE
# JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES

# - JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS - automatically chown all files in the
#   volumes listed to match the user. This could be slow with many files, but
#   it only executes when the volumes permissions are bad. If you don't
#   need this feature, save time by removing the
#   JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS line, but leave rest.
# - JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS - non-recursively chmod the directories
#   listed to 777 so that any initial ownership issues are avoided. Can also
#   be disabled by removing the JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS line
# These two features give volumes a much more desirable default behavior for
# non-root users. Add any other custom behavior here.

: ${VSI_COMMON_DIR=/vsi}

if [ "${ALREADY_RUN_ONCE+set}" != "set" ]; then
  # create the user and associated groups and handle nfs symlinks

  (
    # TODO: This will not source local.env if the src directory were on an nfs
    # Not sure ADDing the local files in the Dockerfile is the "right" solution
    source "${VSI_COMMON_DIR}/linux/just_env" "${JUST_SETTINGS-/dev/null}"
    # Setup the container to be more friendly to non-root users and
    # add other advanced J.U.S.T. features
    JUST_DOCKER_ENTRYPOINT_CHOWN_DIRS="${JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES-}" \
    JUST_DOCKER_ENTRYPOINT_CHMOD_DIRS="${JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES-}" \
    /usr/bin/env bash "${VSI_COMMON_DIR}/linux/just_entrypoint_functions.bsh"
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

source "${VSI_COMMON_DIR}/linux/docker_functions.bsh"
if [ -n "${JUST_PROJECT_PREFIX+set}" ]; then
  # Remove duplicate ${JUST_PROJECT_PREFIX}_*_DOCKER variables
  filter_docker_variables
fi
docker_convert_paths

if [ "${run_just}" = "1" ]; then
  exec just "${@}"
else
  exec "${@}"
fi