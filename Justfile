#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then #If being sourced
  set -euE
fi

JUST_PROJECT_PREFIX=VSI_COMMON
export VSI_COMMON_UID=$(id -u)
export VSI_COMMON_GIDS=$(id -g)

source "$(\cd "$(\dirname "${BASH_SOURCE[0]}")"; \pwd)/linux/just_env" "$(dirname "${BASH_SOURCE[0]}")"/vsi_common.env

source "${VSI_COMMON_DIR}/linux/just_docker_functions.bsh"

cd "$(\dirname "${BASH_SOURCE[0]}")"

function caseify()
{
  local just_arg=$1
  shift 1
  case ${just_arg} in
    test) # Run unit tests
      "${VSI_COMMON_DIR}/tests/run_tests.bsh" ${@+"${@}"}
      extra_args+=$#
      ;;
    --test) # Run only this test
      export TESTLIB_RUN_SINGLE_TEST="${1}"
      extra_args+=1
      ;;
    test_int) # Run integration tests
      TESTS_DIR=int "${VSI_COMMON_DIR}/tests/run_tests.bsh" ${@+"${@}"}
      extra_args+=$#
      ;;
    test_recipe) # Run docker recipe tests
      TESTS_DIR="${VSI_COMMON_DIR}/docker/recipes/tests" "${VSI_COMMON_DIR}/tests/run_tests.bsh" ${@+"${@}"}
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

    build_docs) # Build docs image
      Docker-compose build docs
      ;;

    --nit) # Set nit picky when compiling docs
      export SPHINXOPTS="${SPHINXOPTS-} -n"
      ;;
    --all) # Set rebuild all when compiling docs
      export SPHINXOPTS="${SPHINXOPTS-} -a"
      ;;
    compile_docs) # Compile documentation
      Docker-compose run -e SPHINXOPTS docs ${@+"${@}"}
      ;;
    *)
      defaultify "${just_arg}" ${@+"${@}"}
      ;;
  esac
}

if [ "${JUST_IN_SCRIPT-0}" = "0" ]; then caseify ${@+"${@}"};fi
