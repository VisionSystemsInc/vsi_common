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
#               Added optional teardown
#               Removed PATH
#               Added robodoc documentation
#               Use pushd/popd for each test instead of cd
#               Auto prepend filename to description
#               Added custom PS4
#***
set -e

# create a temporary work space
TRASHDIR="$(mktemp -d -t $(basename "$0")-$$.XXXXXXXX)"

# keep track of num tests and failures
tests=0
failures=0
allowed_failures=0

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
#   Andy Neff - Added teardown
#***
atexit ()
{
  test_status=$?
  [ -n "$test_description" ] && end_test $test_status
  unset test_status

  if type -t teardown &>/dev/null; then
    teardown
  fi

  rm -rf "$TRASHDIR"

  if [ $failures -gt 0 ]; then
    exit 1
  else
    exit 0
  fi
}

# create the trash dir
trap "atexit" EXIT
PS4=$'+${BASH_SOURCE[0]}:${LINENO})\t'

# Common code for begin tests
_begin_common_test ()
{
  pushd "$TRASHDIR" >& /dev/null
  # This make calling end_test between tests "optional", end_test does have to
  # be called after the last test, especially if teardown is defined after the
  # last test
  [ -n "$test_description" ] && end_test $test_status
  unset test_status

  tests=$(( tests + 1 ))
  test_description="$0 - $1"

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
  # This needs to be after _begin_common_test in order to keep end_test optional
  allowed_failure=0
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
  # This needs to be after _begin_common_test in order to keep end_test optional
  allowed_failure=1
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

  if [ "$test_status" -eq 0 ]; then
    printf "test: %-60s OK\n" "$test_description ..."
  elif [ "${allowed_failure}" -eq "1" ]; then
    printf "test: %-60s FAIL OK\n" "$test_description ..."
    allowed_failures=$(( allowed_failures + 1 ))
  else
    failures=$(( failures + 1 ))
    printf "test: %-60s FAILED\n" "$test_description ..."
    (
      echo "-- stdout --"
      sed 's/^/    /' <"$TRASHDIR/out"
      echo "-- stderr --"
      grep -v -e $'^\+[^\t]*\tend_test' \
              -e $'^\+[^\t]*\tset +x -e' <"$TRASHDIR/err" |
        column -c1 -s $'\t' -t |
        sed 's/^/    /'
    ) 1>&2
    echo "-- EOF $test_description --"
  fi
  unset test_description
}

