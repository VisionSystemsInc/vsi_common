#!/usr/bin/env false
#!This file should be sourced, NOT run

. "${VSI_COMMON_DIR}/linux/just_common.bsh"

_just()
{
  shopt -s extglob

  COMPREPLY=()   # Array variable storing the possible completions.

  # $1 - command aka $0
  # $2 - current word on, can be "" if you just_file typed a space
  # $3 - last work completed
  # COMP_WORDS - All args

  # Find Justfile
  local just_file=$(_just_find_justfile "${JUSTFILE-Justfile}")

  if [ "${just_file}" == "" ]; then
    echo 
    echo "Can't find a suitable configuration file in this directory or any"
    echo "parent. Are you in the right directory?"
    echo
    echo "Supported filenames: \"Justfile\" or value of \${JUSTFILE}"
    return 0
  fi

  # Get all command info once
  local all_commands
  local OLD_IFS="${IFS}"
  IFS=$'\n|'
  all_commands=($(_just_commands_from_file "${just_file}"))
  all_commands+=($(_just_commands_from_file "${VSI_COMMON_DIR}/linux/just_functions.bsh"))
  IFS="${OLD_IFS}"
  #Get just command names
  all_commands=("${all_commands[@]%% *}") #Remove everything after the space in every entry
  
  
  #Get main commands only
  local just_commands=()
  IFS=$'\n'
  # Remove all entries containing an _, and sort them and remove duplicates
  just_commands=($(sort -u <<< "${all_commands[*]//*_*}"))
  IFS="${OLD_IFS}"

  #Get sub_commands
  local just_subcommands
  IFS=$'\n'
  just_subcommands=($((_just_subcommands_from_array | sort -u ) <<< "${all_commands[*]}"))
  IFS="${OLD_IFS}"

  #Call local .just if it exist
  local just_dir="$(\dirname ${just_file})"
  if [ -f "${just_dir}/.just" ]; then
    . "${just_dir}/.just"
  fi

  # If the last word completed is a subcommand, only match subtargets
  if isin "$3" ${just_subcommands+"${just_subcommands[@]}"} ]; then
    local just_subtargets=()
    _just_subtargets_from_array "${3}" ${all_commands+"${all_commands[@]}"}
    COMPREPLY+=($(\compgen -W "${just_subtargets[*]}" -- $2))
    return 0
  fi

  # search for the last subcommand used. If a match is found, add it to the total
  # list of just_commands
  for (( i=${#COMP_WORDS[@]}; i>=0; i--)); do
    if isin "${COMP_WORDS[$i]}" "${just_subcommands[@]}"; then
      local just_subtargets=()
      _just_subtargets_from_array "${COMP_WORDS[$i]}" ${all_commands+"${all_commands[@]}"}
      just_commands+=("${just_subtargets[@]}")
      break
    fi
  done

  # Simply just auto complete all commands
  COMPREPLY+=($(\compgen -o bashdefault -W "${just_commands[*]} ${just_subcommands[*]}" -- $2))

  return 0

}

complete -F _just just