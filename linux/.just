#!/usr/bin/env false
#!This file should be sourced, NOT run

: ${VSI_COMMON_DIR="$(dirname "${BASH_SOURCE[0]}")/.."}
. "${VSI_COMMON_DIR}/linux/just_common.bsh"
. "${VSI_COMMON_DIR}/linux/isin"
. "${VSI_COMMON_DIR}/linux/dir_tools.bsh"
. "${VSI_COMMON_DIR}/linux/elements.bsh"

##****F* just/.just
# NAME
#   .just - Auto complete for bash
# USAGE
#   source .just
# DESCRIPTION
#   Creates auto complete suggestions based on parsing the Justfile case
#   statements.
#
#   To add customized tab completions, add a .just script next to project
#   Justfile. Write what would normally go inside the complete function to the
#   .just file (without the function header). This file will be sourced every
#   complete after the just_commands, _just_subcommands, _just_subcommands
#   arrays are populated.
# NOTES
#   Source automatically in Bash when sourcing env.bsh
# BUGS
#   Does not work in zsh
# AUTHOR
#   Andy Neff
##***
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
  # 2. Find Justfile: just_functions.bsh/load_justfile
  JUST_DRYRUN_SOURCE=: _just_load_justfile "${JUSTFILE-Justfile}"
  # 3. Emulate finding and adding plugins
  # The last JUST_HELP_FILES is the just file now
  local just_dir="$(\dirname ${JUST_HELP_FILES[${#JUST_HELP_FILES[@]}-1]})"
  _just_get_plugins "${just_dir}"
  for just_plugin in ${JUST_PLUGINS+"${JUST_PLUGINS[@]}"}; do
    JUST_HELP_FILES+=("${just_plugin}")
  done

  # Get all command info once
  local parsed_help_a
  _just_parse_helps ${JUST_HELP_FILES+"${JUST_HELP_FILES[@]}"}
  # Get just command names and remove the comments
  parsed_help_a=("${parsed_help_a[@]%% ${JUST_HELP_SEPARATOR} *}")

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
    . "${just_dir}/.just"
  fi

  # If the last word completed is a subcommand, only match subtargets
  if isin "$3" ${just_subcommands+"${just_subcommands[@]}"} ]; then
    _just_subtargets_from_array "${3}" ${parsed_help_a+"${parsed_help_a[@]}"}
    COMPREPLY+=($(\compgen -W "${just_subtargets[*]}" -- $2))
    return 0
  fi

  # Search for the last subcommand used. If a match is found, add it to the total
  # list of just_commands
  for (( i=${#COMP_WORDS[@]}-1; i>0; i--)); do
    if isin "${COMP_WORDS[$i]}" "${just_subcommands[@]}"; then
      _just_subtargets_from_array "${COMP_WORDS[$i]}" ${parsed_help_a+"${parsed_help_a[@]}"}
      just_commands+=("${just_subtargets[@]}")
      break
    fi
  done

  # Simply just auto complete all commands
  COMPREPLY+=($(\compgen -o bashdefault -W "${just_commands[*]} ${just_subcommands[*]}" -- $2))

  return 0
}

complete -F _just just