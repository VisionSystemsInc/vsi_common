#!/usr/bin/env false bash

function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    pyinstaller) # Freeze a python program
      cd /src
      exec "${cmd}" --distpath /dist ${@+"${@}"}
      ;;
    *) # Run command
      exec "${cmd}" ${@+"${@}"}
      ;;
  esac
}
