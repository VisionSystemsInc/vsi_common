#!/usr/bin/env bash

# INPUTS
#   [$1...] - Test scripts. Default all test-*.sh

set -eu

cd "$(dirname "${BASH_SOURCE[0]}")"

: ${VERBOSE_LOGS=0}
: ${TESTS_PARALLEL=`nproc`}

function atexit()
{
  local rv=${1:-$?}

  if [ "$rv" != "0" ] && [ "$VERBOSE_LOGS" == "1" ]; then
    # if [ -s "$REMOTEDIR/gitserver.log" ]; then
    #   echo ""
    #   echo "gitserver.log:"
    #   cat "$REMOTEDIR/gitserver.log"
    # fi

    echo ""
    echo "env:"
    env
  fi

  # Tests cleanup routine here
  exit $rv
}

# Test setup/initialization routine here


echo "Running this maxprocs=$TESTS_PARALLEL"
echo

if [ $# -eq 0 ]; then
  testfiles=(test-*.sh)
else
  for ((i=1; i<=$#; i++)); do
    testfiles[i]=test-${!i}.sh
  done
fi

# for file in "${testfiles[@]}"; do
#   echo "0$(cat .$(basename $file).time 2>/dev/null || true) $file"
# done | sort -rnk1 | awk '{ print $2 }' | xargs -I % -P $TESTS_PARALLEL -n 1 /bin/sh -c % --batch

for file in "${testfiles[@]}"; do
  printf "./%s\0" "${file}"
done | sort -z | xargs -0 -I % -P $TESTS_PARALLEL -n 1 /bin/sh -c % ${TEST_ARGS+"${TEST_ARGS[@]}"}