#!/usr/bin/env false bash

# Unit and integration tests do not inherit the parent process' environment,
# this continuously caused too many issues. So instead we wipe it, and only
# copy variables needed here. There shouldn't be much need to add more, but if
# there is, this is where it is done
function vsi_test_env()
{
  local test_env=()
  local envvar
  # Copy all TESTLIB_* vars
  for envvar in $(compgen -A export TESTLIB_ || :); do
    test_env+=("${envvar}=${!envvar}")
  done

  for envvar in VSI_COMMON_DIR HOME TERM PATH \
                DBUS_SESSION_BUS_ADDRESS \
                DOCKER_HOST\
                NUMBER_OF_PROCESSORS OS; do
  # DBUS_SESSION_BUS_ADDRESS - can affect a lot of applications in bad ways if it is missing
  # DOCKER_HOST - for remote docker functionality when running the int tests. When running
  # the docker tests, DOCKER_HOST will not be passed along, os it'll be unset, and still
  # NUMBER_OF_PROCESSORS OS - For windows, this shouldn't be removed, I'd call it a bug
  # VSI_COMMON_DIR HOME TERM PATH - Just normal things
    if [ -n "${!envvar+set}" ]; then
      test_env+=("${envvar}=${!envvar}")
    fi
  done

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
