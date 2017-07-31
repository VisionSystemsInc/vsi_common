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
# COPYRIGHT
#   Original version: (c) 2011-13 by Ryan Tomayko <http://tomayko.com>
#   License: MIT
# AUTHOR
#   Ryan Tomayko
# MODIFICATION HISTORY
#   Andy Neff - Added begin_fail_test
#               Added optional setup/teardown functions
#               Added SETUPDIR
#               Removed PATH
#               Added robodoc documentation
#               Use pushd/popd for each test instead of cd
#               Auto prepend filename to description
#               Added custom PS4
#***
set -e

# create a temporary work space
TRASHDIR="$(mktemp -d -t $(basename "$0")-$$.XXXXXXXX)"
SETUPDIR="$(mktemp -d -t $(basename "$0")-$$.XXXXXXXX)"

# keep track of num tests and failures
tests=0
failures=0
allowed_failures=0
must_failures=0
skipped=0

#****f* testlib.sh/setup
# NAME
#   setup - Function run before the first test
# NOTES
#   A directory SETUPDIR is created for setup, right before running setup().
#   Unlike TRASHDIR, this single directory is used for all the tests in the
#   file.
#
#   Setup is not run if no tests are ever run
# AUTHOR
#   Andy Neff
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
  [ -n "$test_description" ] && end_test $test_status
  unset test_status

  if [ "${tests}" -ne "0" ] && type -t teardown &>/dev/null; then
    teardown
  fi

  if [ "${TEST_KEEP_TEMP_DIRS}" != "1" ]; then
    rm -rf "$TRASHDIR"
    rm -rf "$SETUPDIR"
  fi

  printf '%s summary: %d test ran, %d failures, %d allowed failures, %d must fails, %d skipped\n' \
         "$0" "${tests}" "${failures}" "${allowed_failures}" "${must_failures}" "${skipped}"

  if [ $failures -gt 0 ]; then
    exit 1
  else
    exit 0
  fi
}

# create the trash dir
trap "atexit" EXIT
if declare -p BASH_SOURCE &>/dev/null; then
  PS4=$'+${BASH_SOURCE-null}:${LINENO})\t'
else
  #Not as accurate, but better than nothing
  PS4=$'+${0}:${LINENO})\t'
fi

# Common code for begin tests
_begin_common_test ()
{
  pushd "$TRASHDIR" >& /dev/null
  # This make calling end_test between tests "optional", end_test does have to
  # be called after the last test, especially if teardown is defined after the
  # last test
  [ -n "$test_description" ] && end_test $test_status
  unset test_status

  # Set flag defaults that could be overrideable in certain test types
  # This needs to be after end_test call above in order to keep end_test
  # optional
  allowed_failure=0
  must_fail=0

  # Run setup if this is the first test
  if [ "${tests}" -eq "0" ] && type -t setup &>/dev/null; then
    setup
  fi

  tests=$(( tests + 1 ))
  local test_file_name="$(basename "$0")"
  test_file_name=${test_file_name%.*}
  test_file_name=${test_file_name#test-}
  test_description="$test_file_name - $1"

  exec 3>&1 4>&2
  out="$TRASHDIR/out"
  err="$TRASHDIR/err"
  exec 1>"$out" 2>"$err"

  # allow the subshell to exit non-zero without exiting this process
  set -x +e
}

#****f* testlib.sh/begin_test
# NAME
#   begin_test - Beginning of test demarcation
# USAGE
#   Mark the beginning of a test. A subshell should immediately follow this
#   statement.
# AUTHOR
#   Ryan Tomayko
#***
begin_test ()
{
  test_status=$? # Must be first command
  _begin_common_test ${@+"${@}"}
}

#****f* testlib.sh/begin_fail_test
# NAME
#   begin_fail_test - Beginning of failable test demarcation
# USAGE
#   Define the beginning of a test that is allowed to fail
# AUTHOR
#   Andy Neff
#***
begin_fail_test()
{
  test_status=$? # Must be first command
  _begin_common_test ${@+"${@}"}
  # Override _begin_common_test default
  allowed_failure=1
}

#****f* testlib.sh/begin_must_fail_test
# NAME
#   begin_must_fail_test - Beginning of fail required test demarcation
# USAGE
#   Define the beginning of a test that is required to fail
# AUTHOR
#   Andy Neff
#***
begin_must_fail_test()
{
  test_status=$? # Must be first command
  _begin_common_test ${@+"${@}"}
  # Override _begin_common_test default
  must_fail=1
}


#****f* testlib.sh/begin_test
# NAME
#   begin_test - End of a test demarcation
# USAGE
#   Mark the end of a test.
# AUTHOR
#   Ryan Tomayko
#***
end_test ()
{
  test_status="${1:-$?}" #This MUST be the first line of this function
  set +x -e
  exec 1>&3 2>&4
  popd >& /dev/null

  if [ "${skip_next_test-}" = "1" ] && [ "${test_status}" -eq 122 ]; then
    printf "%-80s SKIPPED OK\n" "$test_description ..."
    skipped=$((skipped+1))
  elif [ "${must_fail}" -eq 1 ] && [ "$test_status" -ne 0 ]; then
    printf "%-80s FAILED OK\n" "$test_description ..."
    must_failures=$((must_failures+1))
  elif [ "${must_fail}" -eq 0 ] && [ "$test_status" -eq 0 ]; then
    printf "%-80s OK\n" "$test_description ..."
  elif [ "${allowed_failure}" -eq 1 ]; then
    printf "%-80s FAIL OK\n" "$test_description ..."
    allowed_failures=$(( allowed_failures + 1 ))
  else
    failures=$(( failures + 1 ))
    printf "%-80s FAILED\n" "$test_description ..."
    (
      echo "-- stdout --"
      sed 's/^/    /' <"$TRASHDIR/out"
      echo "-- stderr --"
      grep -v -e $'^\+[^\t]*\tend_test' \
              -e $'^\+[^\t]*\tset +x -e' <"$TRASHDIR/err" |
        sed $'s|^[^+]| \t&|' |
        column -c1 -s $'\t' -t |
        sed 's/^/    /'
      echo "-- EOF $test_description --"
    ) 1>&2
  fi
  unset test_description
  unset skip_next_test
}

#****f* testlib.sh/skip_next_test
# NAME
#   skip_next_test - Function to indicate the next test should be skipped
# DESCRIPTION
#   This is the first part to creating a skippable test, used in conjunction
#   with check_skip
# EXAMPLE
#   For exampled, skip of docker command not found
#
#     if command -v docker > /dev/null 2>&1 ; then
#       skip_next_test
#     fi
# SEE ALSO
#   testlib.sh/check_skip
# AUTHOR
#   Andy Neff
#***
skip_next_test()
{
  skip_next_test=1
}

#****f* testlib.sh/check_skip
# NAME
#   check_skip - Check to see if this test should be skipped
# DESCRIPTION
#   This is the second part to creating a skippable test. Place at the beginning
#   of a test
# EXAMPLE
#   skip_next_test
#   begin_test "Skipping test"
#   (
#     check_skip
#     #test code here
#   )
# AUTHOR
#   Andy Neff
#***
check_skip()
{
  if [ "${skip_next_test-}" = "1" ]; then
    exit 122
  fi
}