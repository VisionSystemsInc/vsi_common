# If test is the last completed word, aka test+space
if [ "${3}" = "test" ] ||
   # Or if test was any of the previous words. however, do not accept test as
   # the last COMP_WORDS because that means there is no space after it, so
   # things like testlib will be matched, which is not what we want yet
   isin test "${COMP_WORDS[@]:0:${#COMP_WORDS[@]}-1}}"; then

  just_subtargets=($(ls ${VSI_COMMON_DIR}/tests/test-*.bsh))
  just_subtargets=("${just_subtargets[@]#*/test-}")
  just_subtargets=("${just_subtargets[@]%*.bsh}")
fi
