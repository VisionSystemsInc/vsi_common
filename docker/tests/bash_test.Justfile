#!/usr/bin/env false bash

function vsi_test_env()
{
  local test_env=("VSI_COMMON_DIR=${VSI_COMMON_DIR}"
                  "HOME=${HOME}"
                  "TERM=${TERM}"
                  "PATH=${PATH}")
  local envvar
  # Copy all TESTLIB_* vars
  for envvar in $(compgen -A export TESTLIB_ || :); do
    test_env+=("${envvar}=${!envvar}")
  done

  # This can affect a lot of applications in bad ways if it is missing
  if [ -n "${DBUS_SESSION_BUS_ADDRESS+set}" ]; then
    test_env+=("DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS}")
  fi

  env -i "${test_env[@]}" "${@}"
}

function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    all_tests) # Run tests and integration tests
      justify test
      justify test int
      ;;
    test) # Run unit tests
      vsi_test_env "${VSI_COMMON_DIR}/tests/run_tests" ${@+"${@}"}
      extra_args=$#
      ;;
    test_int) # Run integration tests
      TESTLIB_DISCOVERY_DIR=int vsi_test_env "${VSI_COMMON_DIR}/tests/run_tests" ${@+"${@}"}
      extra_args=$#
      ;;
    help)
      # defaultify help
      ;;
    *)
      exec "${cmd}" ${@+"${@}"}
      ;;
  esac
}
