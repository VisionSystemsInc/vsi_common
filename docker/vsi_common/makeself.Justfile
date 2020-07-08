#!/usr/bin/env false bash

source "${VSI_COMMON_DIR}/linux/command_tools.bsh"

function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    makeself)
      cd /src
      mkdir -p /src/dist
      /makeself/makeself.sh --tar-extra "--exclude=.git --exclude=docs ../.juste_wrapper" --noprogress --nomd5 --nocrc --nox11 --keep-umask --header /makeself/makeself-header_just.sh vsi_common/ /src/dist/juste juste_label ./.juste_wrapper
      ;;

    just-project) # Make a self extracting executable for a just \
        # project, locally. Add "--tests" flag to include VSI Common's unit tests. \
        # Unit tests can be run via: just --wrap bash -c 'cd ${VSI_COMMON_DIR}; just test'
      local include_unit_tests
      parse_args extra_args --tests include_unit_tests -- ${@+"${@}"}
      if [ "${include_unit_tests}" = "0" ]; then
        include_unit_tests='--exclude=test-*.bsh'
      else
        include_unit_tests=""
      fi

      # Review: Does the transform below handle (multiple) spaces in the path correctly???
      local vsi_common_rel="${1}"

      # Start by adding just vsi_common, and transform it to have the same relative path as vsi_common_dir really has.
      "/makeself/makeself.sh" \
          --header "/makeself/makeself-header_just.sh" \
          --noprogress --nomd5 --nocrc --nox11 --keep-umask \
          --tar-extra "--show-transformed --transform s|^\./|./${vsi_common_rel}/| ${include_unit_tests} --exclude=./docs --exclude=.git --exclude=*.egg-info" \
          "${VSI_COMMON_DIR}" /dist/just just_label "./${vsi_common_rel}/freeze/just_wrapper"
      # You can't put quotes in tar-extra apparently, it'll screw things up.

      extra_args=1
      ;;
    add-files) # Append files to a makeself executable
      pushd /src &> /dev/null
        MAKESELF_PARSE=true "/makeself/makeself.sh" \
            --header "/makeself/makeself-header_just.sh" \
            --noprogress --nomd5 --nocrc --nox11 --keep-umask \
            --tar-extra "${1-}" --append \
            . /dist/just

        extra_args=$#
      popd &> /dev/null
      ;;

    *)
      exec "${cmd}" ${@+"${@}"}
      ;;
  esac
}
