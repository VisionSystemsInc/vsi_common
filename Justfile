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
        env -i HOME="${HOME}" darling shell env TESTS_PARALLEL=8 ./tests/run_tests.bsh ${@+"${@}"}
      )
      extra_args+=$#
      ;;
    build_wine) # Build wine image
      Docker-compose build
      ;;
    run_wine) # Start a wine bash window
      Docker-compose run -e USER_ID="$(id -u)" wine ${@+"${@}"} || :
      extra_args+=$#
      ;;
    run_wine-gui) # Start a wine bash window in gui mode
      Docker-compose run -e USER_ID="$(id -u)" wine_gui ${@+"${@}"}&
      extra_args+=$#
      ;;
    test_wine) # Run unit tests using wine
      (justify run wine -c "
        cd /z/vsi_common
        . setup.env
        just test ${*}"'
        rv=$?
        read -p "Press any key to close" -r -e -n1
        exit ${rv}')
      extra_args+=$#
      ;;
    *)
      defaultify "${just_arg}" ${@+"${@}"}
      ;;
  esac
}

if [ "${JUST_IN_SCRIPT-0}" = "0" ]; then caseify ${@+"${@}"};fi
