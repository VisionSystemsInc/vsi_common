#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then #If being sourced
  set -euE
fi

JUST_PROJECT_PREFIX=VSI_COMMON
source "$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd)/wrap"
cd "$(\dirname "${BASH_SOURCE[0]}")"

source "${VSI_COMMON_DIR}/linux/just_robodoc_functions.bsh"

function caseify()
{
  local just_arg=$1
  shift 1
  case ${just_arg} in
    test) # Run unit and integration tests
      "${VSI_COMMON_DIR}/tests/run_tests.bsh" ${@+"${@}"}
      extra_args+=$#
      ;;
    test_darling) # Run unit and integration tests using darline
        (
          cd "${VSI_COMMON_DIR}"
          env -i HOME="${HOME}" darling shell ./tests/run_tests.bsh ${@+"${@}"}
        )
        extra_args+=$#
      ;;
    run_wine) # Start a wine bash window
      docker run -it --rm --privileged \
                 -e VSI_COMMON_IS_POWERSHELL=1 \
                 -v "${VSI_COMMON_DIR}":/root/.wine/drive_c/vsi_common \
                 -w /root/.wine/drive_c/vsi_common \
                 vsiri/wine_msys64
      ;;
    run_wine-gui) # Start a wine bash window in gui mode
      docker run --rm --privileged -e DISPLAY -e USER_ID="$(id -u)"\
                 -e VSI_COMMON_IS_POWERSHELL=1 \
                 -v /tmp/.X11-unix:/tmp/.X11-unix \
                 -v "${VSI_COMMON_DIR}":/root/.wine/drive_c/vsi_common \
                 -w /root/.wine/drive_c/vsi_common \
                 vsiri/wine_msys64 &
      ;;
    test_wine)
      docker run -it --rm --privileged \
                 -e VSI_COMMON_IS_POWERSHELL=1 \
                 -v "${VSI_COMMON_DIR}":/root/.wine/drive_c/vsi_common \
                 -w /root/.wine/drive_c/vsi_common \
                 vsiri/wine_msys64 -c \
                 "cd /root/.wine/drive_c/vsi_common
                  . setup.env
                  just test ${*}
                  read -p 'Press any key to close' -r -e -n1"
      extra_args+=$#
      ;;
    *)
      defaultify "${just_arg}" ${@+"${@}"}
      ;;
  esac
}

if [ "${JUST_IN_SCRIPT-0}" == "0" ]; then caseify ${@+"${@}"};fi
