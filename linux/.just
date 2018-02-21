#!/usr/bin/env false
#!This file should be sourced, NOT run

: ${VSI_COMMON_DIR="$(dirname "${BASH_SOURCE[0]}")/.."}
. "${VSI_COMMON_DIR}/linux/just_common.bsh"
. "${VSI_COMMON_DIR}/linux/isin"
. "${VSI_COMMON_DIR}/linux/dir_tools.bsh"

#****F* just/.just
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
#***
_just()
{
  local JUST_HELP_FILES=("${VSI_COMMON_DIR}/linux/just_functions.bsh")
  local JUST_PLUGINS=()
  local just_plugin

  shopt -s extglob # Why is this needed?

  COMPREPLY=()   # Array variable storing the possible completions.

  # $1 - command aka $0
  # $2 - current word on, can be "" if you just typed a space
  # $3 - last work completed
  # COMP_WORDS - All args

  # Find Justfile
  local file_matches
  parent_find_files "${JUSTFILE-Justfile}"

  if [ "${#file_matches[@]}" -eq 0 ]; then
    echo
    echo "Can't find a suitable configuration file in this directory or any"
    echo "parent. Are you in the right directory?"
    echo
    echo "Supported filenames: \"Justfile\" or value of \${JUSTFILE}"
    return 0
  fi
  JUST_HELP_FILES+=("${file_matches[0]}")

  local just_dir="$(\dirname ${just_file})"

  #Load plugins
  _just_get_plugins "${just_dir}"
  for just_plugin in ${JUST_PLUGINS+"${JUST_PLUGINS[@]}"}; do
    JUST_HELP_FILES+=("${just_plugin}")
  done

  # Get all command info once
  local parsed_help_a
  _just_parse_helps ${JUST_HELP_FILES+"${JUST_HELP_FILES[@]}"}
  #Get just command names
  parsed_help_a=("${parsed_help_a[@]%% *}") #Remove everything after the space in every entry

  #Get main commands only
  local just_commands=()
  local OLD_IFS="${IFS}"
  IFS=$'\n'
  # Remove all entries containing an _, and sort them and remove duplicates
  just_commands=($(sort -u <<< "${parsed_help_a[*]//*_*}"))
  IFS="${OLD_IFS}"

  #Get sub_commands
  local just_subcommands
  IFS=$'\n'
  just_subcommands=($((_just_subcommands_from_array | sort -u ) <<< "${parsed_help_a[*]}"))
  IFS="${OLD_IFS}"

  #Call local .just if it exist
  if [ -f "${just_dir}/.just" ]; then
    . "${just_dir}/.just"
  fi

  # If the last word completed is a subcommand, only match subtargets
  if isin "$3" ${just_subcommands+"${just_subcommands[@]}"} ]; then
    local just_subtargets=()
    _just_subtargets_from_array "${3}" ${parsed_help_a+"${parsed_help_a[@]}"}
    COMPREPLY+=($(\compgen -W "${just_subtargets[*]}" -- $2))
    return 0
  fi

  # search for the last subcommand used. If a match is found, add it to the total
  # list of just_commands
  for (( i=${#COMP_WORDS[@]}; i>=0; i--)); do
    if isin "${COMP_WORDS[$i]}" "${just_subcommands[@]}"; then
      local just_subtargets=()
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