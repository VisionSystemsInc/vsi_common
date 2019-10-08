#!/usr/bin/env false
#This file should be sourced, NOT run!

if [ -z ${VSI_COMMON_DIR+set} ]; then
  VSI_COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd)"
fi
source "${VSI_COMMON_DIR}/linux/just_common.bsh"
source "${VSI_COMMON_DIR}/linux/isin"
source "${VSI_COMMON_DIR}/linux/dir_tools.bsh"
source "${VSI_COMMON_DIR}/linux/elements.bsh"

#*# just/just-tab.rst

#**
# .. default-domain:: bash
#
# ==============
# Tab completion
# ==============
#
# .. file:: .just
#
# *Tab* completion suggestions based on parsing the :file:`Justfile` case statements can easily be added to your bash session by sourcing the :file:`.just` file. This file is sourced for you when you source the :ref:`setup file <just-setup-file>`
#
# The *tab* completion script can be extended by adding a ``.just`` file to your project next to the :file:`Justfile`. Write what would normally go inside the ``complete`` function to the ``.just`` file (without the bash ``function()`` header). This file will be sourced by :file:`.just` after the ``just_commands`` and ``_just_subcommands`` arrays are populated. See :ref:`here <just_autocomplete>` for an example:
#
# The ``.just`` can optionally set a ``JUST_RETURN`` variable that will be stop the execution of the rest of :file:`.just` and return the vaule of ``JUST_RETURN``. This is useful when you do not want the rest of the default behavior in a particular case.
#
# .. seealso::
#
#   :cmd:`just help`
#     Explanation of what is parsed from the :file:`Justfile`
#
# .. warning::
#
#   Does not work in ``zsh``, or any shell other than ``bash``
#**
_just()
{
  local JUST_PLUGINS=()
  local just_plugin
  local i

  shopt -s extglob # Why is this needed?

  COMPREPLY=() # Array variable storing the possible completions.

  # $1 - command aka $0
  # $2 - current word; can be "" if you just typed a space
  # $3 - last word completed
  # COMP_WORDS - All args

  # Emulate how the just systems finds all of its help files

  # 1. Initial files: just_functions.bsh
  local JUST_HELP_FILES=(${JUST_HELP_FILES+"${JUST_HELP_FILES[@]}"})
  if [ "${JUST_HELP_FILES+set}" != "set" ]; then
    JUST_HELP_FILES=("${VSI_COMMON_DIR}/linux/just_functions.bsh")
  fi

  # 2. Find Justfile, load it, and copy the JUST_HELP_FILES array
  local just_files="$(
    _just_load_justfile "${JUSTFILE-Justfile}" >& /dev/null
    join_a just_files ${JUST_HELP_FILES+"${JUST_HELP_FILES[@]}"}
    echo "${just_files}"
  )"
  split_s just_files "${just_files}"
  JUST_HELP_FILES=(${just_files+"${just_files[@]}"})

  # 3. Emulate finding and adding plugins
  # _just_load_justfile should have made the justfile the first entry in JUST_HELP_FILES
  local just_dir="$(dirname "${JUST_HELP_FILES[0]}")"
  _just_get_plugins "${just_dir}"
  for just_plugin in ${JUST_PLUGINS+"${JUST_PLUGINS[@]}"}; do
    JUST_HELP_FILES+=("${just_plugin}")
  done

  # Get all command info once
  local parsed_help_a
  _just_parse_helps ${JUST_HELP_FILES+"${JUST_HELP_FILES[@]}"}
  # Get just command names and remove the comments
  parsed_help_a=("${parsed_help_a[@]%% ${JUST_HELP_SEPARATOR}*}")

  # Get main commands only
  local just_commands=()
  while IFS= read -r -d '' i || [ -n "${i}" ]; do
    # Remove all entries containing an _, and sort them and remove duplicates
    if [[ "${i}" != *_* ]]; then
      just_commands+=("${i}")
    fi
  done < <(MIFS='\\x00' join_a_out "${parsed_help_a[@]}" | sort -u -z)

  # Get sub_commands
  local just_subcommands
  just_subcommands=($(IFS=$'\n'; (_just_subcommands_from_array | sort -u ) <<< "${parsed_help_a[*]}"))

  # Declare here so I can use it in .just plugin
  local just_subtargets=()

  # Call local .just if it exists
  if [ -f "${just_dir}/.just" ]; then
    source "${just_dir}/.just"
    if [ -n "${JUST_RETURN+set}" ]; then
      local just_return="${JUST_RETURN}"
      unset JUST_RETURN
      return ${JUST_RETURN}
    fi
  fi

  # If the last word completed is a subcommand, only match subtargets
  if isin "$3" ${just_subcommands+"${just_subcommands[@]}"} ]; then
    _just_subtargets_from_array "${3}" ${parsed_help_a+"${parsed_help_a[@]}"}
    COMPREPLY+=($(\compgen -W "${just_subtargets+${just_subtargets[*]}}" -- $2))
    return 0
  fi

  # Search for the last subcommand used. If a match is found, add it to the total
  # list of just_commands
  for (( i=${#COMP_WORDS[@]}-1; i>0; i--)); do
    if isin "${COMP_WORDS[$i]}" "${just_subcommands[@]}"; then
      _just_subtargets_from_array "${COMP_WORDS[$i]}" ${parsed_help_a+"${parsed_help_a[@]}"}
      just_commands+=(${just_subtargets+"${just_subtargets[@]}"})
      break
    fi
  done

  # Simply just auto complete all commands
  COMPREPLY+=($(\compgen -o bashdefault -W "${just_commands+${just_commands[*]}} ${just_subcommands+${just_subcommands[*]}}" -- $2))

  return 0
}

# https://stackoverflow.com/a/19062943/4166604
if ! command -v compopt &> /dev/null; then
  # While this won't allow compopt to behave the way we always want on bash 3.2
  # It's the best "default" behavior
  complete -o default -F _just just
else
  complete -F _just just
fi