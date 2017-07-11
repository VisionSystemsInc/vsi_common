#!/usr/bin/env bash

. "$(dirname ${BASH_SOURCE[0]})/testlib.sh"

begin_test "Test test"
(
  set -eu
  
  echo "Working test ${@+${@}}"
)
end_test

begin_fail_test "Test Fail"
(
  set -eu
  
  echo "Fail test ${@+${@}}"
  exit 1
)
end_test
