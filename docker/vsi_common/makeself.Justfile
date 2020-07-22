#!/usr/bin/env false bash

source "${VSI_COMMON_DIR}/linux/command_tools.bsh"

function caseify()
{
  local cmd="${1}"
  shift 1

  local vsi_common_excludes='--exclude=./docs --exclude=.git --exclude=*.egg-info'

  case "${cmd}" in
    juste) # Make a pure just executable, not a project executable (Not finished. .juste_wrapper needs to be merged into just_wrapper)
      cd /src
      mkdir -p /src/dist
      /makeself/makeself.sh \
        --header /makeself/makeself-header_just.sh \
        --noprogress --nomd5 --nocrc --nox11 --keep-umask \
        --tar-extra "${vsi_common_excludes} ../.juste_wrapper" \
        vsi_common/ /src/dist/juste juste_label ./.juste_wrapper
      ;;

    makeself) # Run makeself
      /makeself/makeself.sh ${@+"${@}"}
      extra_args=$#
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
      /makeself/makeself.sh \
          --header /makeself/makeself-header_just.sh \
          --noprogress --nomd5 --nocrc --nox11 --keep-umask \
          --tar-extra "--show-transformed --transform s|^\./|./${vsi_common_rel}/| ${include_unit_tests} ${vsi_common_exlcudes}" \
          "${VSI_COMMON_DIR}" "/dist/${MAKESELF_NAME-just}" "${MAKESELF_LABEL-just_label}" "./${vsi_common_rel}/freeze/just_wrapper"
      # You can't put quotes in tar-extra apparently, it'll screw things up.

      extra_args=1
      ;;
    add-files) # Append files to a makeself executable
      pushd /src &> /dev/null
        MAKESELF_PARSE=true /makeself/makeself.sh \
            --header /makeself/makeself-header_just.sh \
            --noprogress --nomd5 --nocrc --nox11 --keep-umask \
            --tar-extra "${1-}" --append \
            . "/dist/${MAKESELF_NAME-just}"

        extra_args=$#
      popd &> /dev/null
      ;;

    *)
      exec "${cmd}" ${@+"${@}"}
      ;;
  esac
}
