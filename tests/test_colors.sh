
#*# tests/test_colors

#**
# ===========
# Test Colors
# ===========
#
# .. default-domain:: bash
#
# .. file:: test_colors.sh
#
# Color definitions for testlib
#**

#**
# .. envvar:: TEST_NO_COLOR
#
# Disable the use of ``ANSI`` colors
#
# In order to disable color test testlib's failing cases, set :envvar:`TEST_NO_COLOR` =1
: ${TEST_GOOD_COLOR=$'\e[1;32m'}
: ${TEST_BAD_COLOR=$'\e[1;31m'}
: ${TEST_WARN_COLOR=$'\e[1;33m'}
: ${TEST_BOLD_COLOR=$'\e[1m'}
: ${TEST_RESET_COLOR=$'\e[m'}

if [ "${TEST_NO_COLOR-0}" == 1 ]; then
  TEST_GOOD_COLOR=''
  TEST_BAD_COLOR=''
  TEST_BOLD_COLOR=''
  TEST_RESET_COLOR=''
fi
#
# .. rubric:: Source
#**
# If it gets more complicated, *consider* using linux/colors.bsh
