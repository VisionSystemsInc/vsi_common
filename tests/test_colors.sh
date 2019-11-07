
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
# .. envvar:: TESTLIB_NO_COLOR
#
# Disable the use of ``ANSI`` colors
#
# In order to disable color test testlib's failing cases, set :envvar:`TESTLIB_NO_COLOR` =1
: ${TESTLIB_GOOD_COLOR=$'\e[1;32m'}
: ${TESTLIB_BAD_COLOR=$'\e[1;31m'}
: ${TESTLIB_WARN_COLOR=$'\e[1;33m'}
: ${TESTLIB_BOLD_COLOR=$'\e[1m'}
: ${TESTLIB_RESET_COLOR=$'\e[m'}

if [ "${TESTLIB_NO_COLOR-0}" == 1 ]; then
  TESTLIB_GOOD_COLOR=''
  TESTLIB_BAD_COLOR=''
  TESTLIB_BOLD_COLOR=''
  TESTLIB_RESET_COLOR=''
fi
#
# .. rubric:: Source
#**
# If it gets more complicated, *consider* using linux/colors.bsh
