#!/usr/bin/env bash

. "$(dirname ${BASH_SOURCE[0]})/testlib.sh"

d=$(mktemp)

begin_test "Element test"
(
  set -eu
  echo foo
)
end_test

function teardown
{
  :
}