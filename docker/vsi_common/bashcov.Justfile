#!/usr/bin/env false bash

source "${VSI_COMMON_DIR}/linux/isin"
source "${VSI_COMMON_DIR}/tests/run_tests"

function caseify()
{
  local cmd="${1}"
  shift 1

  : ${TESTLIB_PARALLEL=$(nproc)}
  export TESTLIB_PS4='+'
  export TESTLIB_REDIRECT_OUTPUT=0

  case "${cmd}" in
    bashcov) # Run bashcov
      run_all_tests_setup_summary_dir
      pushd /src &> /dev/null
        bashcov --root /src ${@+"${@}"}
        extra_args=$#
      popd &> /dev/null
      ;;
    multiple) # Run multiple commands through bashcov
      run_all_tests_setup_summary_dir
      pushd /src &> /dev/null
        extra_args=$#
        while (( $# )); do
          printf '%s\0' "${1}"
          shift 1
        done | sort -z | xargs -0 -I % -P "${TESTLIB_PARALLEL}" bashcov --root /src %
      popd &> /dev/null
      ;;
    resume) # Resume running bashcov multiple, skipping already run.
      local bash="$(which bash)"
      local files=()

      pushd /src &> /dev/null
        if [ -r /src/coverage/.resultset.json ]; then
          IFS='' readarray -t -d $'\n' files < <(
            jq -r 'keys | .[]' /src/coverage/.resultset.json | \
            sed "s|${bash} ||")
        fi

        extra_args=$#
        while (( $# )); do
          if isin "${1}" ${files[@]+"${files[@]}"}; then
            echo "Skipping ${1}..." >&2
          else
            printf '%s\0' "${1}"
          fi
          shift 1
        done | sort -z | xargs -0 -I % -P "${TESTLIB_PARALLEL}" bashcov --root /src %
      popd &> /dev/null
      ;;
    *) # Run command in pipenv
      exec "${cmd}" "${@}"
      ;;
  esac
}
