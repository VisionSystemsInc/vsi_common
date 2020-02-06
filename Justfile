#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then #If being sourced
  set -euE
fi

# VSI_COMMON_DIR is a special var, handle is carefully.
if [ -z ${VSI_COMMON_DIR+set} ]; then
  VSI_COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd)"
fi
source "${VSI_COMMON_DIR}/linux/just_env" "${VSI_COMMON_DIR}/vsi_common.env"

source "${VSI_COMMON_DIR}/linux/just_docker_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_sphinx_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_bashcov_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_test_functions.bsh"
# Load vsi_test_env
source "${VSI_COMMON_DIR}/docker/tests/bash_test.Justfile"
source "${VSI_COMMON_DIR}/linux/elements.bsh"

cd "${VSI_COMMON_DIR}"

function caseify()
{
  local just_arg=$1
  shift 1

  case ${just_arg} in
    test) # Run unit tests
      (
        parse_testlib_args ${@+"${@}"}
        shift "${extra_args}"
        vsi_test_env "${VSI_COMMON_DIR}/tests/run_tests" ${@+"${@}"}
      )
      extra_args=$#
      ;;
    # --test) # Run only this test
    #   export TESTLIB_RUN_SINGLE_TEST="${1}"
    #   extra_args=1
    #   ;;
    test_int) # Run integration tests
      justify test --dir int ${@+"${@}"}
      extra_args=$#
      ;;

    test_docker) # Run tests in docker image. Useful for running in specific bash version ($1)
      local version="${1-5.0}"
      shift 1
      extra_args=1
      Just-docker-compose run "bash_test_${version}" ${@+"${@}"}
      extra_args+=$#
      ;;
    ci_load) # Load ci
      justify docker-compose_ci-load "${VSI_COMMON_DIR}/docker-compose.yml" "bash_test_${1}"
      extra_args=1
      ;;
    test_int_appveyor) # Run integration tests for windows appveyor
      (
        source elements.bsh
        test_list=($(ls "${VSI_COMMON_DIR}/tests/int/"))
        remove_element_a test_list test-common_source.bsh
        tests=()
        for x in "${test_list[@]}"; do
          x="${x%.bsh}"
          tests+=("${x#test-}")
        done
        justify test int "${tests[@]}"
      )
      ;;
    test_recipe) # Run docker recipe tests
      TESTLIB_DISCOVERY_DIR="${VSI_COMMON_DIR}/docker/recipes/tests" vsi_test_env "${VSI_COMMON_DIR}/tests/run_tests" ${@+"${@}"}
      extra_args=$#
      ;;
    test_darling) # Run unit tests using darling
      (
        cd "${VSI_COMMON_DIR}"
        TESTLIB_PARALLEL=8 vsi_test_env darling shell ./tests/run_tests ${@+"${@}"}
      )
      extra_args=$#
      ;;
    test_python) # Run python unit tests
      Docker-compose run python3
      # Docker-compose run python2
      # python3 -B -m unittest discover -s "${VSI_COMMON_DIR}/python/vsi/test"
      ;;
    build_docker) # Build docker image
      Docker-compose build
      justify docker-compose clean venv2 docker-compose clean venv3
      justify _post_build_docker
      ;;

    build_bash) # Build images for all bash versions or a specific version ($1)
      local version

      if [ $# -gt 0 ]; then
        Just-docker-compose build "bash_test_${1}"
        extra_args=1
      else
        for version in 3.2 4.0 4.1 4.2 4.3 4.4 5.0; do
          Just-docker-compose build "bash_test_${version}"
        done
      fi
      ;;
    test_bash) # Run command (like bash) in the contain for a specific version of bash ($1)
      local bash_version="${1}"
      extra_args=$#
      shift 1
      Just-docker-compose run "bash_test_${bash_version}" ${@+"${@}"}
      ;;

    bashcov_vsi) # Run bashcov on vsi_common
      local int_tests=(./tests/int/test-*.bsh)
      remove_element_a int_tests ./tests/int/test-common_source.bsh

      justify bashcov multiple "${int_tests[@]}" ./tests/test-*.bsh
      ;;

    _post_build_docker)
      docker_cp_image "${VSI_COMMON_DOCKER_REPO}:python2_test" "/venv/Pipfile2.lock" "${VSI_COMMON_DIR}/docker/tests/Pipfile2.lock"
      docker_cp_image "${VSI_COMMON_DOCKER_REPO}:python3_test" "/venv/Pipfile3.lock" "${VSI_COMMON_DIR}/docker/tests/Pipfile3.lock"
      ;;
    run_wine) # Start a wine bash window
      Docker-compose run -e USER_ID="$(id -u)" wine ${@+"${@}"} || :
      extra_args=$#
      ;;
    run_wine-gui) # Start a wine bash window in gui mode
      Docker-compose run -e USER_ID="$(id -u)" wine_gui ${@+"${@}"}&
      extra_args=$#
      ;;
    test_wine) # Run unit tests using wine
      justify run wine -c "
        cd /z/vsi
        source setup.env
        just test ${*}"'
        rv=$?
        read -p "Press any key to close" -r -e -n1
        exit ${rv}'
      extra_args=$#
      ;;
    *)
      defaultify "${just_arg}" ${@+"${@}"}
      ;;
  esac
}

if ! command -v justify &> /dev/null; then caseify ${@+"${@}"};fi
