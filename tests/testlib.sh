#!/usr/bin/env false

#****J* vsi/testlib.sh
# NAME
#   testlib.sh - Simple shell command language test library
# USAGE
#   . testlib.sh
# EXAMPLE
#   Tests must follow the basic form:
#
#   source testlib.sh
#
#   begin_test "the thing"
#   (
#        set -e
#        echo "hello"
#        false
#   )
#   end_test
#
#   When a test fails its stdout and stderr are shown.
# NOTES
#   Tests must 'set -e' within the subshell block or failed assertions will not
#   cause the test to fail and the result may be misreported. While this is not
#   required, most tests will have this on.
# BUGS
#   On darling: when debugging a unit test error, sometimes the printout is cut
#   off, making it difficult to do "printf debugging." While the cause and scope
#   of this is unknown, it appears that running "reset" just prior to the test
#   fixes this. So if this is happening to you, simply run reset before every
#   call to run the tests.
# COPYRIGHT
#   Original version: (c) 2011-13 by Ryan Tomayko <http://tomayko.com>
#   License: MIT
# AUTHOR
#   Ryan Tomayko
# MODIFICATION HISTORY
#   Andy Neff - Added begin_expected_fail_test
#               Added optional setup/teardown functions
#               Removed PATH
#               Added robodoc documentation
#               Use pushd/popd for each test instead of cd
#               Auto prepend filename to description
#               Added custom PS4
#***

# The above must be the first command executed, or else it won't work. Use this
# instead of BASH_SOURCE to maintain sh compatibility
: ${VSI_COMMON_DIR="$(cd "$(dirname "$_")/.."; pwd)"}

set -e

if [ "${TESTLIB_SHOW_TIMING-0}" == "1" ] || [[ ${OSTYPE} = darwin* ]]; then
  . "${VSI_COMMON_DIR}/linux/time_tools.bsh"
fi
. "${VSI_COMMON_DIR}/linux/file_tools.bsh"
. "${VSI_COMMON_DIR}/tests/test_colors.sh"

# create a temporary work space
TRASHDIR="$(mktemp -d -t $(basename "$0")-$$.XXXXXXXX)"

# keep track of num tests and failures
tests=0
failures=0
expected_failures=0
required_failures=0
skipped=0

#****f* testlib.sh/setup
# NAME
#   setup - Function run before the first test
# NOTES
#   A directory TRASHDIR is created for setup, right before running setup().
#
#   Setup is not run if no tests are ever run
# AUTHOR
#   Andy Neff
#***

#****d* testlib.sh/TRASHDIR
# NAME
#   TRASHDIR - Temporary directory where everything for the test file is stored
# DESCRIPTION
#   Automatically generated and removed (unless TEST_KEEP_TEMP_DIRS is changed)
# SEE ALSO
#   testlib.sh/TESTDIR
# AUTHOR
#   Ryan Tomayko
#***

#****d* testlib.sh/TESTDIR
# NAME
#   TESTDIR - Unique temporary directory for a single test (in TRASHDIR)
# DESCRIPTION
#   Automatically generated and removed (unless TEST_KEEP_TEMP_DIRS is changed)
# SEE ALSO
#   testlib.sh/TRASHDIR
# AUTHOR
#   Ryan Tomayko
#***

#****f* testlib.sh/teardown
# NAME
#   teardown - Function run after the last test
# NOTES
#   Teardown is not run if no tests are ever run
# AUTHOR
#   Andy Neff
#***

#****d* testlib.sh/TEST_KEEP_TEMP_DIRS
# NAME
#   TEST_KEEP_TEMP_DIRS - Keep the trashdir/setup dir
# DESCRIPTION
#   Debug flag to keep the temporary directories generated when testing. Set to
#   1 to keep directories. Default: 0
# AUTHOR
#   Andy Neff
#***

#****d* testlib.sh/TESTLIB_SHOW_TIMING
# NAME
#   TESTLIB_SHOW_TIMING - Display test time after each test
# DESCRIPTION
#   Debug flag to display time elapsed for each test. Set to 1 to enable.
#   Default: 0
# AUTHOR
#   Andy Neff
#***

