#!/usr/bin/env false bash

function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    pyinstaller) # Freeze a python program
      cd /src
      exec pipenv run "${cmd}" ${@+"${@}"}
      ;;
    nopipenv) # Run command not in pipenv
      exec ${@+"${@}"}
      ;;
    *) # Run command in pipenv
      exec pipenv run "${cmd}" ${@+"${@}"}
      ;;
  esac
}
