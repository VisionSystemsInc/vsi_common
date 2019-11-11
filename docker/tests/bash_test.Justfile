#!/usr/bin/env false bash

function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    test) # Run unit tests
      "${VSI_COMMON_DIR}/tests/run_tests" ${@+"${@}"}
      extra_args=$#
      ;;
    test_int) # Run integration tests
      TESTLIB_DISCOVERY_DIR=int "${VSI_COMMON_DIR}/tests/run_tests" ${@+"${@}"}
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