#****d* testlib.sh/TESTLIB_RUN_SINGLE_TEST
# NAME
#   TESTLIB_RUN_SINGLE_TEST - Run a single test
# DESCRIPTION
#   Instead of running all the tests in a test file, all tests not matching the
#   description exactly to the value of TESTLIB_RUN_SINGLE_TEST will be skipped.
#   Useful for debugging a specific test/piece of code
#   Default: unset
# AUTHOR
#   Andy Neff
#***

#****f* testlib.sh/atexit
# NAME
#   atexit - Function that runs at process exit
# USAGE
#   Automatically called on exit by trap.
#
#   Checks to see if teardown is defined, and calls it. teardown is typically a
#   function, alias, or something that makes sense to call.
# AUTHOR
#   Ryan Tomayko
# MODIFICATION HISTORY
#   Andy Neff - Added setup cleanup
#               Added teardown
#               Added TEST_KEEP_TEMP_DIRS flags
#***
atexit ()
{
  test_status=$?
  if [ -n "${test_description+set}" ]; then
    end_test $test_status
    echo "${TEST_BAD_COLOR}WARNING${TEST_RESET_COLOR}: end_test not added at end of last test." 1>&2
    declare -p BASH_SOURCE
  fi
  unset test_status

  if [ "${tests}" -ne 0 ] && [ "${tracking_touched_files-}" = "1" ]; then
    cleanup_touched_files
  fi

  if [ "${tests}" -ne 0 ] && type -t teardown &>/dev/null && [ "$(command -v teardown)" == "teardown" ]; then
    teardown
  fi

  if [ "${TEST_KEEP_TEMP_DIRS-}" != "1" ]; then
    rm -rf "$TRASHDIR"
  fi

  local BOLD_COLOR
  if [ "${failures}" -eq 0 ]; then
    BOLD_COLOR="${TEST_BOLD_COLOR}"
  else
    BOLD_COLOR="${TEST_BAD_COLOR}"
  fi

  printf "%s summary: %d test ran, ${BOLD_COLOR}%d failures${TEST_RESET_COLOR}, %d expected failures, %d required failures, %d skipped\n" \
         "$0" "${tests}" "${failures}" "${expected_failures}" "${required_failures}" "${skipped}"

  if [ -d "${summary_log_dir-}" ]; then
    echo "${tests} ${failures} ${expected_failures} ${required_failures} ${skipped}" > "${summary_log_dir}/$(basename "$0")"
  fi

  if [ "${failures}" -gt 0 ]; then
    exit 1
  else
    exit 0
  fi
}
trap "atexit" EXIT

if declare -p BASH_SOURCE &>/dev/null; then
  PS4=$'+${BASH_SOURCE-null}:${LINENO})\t'
else
  # Not as accurate, but better than nothing
  PS4=$'+${0}:${LINENO})\t'
fi

