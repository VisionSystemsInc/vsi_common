#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then #If being sourced
  set -euE
fi

JUST_PROJECT_PREFIX=VSI_COMMON
VSI_COMMON_WINE_TEST_IMAGE=vsi_wine_test
VSI_COMMON_WINE_TEST_VOLUME=vsi_common_wine_home

source "$(\cd "$(\dirname "${BASH_SOURCE[0]}")"; \pwd)/wrap"
cd "$(\dirname "${BASH_SOURCE[0]}")"

source "${VSI_COMMON_DIR}/linux/just_robodoc_functions.bsh"

function caseify()
{
  local just_arg=$1
  shift 1
  case ${just_arg} in
    test) # Run unit tests
      "${VSI_COMMON_DIR}/tests/run_tests.bsh" ${@+"${@}"}
      extra_args+=$#
      ;;
    testint) # Run integration tests
      TESTS_DIR=int "${VSI_COMMON_DIR}/tests/run_tests.bsh" ${@+"${@}"}
      extra_args+=$#
      ;;
    test_darling) # Run unit tests using darling
      (
        cd "${VSI_COMMON_DIR}"
        env -i HOME="${HOME}" darling shell ./tests/run_tests.bsh ${@+"${@}"}
      )
      extra_args+=$#
      ;;
    build_wine) # Build wine image
      (
        cd "${VSI_COMMON_DIR}/docker/tests"
        docker build -t "${VSI_COMMON_WINE_TEST_IMAGE}" -f wine.Dockerfile .
      )
      ;;
    run_wine) # Start a wine bash window
      docker run -it --rm --cap-add=SYS_PTRACE \
                 -e USER_ID="$(id -u)" \
                 -e VSI_COMMON_IS_POWERSHELL=1 \
                 -e WINEDEBUG=fixme-all,err-winediag,err-menubuilder \
                 -v "${VSI_COMMON_WINE_TEST_VOLUME}:/home/.user_wine" \
                 -v "${VSI_COMMON_DIR}":/vsi_common:ro \
                 -w /vsi_common \
                 "${VSI_COMMON_WINE_TEST_IMAGE}" -c "cd /z/vsi_common; bash -l"
      ;;
    run_wine-gui) # Start a wine bash window in gui mode
      docker run --rm --cap-add=SYS_PTRACE -e DISPLAY \
                 -e USER_ID="$(id -u)" \
                 -e VSI_COMMON_IS_POWERSHELL=1 \
                 -e WINEDEBUG=fixme-all,err-winediag,err-menubuilder \
                 -v "${VSI_COMMON_WINE_TEST_VOLUME}:/home/.user_wine" \
                 -v /tmp/.X11-unix:/tmp/.X11-unix \
                 -v "${VSI_COMMON_DIR}":/vsi_common:ro \
                 -w /vsi_common \
                 "${VSI_COMMON_WINE_TEST_IMAGE}" &
      ;;
    test_wine) # Run unit tests using wine
      docker run -it --rm --cap-add=SYS_PTRACE \
                 -e USER_ID="$(id -u)" \
                 -e VSI_COMMON_IS_POWERSHELL=1 \
                 -e WINEDEBUG=fixme-all,err-winediag,err-menubuilder \
                 -v "${VSI_COMMON_WINE_TEST_VOLUME}:/home/.user_wine" \
                 -v "${VSI_COMMON_DIR}":/vsi_common:ro \
                 -w /vsi_common \
                 "${VSI_COMMON_WINE_TEST_IMAGE}" -c \
                 "cd /z/vsi_common
                  . setup.env
                  just test ${*}
                "'rv=$?
                  read -p "Press any key to close" -r -e -n1
                  exit ${rv}'
      extra_args+=$#
      ;;
    *)
      defaultify "${just_arg}" ${@+"${@}"}
      ;;
  esac
}

if [ "${JUST_IN_SCRIPT-0}" = "0" ]; then caseify ${@+"${@}"};fi
