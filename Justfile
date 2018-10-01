#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then #If being sourced
  set -euE
fi

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
    test_python) # Run python unit tests
      Docker-compose run python2
      Docker-compose run python3
      # python3 -B -m unittest discover -s "${VSI_COMMON_DIR}/python/vsi/test"
      ;;
    build_docker) # Build docker image
      Docker-compose build
      (justify clean venv)
      (justify _post_build_docker)
      ;;
    clean_venv) # Delete the virtual environment volume. The next container \
                # to use this volume will automatically copy the contents from \
                # the image.
      if docker volume inspect "${COMPOSE_PROJECT_NAME}_venv2" &> /dev/null; then
        Docker volume rm "${COMPOSE_PROJECT_NAME}_venv2"
      else
        echo "${COMPOSE_PROJECT_NAME}_venv2 already removed" >&2
      fi
      if docker volume inspect "${COMPOSE_PROJECT_NAME}_venv3" &> /dev/null; then
        Docker volume rm "${COMPOSE_PROJECT_NAME}_venv3"
      else
        echo "${COMPOSE_PROJECT_NAME}_venv3 already removed" >&2
      fi
      ;;

    _post_build_docker)
      image_name=$(docker create ${VSI_COMMON_DOCKER_REPO}:python2_test)
      docker cp ${image_name}:/venv/Pipfile2.lock "${VSI_COMMON_DIR}/docker/tests/Pipfile2.lock"
      docker rm ${image_name}
      image_name=$(docker create ${VSI_COMMON_DOCKER_REPO}:python3_test)
      docker cp ${image_name}:/venv/Pipfile3.lock "${VSI_COMMON_DIR}/docker/tests/Pipfile3.lock"
      docker rm ${image_name}
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
      image_name=$(docker create ${VSI_COMMON_DOCKER_REPO}:compile_docs)
      docker cp ${image_name}:/venv/Pipfile.lock "${VSI_COMMON_DIR}/docs/Pipfile.lock"
      docker rm ${image_name}
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
