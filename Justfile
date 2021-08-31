#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then #If being sourced
  set -euE
fi

# VSI_COMMON_DIR is a special var, handle is carefully.
if [ -z ${VSI_COMMON_DIR+set} ]; then
  VSI_COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd)"
fi
source "${VSI_COMMON_DIR}/linux/just_files/just_env" "${VSI_COMMON_DIR}/vsi_common.env"

source "${VSI_COMMON_DIR}/linux/just_files/just_docker_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_files/just_sphinx_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_files/just_bashcov_functions.bsh"
source "${VSI_COMMON_DIR}/linux/just_files/just_test_functions.bsh"
# Load vsi_test_env
source "${VSI_COMMON_DIR}/docker/tests/bash_test.Justfile"
source "${VSI_COMMON_DIR}/linux/elements.bsh"
source "${VSI_COMMON_DIR}/linux/findin"

cd "${VSI_COMMON_DIR}"

function sanitize_tag_name()
{
  local tag_name="${1//:/_}"
  tag_name=${tag_name////_}
  echo "${tag_name//@/_}"
}

function caseify()
{
  local just_arg=$1
  shift 1

  case ${just_arg} in
    test) # Run unit tests
      # Exit code 123 just means a test failed, no need for a Just stack trace
      # This has to be outside the (), because the () causes two stack traces
      local JUST_IGNORE_EXIT_CODES=123
      (
        parse_testlib_args ${@+"${@}"}
        shift "${extra_args}"
        vsi_test_env "${VSI_COMMON_DIR}/tests/run_tests" ${@+"${@}"}
      )
      local rv=$?
      if [ "${rv}" -ne "0" ]; then
        # This is needed for bash 3.2
        return rv
      fi
      extra_args=$#
      ;;
    test_int) # Run integration tests
      local JUST_IGNORE_EXIT_CODES=123
      justify test --dir int ${@+"${@}"}
      extra_args=$#
      ;;

    build_oses) # Build images for other OSes
      local os
      for os in ${VSI_COMMON_TEST_OSES[@]+"${VSI_COMMON_TEST_OSES[@]}"}; do
        justify build os "${os}"
      done
      ;;
    build_os) # Build images for other OSes, $1 - base OS image name
      local VSI_COMMON_TEST_OS="${1}"
      export VSI_COMMON_TEST_OS

      local VSI_COMMON_TEST_OS_TAG_NAME="$(sanitize_tag_name "${VSI_COMMON_TEST_OS}")"
      export VSI_COMMON_TEST_OS_TAG_NAME

      Just-docker-compose build os
      extra_args=1
      ;;
    test_oses) # Run test in docker image on OSes
      local os
      for os in ${VSI_COMMON_TEST_OSES[@]+"${VSI_COMMON_TEST_OSES[@]}"}; do
        echo "Testing ${os}" >&2
        justify test os "${os}"
      done
      ;;
    test_os) # Run test in docker images on specific OS, $1 - base OS image name
      local JUST_IGNORE_EXIT_CODES=123
      local VSI_COMMON_TEST_OS="${1}"
      export VSI_COMMON_TEST_OS
      shift 1
      extra_args=1

      local VSI_COMMON_TEST_OS_TAG_NAME="$(sanitize_tag_name "${VSI_COMMON_TEST_OS}")"
      export VSI_COMMON_TEST_OS_TAG_NAME
      Just-docker-compose run os ${@+"${@}"}
      extra_args+=$#
      ;;
    test_oses-common-source) # Test all oses for common_source
      local os
      for os in ${VSI_COMMON_TEST_OSES[@]+"${VSI_COMMON_TEST_OSES[@]}"}; do
        echo "Testing ${os}" >&2
        justify test os-common-source "${os}"
      done
      ;;
    test_os-common-source) # Run VSI Common source test - $1 name of image to check
      local ans
      extra_args=1
      ans="$(findin "${1}" "${VSI_COMMON_TEST_OSES[@]}")"
      ans="${VSI_COMMON_TEST_OSES_ANS[ans]}"
      local image="${VSI_COMMON_DOCKER_REPO}:os_$(sanitize_tag_name "${1}")"

      local x="$(docker run --rm -v ${VSI_COMMON_DIR}:/vsi "${image}" \
                   sh -euc ". /vsi/linux/common_source.sh;
                            echo \$VSI_DISTRO - \$VSI_DISTRO_VERSION, \
                                 \$VSI_DISTRO_LIKE - \$VSI_DISTRO_VERSION_LIKE, \
                                 \$VSI_DISTRO_CORE - \$VSI_DISTRO_VERSION_CORE \$VSI_MUSL")"
      if [ "${x}" = "${ans}" ]; then
        echo "${1} passed"
      else
        echo "${x} != ${ans}"
        return 1
      fi
      ;;
    push_oses) # Push os images
      local os
      for os in ${VSI_COMMON_TEST_OSES[@]+"${VSI_COMMON_TEST_OSES[@]}"}; do
        docker push "${VSI_COMMON_DOCKER_REPO}:os_$(sanitize_tag_name "${os}")"
      done
      ;;

    pull_oses) # Pull latest images for other OSes
      local os
      for os in ${VSI_COMMON_TEST_OSES[@]+"${VSI_COMMON_TEST_OSES[@]}"}; do
        docker pull "${os}"
      done
      ;;

    pull_os) # Pull image for os - $1
      docker pull "${VSI_COMMON_DOCKER_REPO}:os_$(sanitize_tag_name "${1}")"
      extra_args=1
      ;;

    ci_load) # Load ci
      justify docker-compose_ci-load "${VSI_COMMON_DIR}/docker-compose.yml" "bash_test_${1}"
      extra_args=1
      ;;
    test_int_appveyor) # Run integration tests for windows appveyor
      local JUST_IGNORE_EXIT_CODES=123
      (
        source elements.bsh
        pushd "${VSI_COMMON_DIR}/tests/int/" &> /dev/null
          test_list=(*)
        popd &> /dev/null
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
      local JUST_IGNORE_EXIT_CODES=123
      TESTLIB_DISCOVERY_DIR="${VSI_COMMON_DIR}/docker/recipes/tests" vsi_test_env "${VSI_COMMON_DIR}/tests/run_tests" ${@+"${@}"}
      extra_args=$#
      ;;
    test_darling) # Run unit tests using darling
      local JUST_IGNORE_EXIT_CODES=123
      (
        cd "${VSI_COMMON_DIR}"
        TESTLIB_PARALLEL=8 vsi_test_env darling shell ./tests/run_tests ${@+"${@}"}
      )
      local rv=$?
      if [ "${rv}" -ne "0" ]; then
        # This is needed for bash 3.2
        return rv
      fi
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
        VSI_COMMON_BASH_TEST_VERSION="${1}" Just-docker-compose build bash_test
        extra_args=1
      else
        for version in ${VSI_COMMON_BASH_TEST_VERSIONS[@]+"${VSI_COMMON_BASH_TEST_VERSIONS[@]}"}; do
          VSI_COMMON_BASH_TEST_VERSION="${version}" Just-docker-compose build bash_test
        done
      fi
      ;;
    test_bash) # Run command (like bash) in the contain for a specific version of bash ($1)
      local bash_version="${1-5.0}"
      local JUST_IGNORE_EXIT_CODES=123
      extra_args=$#
      shift 1
      VSI_COMMON_BASH_TEST_VERSION="${bash_version}" Just-docker-compose run bash_test ${@+"${@}"}
      ;;

    background_start) # Start bash dockers in background
      local DOCKER_COMPOSE_EXTRA_RUN_ARGS
      local name
      if [ $# -gt 0 ]; then
        name="${COMPOSE_PROJECT_NAME}_bash_bg_${1}"
        if Docker inspect --type container "${name}" &> /dev/null; then
          Docker rm -f "${name}"
        fi
        DOCKER_COMPOSE_EXTRA_RUN_ARGS=(-d --name "${name}")
        VSI_COMMON_BASH_TEST_VERSION="${1}" Just-docker-compose run bash_test bash
        extra_args=1
      else
        local version
        for version in ${VSI_COMMON_BASH_TEST_VERSIONS[@]+"${VSI_COMMON_BASH_TEST_VERSIONS[@]}"}; do
          name="${COMPOSE_PROJECT_NAME}_bash_bg_${version}"
          if Docker inspect --type container "${name}" &> /dev/null; then
            Docker rm -f "${name}"
          fi
          DOCKER_COMPOSE_EXTRA_RUN_ARGS=(-d --name "${name}")
          VSI_COMMON_BASH_TEST_VERSION="${version}" Just-docker-compose run bash_test bash
        done
      fi
      ;;
    background_stop) # Stop background bashes
      local name
      if [ $# -gt 0 ]; then
        name="${COMPOSE_PROJECT_NAME}_bash_bg_${1}"
        if Docker inspect --type container "${name}" &> /dev/null; then
          Docker rm -f "${name}"
        fi
        extra_args=1
      else
        local version
        for version in ${VSI_COMMON_BASH_TEST_VERSIONS[@]+"${VSI_COMMON_BASH_TEST_VERSIONS[@]}"}; do
          name="${COMPOSE_PROJECT_NAME}_bash_bg_${version}"
          if Docker inspect --type container "${name}" &> /dev/null; then
            Docker rm -f "${name}"
          fi
        done
      fi
      ;;
    background_exec) # Run command in background bashes
      local name
      local names=($(docker ps --format '{{.Names}}' | grep "^${COMPOSE_PROJECT_NAME}_bash_bg_"))

      for name in ${names[@]+"${names[@]}"}; do
        echo "Bash ${name}" >&2
        Docker exec -it "${name}" ${@+"${@}"}
      done
      extra_args=$#
      ;;

    push_bash) # Push bash images
      local version

      if [ $# -gt 0 ]; then
        Docker push "${VSI_COMMON_DOCKER_REPO}:bash_test_${1}"
        extra_args=1
      else
        for version in ${VSI_COMMON_BASH_TEST_VERSIONS[@]+"${VSI_COMMON_BASH_TEST_VERSIONS[@]}"}; do
          Docker push "${VSI_COMMON_DOCKER_REPO}:bash_test_${version}"
        done
      fi
      ;;

    pull_bash) # Pull bash image
      Docker pull "${VSI_COMMON_DOCKER_REPO}:bash_test_${1}"
      extra_args=1
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
      local JUST_IGNORE_EXIT_CODES=123
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
