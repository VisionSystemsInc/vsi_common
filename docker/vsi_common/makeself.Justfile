#!/usr/bin/env false bash

source "${VSI_COMMON_DIR}/linux/command_tools.bsh"
source "${VSI_COMMON_DIR}/linux/dir_tools.bsh"

function caseify()
{
  local cmd="${1}"
  shift 1

  # git ls-files --other never lists .git, so add an exclusion
  local vsi_common_excludes='--exclude=./docs --exclude=.git'

  local just_project_src_dir="${JUST_PROJECT_PREFIX}_MAKESELF_SRC_DIR"
  just_project_src_dir="${!just_project_src_dir}"
  local just_project_dist_dir="${JUST_PROJECT_PREFIX}_MAKESELF_DIST_DIR"
  just_project_dist_dir="${!just_project_dist_dir}"

  case "${cmd}" in
    juste) # Make a pure just executable, not a project executable (Not finished. .juste_wrapper needs to be merged into just_wrapper)
      pushd "${just_project_src_dir}" > /dev/null
        mkdir -p "${just_project_dist_dir}"
        /makeself/makeself.sh \
          --header /makeself/makeself-header_just.sh \
          --noprogress --nomd5 --nocrc --nox11 --keep-umask \
          --tar-extra "${vsi_common_excludes} ../.juste_wrapper" \
          vsi_common/ "${just_project_dist_dir}/juste" juste_label ./.juste_wrapper
      popd > /dev/null
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
      shift "${extra_args}"

      # Review: Does the transform below handle (multiple) spaces in the path correctly???
      local vsi_common_rel="${1}"

      local excluded_files
      make_temp_path excluded_files

      # Makeself ~ runs: find {my dir} | xargs tar ${tar_extra} czvf /dist/${MAKESELF_NAME}
      # I need to slip into ${tar_extra} what I want to get it to behave the way I want
      # -T won't work, because it just adds the files I want twice, and all the files I don't want once
      # -X is my only choice
      pushd "${just_project_src_dir}/${vsi_common_rel}" > /dev/null

        # 1) Create a list of files I want ignore
        # a - list all ignored files
        #     --ignored lists TRACKED files that match the ignore filter,
        #     adding --other makes it untracked ignored files
        # b - list all untracked files (--others)
        git ls-files --others --ignored --exclude-standard > "${excluded_files}"
        git ls-files --others --exclude-standard >> "${excluded_files}"

        # For no reason --recurse-submodules isn't supported by --others/--ignored
        # c - sed to append path back to filenames
        git submodule --quiet foreach --recursive '(
          git ls-files --others --ignored --exclude-standard;
          git ls-files --others --exclude-standard) | \
          sed "s|^|${displaypath}/|"' >> "${excluded_files}"
      popd > /dev/null

      # Transform the path, so the vsi dir appears where it really is, wrt to the
      # base repo
      local tar_extra="${vsi_common_excludes}"
      if [ "${vsi_common_rel}" != "." ]; then
        tar_extra+=" --show-transformed --transform s|^\./|./${vsi_common_rel}/|"
      fi
      tar_extra+=" -X ${excluded_files}"
      if [ "${include_unit_tests}" = "0" ]; then
        tar_extra+=' --exclude=test-*.bsh --exclude=quiz-*.bsh'
      fi

      # Start by adding just vsi_common, and transform it to have the same relative path as vsi_common_dir really has.
      /makeself/makeself.sh \
          --header /makeself/makeself-header_just.sh \
          --noprogress --nomd5 --nocrc --nox11 --keep-umask \
          --tar-extra "${tar_extra}" \
          "${just_project_src_dir}/${vsi_common_rel}" \
          "${just_project_dist_dir}/${MAKESELF_NAME-just}" \
          "${MAKESELF_LABEL-just_label}" \
          "./${vsi_common_rel}/freeze/just_wrapper"
      # You can't put quotes in tar-extra apparently, it'll screw things up.

      extra_args+=1
      ;;
    # 1 - Relative path to dir of files to add
    # [2] tar_extra flags
    add-git-files) # Append files to a makeself executable
      local git_dir_rel="${1}"

      local excluded_files
      make_temp_path excluded_files

      pushd "${just_project_src_dir}/${git_dir_rel}" > /dev/null
        (git ls-files --others --ignored --exclude-standard;
         git ls-files --others --exclude-standard |
         sed "s|^|${git_dir_rel}/|") > "${excluded_files}"

        # For no reason --recurse-submodules isn't supported by --others/--ignored
        git submodule --quiet foreach --recursive '(
          git ls-files --others --ignored --exclude-standard;
          git ls-files --others --exclude-standard) | \
          sed "s|^|${vsi_common_rel}/${displaypath}/|"' >> "${excluded_files}"
      popd > /dev/null

      local tar_extra="--exclude=.git"
      if [ "${git_dir_rel}" != "." ]; then
        tar_extra+=" --show-transformed --transform s|^\./|./${git_dir_rel}/|"
      fi
      tar_extra+=" -X ${excluded_files}"
      tar_extra+=" ${2-}"

      MAKESELF_PARSE=true /makeself/makeself.sh \
        --header /makeself/makeself-header_just.sh \
        --noprogress --nomd5 --nocrc --nox11 --keep-umask \
        --tar-extra "${tar_extra}" --append \
        "${just_project_src_dir}/${git_dir_rel}" \
        "${just_project_dist_dir}/${MAKESELF_NAME-just}"

      extra_args=$#
      ;;

    add-files) # Append files to a makeself executable
      pushd "${just_project_src_dir}" > /dev/null
        MAKESELF_PARSE=true /makeself/makeself.sh \
            --header /makeself/makeself-header_just.sh \
            --noprogress --nomd5 --nocrc --nox11 --keep-umask \
            --tar-extra "${1-}" --append \
            . "${just_project_dist_dir}/${MAKESELF_NAME-just}"

        extra_args=$#
      popd > /dev/null
      ;;

    *)
      exec "${cmd}" ${@+"${@}"}
      ;;
  esac
}
