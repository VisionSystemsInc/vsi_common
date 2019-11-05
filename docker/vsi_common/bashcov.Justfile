#!/usr/bin/env false bash

source "${VSI_COMMON_DIR}/linux/isin"


function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    bashcov) # Run bashcov
      pushd /src &> /dev/null
        TESTLIB_NO_PS4=1 TESTS_PARALLEL=1 TESTLIB_REDIRECT_OUTPUT=0 bashcov --root /src ${@+"${@}"}
        extra_args=$#
      popd &> /dev/null
      ;;
    multiple) # Run multiple commands through bashcov
      pushd /src &> /dev/null
        extra_args=$#
        while (( $# )); do
          TESTLIB_NO_PS4=1 TESTS_PARALLEL=1 TESTLIB_REDIRECT_OUTPUT=0 bashcov --root /src "${1}"
          shift 1
        done
      popd &> /dev/null
      ;;
    resume) # Resume running bashcov multiple, skipping already run.
      local bash="$(which bash)"
      local files

      pushd /src &> /dev/null
        IFS='' readarray -t -d $'\n' files < <(
          jq -r 'keys | .[]' /src/coverage/.resultset.json | \
          sed "s|${bash} ||")

        # IFS='' readarray -d '' files < <(
        #   jq -M keys /src/coverage/.resultset.json | \
        #   sed -nE '
        #     # Unlike the standard "load entire file into the pattern buffer", this
        #     # will load the entire file into the hold buffer, except the first and last line
        #     # Remove first line, it is just a [
        #     1d
        #     # Replace the hold buffer with line two (because it starts off containing a newline)
        #     # and then delete the line from the pattern buffer, only because that ends execution
        #     # and goes onto the next line.
        #     2{h;d}

        #     :combine
        #     # If this is the last line, goto done. This means the last line is not added to the hold buffer
        #     $bdone
        #     # Else append the line to the hold buffer
        #     H
        #     # read the next line
        #     n
        #     # Continue iterating
        #     bcombine
        #     :done
        #     x

        #     # Remove the last " at the end of the last filename
        #     s|"$||
        #     # Remove the first "bash_patch{space}
        #     s|^  "'"${bash}"' ||
        #     #convert the rest of the ", "bash_path to null, resulting in null separated strings
        #     s|",\n  "'"${bash}"' |\x00|g
        #     p' | \
        #     # https://stackoverflow.com/a/1654042/4166604
        #     perl -pe 'chomp if eof')

        extra_args=$#
        while (( $# )); do
          if isin "${1}" ${files[@]+"${files[@]}"}; then
            echo "Skipping ${1}..." >&2
            shift 1
            continue
          fi
          TESTLIB_NO_PS4=1 TESTS_PARALLEL=1 TESTLIB_REDIRECT_OUTPUT=0 bashcov --root /src "${1}"
          shift 1
        done
      popd &> /dev/null
      ;;
    *) # Run command in pipenv
      exec "${cmd}" "${@}"
      ;;
  esac
}
