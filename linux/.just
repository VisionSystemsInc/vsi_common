#!/usr/bin/env false
#!This file should be sourced, NOT run

. "${VSI_COMMON_DIR}/linux/just_common.bsh"

# _just_all_commands()
# {
#   #Replace \\\n with a space
#   \awk -v RS='\0' -v ORS= '{gsub(/\\\n/," ")}1' "${1}" |
#   # Match all commands lines
#   \grep -E '^ *[a-zA-Z0-9 |_\-]+\)' |
#   # Remove trailing and beginning 
#   \sed -E 's#^ *([a-zA-Z0-9 |_\-]+)\).*#\1#' |
#   # Convert | to newlines so I have a clean line per command
#   \sed 's# *| *#\n#g'
# }

# _just_commands()
# {
#   #Remove underscore commands, those are subcommands
#   just_commands+=($(_just_all_commands "${1}" | \grep -v _))
# }

# _just_add_subcommands()
# {
#   just_subcommands+=($(_just_all_commands "${1}" | 
#                        \grep -E '^[a-z0-9\-]+_[a-z0-9_\-]+$' |
#                        \sed -E 's|^([a-z0-9\-]+)_([a-z0-9_\-]+)|\1\t\2|'))
# }

# _just_get_subtargets()
# {
#   for i in "${!_just_subtargets[@]}"; do
#     if [ "${_just_subcommands[$i]}" == "$1" ]; then
#       subtargets+=("${_just_subtargets[$i]}")
#     fi
#   done
# }

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
  #_just_commands "${just_file}"
  #_just_commands "${VSI_COMMON_DIR}/linux/just_functions.bsh"
  IFS=$'\n'
  # Remove all entries containing an _, and sort them and remove duplicates
  just_commands=($(sort -u <<< "${all_commands[*]//*_*}"))
  IFS="${OLD_IFS}"

  #Get sub_commands
  local just_subcommands
  #$(\grep -E '^ +[a-z0-9\-]+_[a-z0-9\-]+\)' "${just_file}" | \sed -E 's|^ +([a-z0-9\-]+)_([a-z0-9\-]+)\).*|\1\t\2|'))
  #_just_add_subcommands "${just_file}"
  #_just_add_subcommands "${VSI_COMMON_DIR}/linux/just_functions.bsh"
  IFS=$'\n'
  just_subcommands=($((_just_subcommands_from_array | sort -u ) <<< "${all_commands[*]}"))
  IFS="${OLD_IFS}"
#   local _just_subtargets=()
#   local _just_subcommands=()

#   #Determine sub commands' targets
#   local i
#   for i in $(seq 1 2 ${#just_subcommands[@]}); do
#     _just_subcommands+=("${just_subcommands[$((i-1))]}")
#     _just_subcommands+=("${just_subcommands[$i]}")
#   done
#   . 

#   _just_commands_from_file
declare -p all_commands
declare -p just_commands
declare -p just_subcommands
# return

  #Make subcommand pattern for case statement
  #just_subcommands=$(echo "${_just_subcommands[@]}" | \tr ' ' '\n' | \sort -u | \tr '\n' '|')
  #just_subcommands="@(${just_subcommands::-1})" #remove trailing |


  #Call local .just if it exist
  local just_dir="$(\dirname ${just_file})"
  if [ -f "${just_dir}/.just" ]; then
    . "${just_dir}/.just"
  fi

  if [ "${just_subcommands}" != "" ]; then
echo "Subcommand detected: $3"
    case "$3" in 
      ${just_subcommands})
        local subtargets=()
        #_just_get_subtargets "$3" caseify
        _just_subtargets_from_array "${3}" ${all_commands+"${all_commands[@]}"}
declare -p just_subtargets
        COMPREPLY+=($(\compgen -W "${subtargets[*]}" -- $2))
        return 0
        ;;
    esac
  fi

  for (( i=${#COMP_WORDS[@]}; i>=0; i--)); do
    if isin "${COMP_WORDS[$i]}" "${_just_subcommands[@]}"; then
echo "Subcommand detected2: $3"
      local subtargets=()
      #_just_get_subtargets "${COMP_WORDS[$i]}" caseify
      _just_subtargets_from_array "${COMP_WORDS[$i]}" ${all_commands+"${all_commands[@]}"}
declare -p just_subtargets
      just_commands+=("${subtargets[@]}")
      break
    fi
  done

  # Simply just auto complete all commands
  COMPREPLY+=($(\compgen -o bashdefault -W "${just_commands[*]} ${_just_subcommands[*]}" -- $2))

  return 0

}

complete -F _just just