#!/usr/bin/env false
#!This file should be sourced, NOT run

_just_find_justfile()
{
  local just_tmp_last_node=
  local just_tmp_stat_command=
  if [ "$(\uname)" == "Darwin" ]; then
    just_tmp_stat_command="stat -f %d:%i ."
  else
    just_tmp_stat_command="stat -c %d:%i ."
  fi
  \pushd . > /dev/null
  while [ "${just_tmp_last_node}" != "$(\eval ${just_tmp_stat_command})" ]; do
    if [ -f "${1}" ]; then
      \echo "$(\cd "$(\dirname "${1}")"; \pwd)/$(\basename "${1}")"
      break
    fi
    just_tmp_last_node=$(\eval ${just_tmp_stat_command})
    \cd ..
  done
  \popd > /dev/null
}

_just_commands()
{
  just_commands+=($(\grep -E '^ +[a-z0-9|\-]+\)|^ +[_a-z0-9|\-]+\) *#' "${1}" |
                    \sed -E 's|^ *([_a-z0-9|\-]+)\).*|\1|' |
                    \tr '|' ' '))
}

_just_add_subcommands()
{
  just_subcommands+=($(\grep -E '^ +[a-z0-9\-]+_[a-z0-9\-]+\)' "${1}" |
                       \sed -E 's|^ +([a-z0-9\-]+)_([a-z0-9\-]+)\).*|\1\t\2|'))
}

_just_get_subtargets()
{
  for i in "${!_just_subtargets[@]}"; do
    if [ "${_just_subcommands[$i]}" == "$1" ]; then
      subtargets+=("${_just_subtargets[$i]}")
    fi
  done
}

_just()
{
  shopt -s extglob

  COMPREPLY=()   # Array variable storing the possible completions.

  # $1 - command aka $0
  # $2 - current word on, can be "" if you just typed a space
  # $3 - last work completed
  # COMP_WORDS - All args

  # Find Justfile
  local just_file=$(_just_find_justfile "${JUSTFILE-Justfile}")

  #Get commands
  local just_commands=()
  _just_commands "${just_file}"
  _just_commands "$(\dirname "${BASH_SOURCE[0]}")/just_functions.bsh"

  #Get sub_commands
  local just_subcommands=()
  #$(\grep -E '^ +[a-z0-9\-]+_[a-z0-9\-]+\)' "${just_file}" | \sed -E 's|^ +([a-z0-9\-]+)_([a-z0-9\-]+)\).*|\1\t\2|'))
  _just_add_subcommands "${just_file}"
  _just_add_subcommands "$(\dirname "${BASH_SOURCE[0]}")/just_functions.bsh"
  local _just_subtargets=()
  local _just_subcommands=()

  #Determine sub commands' targets
  local i
  for i in $(seq 1 2 ${#just_subcommands[@]}); do
    _just_subcommands+=("${just_subcommands[$((i-1))]}")
    _just_subtargets+=("${just_subcommands[$i]}")
  done

  #Make subcommand pattern for case statement
  just_subcommands=$(echo "${_just_subcommands[@]}" | \tr ' ' '\n' | \sort -u | \tr '\n' '|')
  just_subcommands="@(${just_subcommands::-1})" #remove trailing |

  #Call local .just if it exist
  if [ -f "$(\dirname ${just_file})/.just" ]; then
    local just_local=1
    . "$(\dirname ${just_file})/.just"
    if [ "${just_local}" == "0" ]; then
      return 0
    fi
  fi

  if [ "${just_subcommands}" != "" ]; then
    case "$3" in 
      ${just_subcommands})
        local subtargets=()
        _just_get_subtargets "$3"
        COMPREPLY+=($(\compgen -W "${subtargets[*]}" -- $2))
        return 0
        ;;
    esac
  fi

  for (( i=${#COMP_WORDS[@]}; i>=0; i--)); do
    if isin "${COMP_WORDS[$i]}" "${_just_subcommands[@]}"; then
      local subtargets=()
      _just_get_subtargets "${COMP_WORDS[$i]}"
      just_commands+=("${subtargets[@]}")
      break
    fi
  done

  # Simply just auto complete all commands
  COMPREPLY+=($(\compgen -o bashdefault -W "${just_commands[*]} ${_just_subcommands[*]}" -- $2))

  return 0

}

complete -F _just just