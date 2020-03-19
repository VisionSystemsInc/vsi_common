# If test is the last completed word, aka test+space
if [ "${3}" = "test" ] ||
   # Or if test was any of the previous words. However, do not accept test as
   # the last COMP_WORDS because that means there is no space after it, so
   # things like testlib will be matched, which is not what we want yet
   isin test "${COMP_WORDS[@]:0:${#COMP_WORDS[@]}-1}}"; then

  # WARNING: This could explode if a test name has a wildcard, luckily it never would.
  pushd "${VSI_COMMON_DIR}/tests/" &> /dev/null
    just_subtargets=(test-*.bsh)
  popd &> /dev/null
  just_subtargets=("${just_subtargets[@]#*/test-}")
  just_subtargets=("${just_subtargets[@]%*.bsh}")
fi