# Common code for begin tests
_begin_common_test ()
{
  local fd
  TESTDIR="${TRASHDIR}/test${tests}"
  mkdir -p "${TESTDIR}"
  pushd "$TESTDIR" &> /dev/null
  # This makes calling end_test between tests "optional", but highly recommended.
  # end_test does have to be called after the last test, especially if teardown
  # is defined after the last test
  if [ -n "${test_description+set}" ]; then
    end_test $test_status
    echo "${TEST_BAD_COLOR}WARNING${TEST_RESET_COLOR}: end_test not added at end of a test." 1>&2
    declare -p BASH_SOURCE
  fi
  unset test_status

  # Set flag defaults that could be overrideable in certain test types.
  # This needs to be after end_test call above in order to keep end_test
  # optional
  expected_failure=${_expected_failure-0}
  required_fail=${_required_fail-0}

  # Run setup if this is the first test
  if [ "${tests}" -eq 0 ] && type -t setup &>/dev/null && [ "$(command -v setup)" == "setup" ]; then
    setup
  fi

  tests=$(( tests + 1 ))
  local test_file_name="$(basename "$0")"
  test_file_name=${test_file_name%.*}
  test_file_name=${test_file_name#test-}
  test_description="$test_file_name - $1"

  if [ "${tracking_touched_files}" = "1" ]; then
    track_touched_file="$(mktemp -u)"
    ttouch "${track_touched_file}"
  fi

  if [ "${TESTLIB_SHOW_TIMING-0}" == "1" ]; then
    _time_0=$(get_time_seconds)
  fi

  if [ "${TESTLIB_RUN_SINGLE_TEST+set}" = "set" ] && \
     [ "$1" != "${TESTLIB_RUN_SINGLE_TEST}" ]; then
    skip_next_test
  fi

  find_open_fd stdout
  eval "exec ${stdout}>&1"
  find_open_fd stderr
  eval "exec ${stderr}>&2"

  out="${TESTDIR}/out"
  err="${TESTDIR}/err"
  exec 1>"$out" 2>"$err"

  # Allow the subshell to exit non-zero without exiting this process
  set -x +e
}

#****f* testlib.sh/begin_test
# NAME
#   begin_test - Beginning of test demarcation
# USAGE
#   Mark the beginning of a test. A subshell should immediately follow this
#   statement.
# SEE ALSO
#   testlib.sh/end_test
# AUTHOR
#   Ryan Tomayko
#***
begin_test ()
{
  test_status=$? # Must be first command
  _begin_common_test ${@+"${@}"}
}

#****f* testlib.sh/begin_expected_fail_test
# NAME
#   begin_expected_fail_test - Beginning of expected fail test demarcation
# USAGE
#   Define the beginning of a test that is expected to fail
# AUTHOR
#   Andy Neff
#***
begin_expected_fail_test()
{
  test_status=$? # Must be first command
  # Override _begin_common_test default
  _expected_failure=1 _begin_common_test ${@+"${@}"}
}

#****f* testlib.sh/begin_required_fail_test
# NAME
#   begin_required_fail_test - Beginning of required fail test demarcation
# USAGE
#   Define the beginning of a test that is required to fail
# AUTHOR
#   Andy Neff
#***
begin_required_fail_test()
{
  test_status=$? # Must be first command
  # Override _begin_common_test default
  _required_fail=1 _begin_common_test ${@+"${@}"}
}

#****f* testlib.sh/setup_test
# NAME
#   setup_test - Sets up the test
# DESCRIPTION
#   Once inside the () subshell, typically set -eu needs to be run, then other
#   things such as checking to see if a test should be skipped, etc. need to
#   be done. This is all encapsulated into setup_test. This is required; without
#   it, end_test will know you forgot to call this and fail.
#
#   This is also the second part of creating a skippable test.
#
#   You are free to change "set -eu" after setup_test, should you wish.
# USAGE
#   Place at the beginning of a test
# EXAMPLE
#   skip_next_test
#   begin_test "Skipping test"
#   (
#     setup_test
#     #test code here
#   )
# SEE ALSO
#   testlib.sh/skip_next_test
# AUTHOR
#   Andy Neff
#***
setup_test()
{
  # Identify that setup_test was called
  touch "${TRASHDIR}/.setup_test"

  # Check to see if this test should be skipped
  if [ "${__testlib_skip_test-}" = "1" ]; then
    exit 0
  fi

  set -eu
}

#****f* testlib.sh/end_test
# NAME
#   end_test - End of a test demarcation
# USAGE
#   Mark the end of a test. Must be the first command after the test group, or
#   else the return value will not be captured successfully.
# SEE ALSO
#   testlib.sh/begin_test
# AUTHOR
#   Ryan Tomayko
#***
end_test ()
{
  test_status="${1:-$?}" # This MUST be the first line of this function
  set +x -e
  eval "exec 1>&${stdout} 2>&${stderr}"
  popd &> /dev/null

  local time_e=''
  if [ "${TESTLIB_SHOW_TIMING-0}" == "1" ]; then
    time_e=$(awk "BEGIN {print \"\t\" $(get_time_seconds)-${_time_0}}")
  fi

  if [ ! -e "${TRASHDIR}/.setup_test" ]; then
    # This is a "no matter what, failure". No expected/required failure work
    # around for this
    printf "%-80s ${TEST_BAD_COLOR}SETUP FAILURE${TEST_RESET_COLOR}%s\n" "${test_description}" "${time_e}"
    failures=$(( failures + 1 ))
  elif [ "${__testlib_skip_test-}" = "1" ] && [ "${test_status}" -eq 0 ]; then
    printf "%-80s ${TEST_GOOD_COLOR}SKIPPED${TEST_RESET_COLOR}%s\n" "${test_description}" "${time_e}"
    skipped=$((skipped+1))
  elif [ "${required_fail}" -eq 1 ] && [ "$test_status" -ne 0 ]; then
    printf "%-80s ${TEST_GOOD_COLOR}FAIL REQUIRED${TEST_RESET_COLOR}%s\n" "${test_description}" "${time_e}"
    required_failures=$((required_failures+1))
  elif [ "${required_fail}" -eq 0 ] && [ "$test_status" -eq 0 ]; then
    printf "%-80s ${TEST_GOOD_COLOR}OK${TEST_RESET_COLOR}%s\n" "${test_description}" "${time_e}"
  elif [ "${expected_failure}" -eq 1 ]; then
    printf "%-80s ${TEST_GOOD_COLOR}FAIL EXPECTED${TEST_RESET_COLOR}%s\n" "${test_description}" "${time_e}"
    expected_failures=$(( expected_failures + 1 ))
  else
    failures=$(( failures + 1 ))
    if [ "${required_fail}" -eq 1 ]; then
      printf "%-80s ${TEST_BAD_COLOR}SHOULD HAVE FAILED${TEST_RESET_COLOR}%s\n" "${test_description}" "${time_e}"
    else
      printf "%-80s ${TEST_BAD_COLOR}FAILED${TEST_RESET_COLOR}%s\n" "${test_description}" "${time_e}"
    fi
    (
      echo "-- stdout --"
      sed 's/^/    /' <"${TESTDIR}/out"
      echo "-- stderr --"
      grep -v -e $'^\+[^\t]*\tend_test' \
              -e $'^\+[^\t]*\tset +x -e' <"${TESTDIR}/err" |
        sed $'s|^[^+]| \t&|' |
        column -c1 -s $'\t' -t |
        sed 's/^/    /'
      echo "-- EOF $test_description --"
    ) 1>&2
  fi

  if [ "${tracking_touched_files-}" = "1" ]; then
    cleanup_touched_files
  fi

  unset test_description
  unset __testlib_skip_test

  rm "${TRASHDIR}/.setup_test" || :
}

#****f* testlib.sh/skip_next_test
# NAME
#   skip_next_test - Function to indicate the next test should be skipped
# DESCRIPTION
#   This is the first part of creating a skippable test, used in conjunction
#   with setup_test
# EXAMPLE
#   For example, skip if docker command not found
#
#     command -v docker &>/dev/null && skip_next_test
#     begin_test "My test"
#     (
#       setup_test
#       [ "$(docker run -it --rm ubuntu:14.04 echo hi)" = "hi" ]
#     )
# SEE ALSO
#   testlib.sh/setup_test
# NOTES
#   This must be done outside of the test, or else the skip variable will not
#   be set and detected by end_test
# AUTHOR
#   Andy Neff
#***
skip_next_test()
{
  __testlib_skip_test=1
}

#****f* testlib.sh/not
# NAME
#   not - Returns true only when the command fails
# DESCRIPTION
#   Since ! is ignored by "set -e", use not instead. This is just a helper to
#   make unittests look nice and not need extra ifs everywhere
# INPUTS
#   $1... - Command and arguments
# OUTPUT
#   Return value
#     0 - On non-zero return code evaluation
#     1 - On zero return code
# EXAMPLE
#   # No good, always passes, even if ! true
#   ! false
#
#   # good
#   not false
#   # equivalent to
#   if ! false; then
#     true
#   else
#     false
#   fi
# BUGS
#   Complex statements do not work, e.g. [, [[ and ((, etc...
#   For example, you should use
#     [ ! -e /test ]
#   instead of
#     not [ -e /test ]
#   In cases where this is not easily worked around, you can use
#     not_s '[ -e /test ]'
# SEE ALSO
#   testlib.sh/not_s
# AUTHOR
#   Andy Neff
#***
not()
{
  local cmd="$1"
  shift 1
  if "${cmd}" ${@+"${@}"}; then
    return 1
  else
    return 0
  fi
}

# Testing this idea...
#****f* testlib.sh/not_s
# NAME
#   not_s - Returns true only when the string version of command fails
# DESCRIPTION
#   Since ! is ignored by "set -e", use not instead. This is just a helper to
#   make unittests look nice and not need extra ifs everywhere
# INPUTS
#   $1 - Command/statement in a single string
# OUTPUT
#   Return value
#     0 - On non-zero return code evaluation
#     1 - On zero return code
# EXAMPLES
#   x=test
#   y=t.st
#   not2 '[[ $x =~ $y ]]' # <-- notice single quotes.
#
#   While the single quotes aren't necessary, they handle the more complicated
#   situations more easily
# NOTES
#   Uses eval
# SEE ALSO
#   testlib.sh/not
# AUTHOR
#   Andy Neff
#***
not_s()
{
  eval "if ${1}; then return 1; else return 0; fi"
}

#****f* testlib.sh/track_touched_files
# NAME
#   track_touched_files - Start tracking touched files
# DESCRIPTION
#   After running track_touched_files, any call to touch will cause that file
#   to be added to the internal list (touched_files). Just prior to the teardown
#   phase, all of these files will be automatically removed for your convenience.
# EXAMPLES
#   setup()
#   {
#     track_touched_files
#   }
#   begin_test Testing
#   (
#     touch /tmp/hiya
#   )
#   end_test
# USAGE
#   Should be called before the begin_test block, not inside. Inside a ()
#   subshell block will not work. Setup is the logical place to put it
# BUGS
#   Does not work in sh, only bash. Uses array, and I didn't want to make this
#   use a string instead
#
#   Not thread safe. Use a different file for each thread
# SEE ALSO
#   testlib.sh/cleanup_touched_files
# AUTHOR
#   Andy Neff
#***
track_touched_files()
{
  tracking_touched_files=1
}

#****if* testlib.sh/ttouch
# NAME
#   ttouch - Touch function that should behave like the original touch command
# SEE ALSO
#   testlib.sh/track_touched_files
# AUTHOR
#   Andy Neff
#***
ttouch()
{
  local filename
  local end_options=0

  touch "${@}"

  # Skip all options
  while [ $# -gt 0 ]; do
    if [ "${end_options}" = "0" ] && [ "$1" = "--" ]; then
      end_options=1
      shift 1
    elif [ "${end_options}" = "0" ] && [ ${#1} -gt 0 ] && [ "${1:0:1}" = "-" ]; then
      shift 1
    else
      filename="$1"
      # force to be absolute path
      if [ "${filename:0:1}" != "/" ]; then
        filename="$(pwd)/$1"
      fi
      printf "${filename}\0" >> "${track_touched_file}"
      shift 1
    fi
  done
}

#****if* testlib.sh/cleanup_touched_files
# NAME
#   cleanup_touched_files - Delete all the touched files
# DESCRIPTION
#   At the end of the last test, delete all the files in the array
# AUTHOR
#   Andy Neff
#***
cleanup_touched_files()
{
  local touched_file
  local touched_files
  local line

  # This will normally get called an extra time at exit, so the existence of
  # the file acts as a check.
  if [ -f "${track_touched_file}" ]; then
    while IFS='' read -r -d '' line 2>/dev/null || [ -n "$line" ]; do
      touched_files+=("$line")
      line='' #Have to clear it, in case the timeout times out
    done < "${track_touched_file}"

    for touched_file in ${touched_files+"${touched_files[@]}"}; do
      if [ -e "${touched_file}" ] && [ ! -d "${touched_file}" ]; then
        \rm "${touched_file}"
      fi
    done
  fi
}