#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then #If being sourced
  set -euE
fi

JUST_PROJECT_PREFIX=VSI_COMMON
VSI_COMMON_WINE_TEST_IMAGE=vsi_wine_test
VSI_COMMON_WINE_TEST_VOLUME=vsi_common_wine_home

source "$(\cd "$(\dirname "${BASH_SOURCE[0]}")"; \pwd)/wrap"
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

    build_docs) # Build docker image
      ( #TODO move to docker
        cd "${VSI_COMMON_DIR}/docs"
        pipenv run make
      )
      ;;

    compile_docs) # Compile documentation
      (
        cd "${VSI_COMMON_DIR}/docs"
        # if (( $# )); then
        #   pipenv run make "${@}"
        # else
        #   pipenv run make html
        # fi
        files=()

        # For now, all languages we are using can use ## as comments. When this
        # is no longer true, the find will need to be extension specific, or
        # some mechanism will be needed to determine type, say `file`
        while IFS= read -r -d '' file; do
          files+=("${file}")
        done < <(find "${VSI_COMMON_DIR}" -type f -not -name '*.md' -name just -print0)

        for file in "${files[@]}"; do
          doc_file="$(sed -nE '/ *#\*# */{s/ *#\*# *//; p;q}' "${file}")"
          if [[ ${doc_file::1} =~ ^[./j] ]]; then
            echo "${file} skipped. Invalid dockname ${doc_file}"
            continue
          fi
          sed -nE  ':block_start
                    # If the beginning pattern matched, start reading the block
                    /^#\*\*/b read_block
                    # Else do not print, goes to next line
                    b noprint
                    :read_block
                    # read the next line
                    n
                    # If the end of doc comment, move on
                    /^ *#\*\*/b noprint
                    # If a line starting with #
                    /^ *#/{
                      # Remove those extra spaced, #, and an optional space
                      s/# ?//
                      # print it
                      # p
                    }
                    # continue reading the block
                    b read_block
                    # Move on
                    :noprint
                   ' "${file}"
        done
      )
      ;;
    *)
      defaultify "${just_arg}" ${@+"${@}"}
      ;;
  esac
}

if [ "${JUST_IN_SCRIPT-0}" = "0" ]; then caseify ${@+"${@}"};fi
