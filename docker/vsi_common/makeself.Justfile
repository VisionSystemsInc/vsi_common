#!/usr/bin/env false bash

source "${VSI_COMMON_DIR}/linux/command_tools.bsh"
source "${VSI_COMMON_DIR}/linux/dir_tools.bsh"

#**
# .. function: makeself_git_prep
#
# Helper function for running makeself on git repos
#
# :Arguments: ``$1`` - Relative path of dir to be added to makeself archive; should not start with ``./`` nor end with ``/``. Use ``.`` to denote ``just_project_src_dir``
# :Parameters: ``just_project_src_dir`` - The main project dir. ``$1`` needs to be relative to and a subdirectory of ``just_project_src_dir`
# :Outputs: * ``excluded_files`` - Name of file containing list of filenames to exclude
#           * ``tar_extra`` - Additional tar arguments
#**
function makeself_git_prep()
{
  make_temp_path excluded_files

  # Makeself ~ runs: find {my dir} | xargs tar ${tar_extra} czvf /dist/${MAKESELF_NAME}
  # I need to slip into ${tar_extra} what I want to get it to behave the way I want
  # -T won't work, because it just adds the files I want twice, and all the files I don't want once
  # -X is my only choice
  pushd "${just_project_src_dir}/${1}" > /dev/null

    # 1) Create a list of all untracked files I want ignored
    # a - List all untracked ignored files
    #     "--ignored --exclude-standard" lists ignored files, "--others" makes
    #     it untracked ignored files. In other words: the extra files that show
    #     up in "git status --ignored" as "Untracked files"
    # b - List all untracked files "--others --exclude-standard", except those
    #     that match the exclude filter. In other words: the files that show up
    #     in "git status" as "Untracked files"
    git ls-files --others --ignored --exclude-standard > "${excluded_files}"
    git ls-files --others --exclude-standard >> "${excluded_files}"

    # For no reason --recurse-submodules isn't supported by --others/--ignored
    # c - sed to append path back to filenames
    git submodule --quiet foreach --recursive '(
      git ls-files --others --ignored --exclude-standard;
      git ls-files --others --exclude-standard) | \
      sed "s|^|${displaypath}/|"' >> "${excluded_files}"
  popd > /dev/null

  tar_extra="-X ${excluded_files}"

  # Makeself works by adding a directory to a self-enclosed archive. The path
  # of the directory for the added files always becomes ".". For example, when
  # you call makeself on "/project_dir/external/vsi_common", this path becomes
  # "./" instead of "./external/vsi_common/" in the archive. Transform the path
  # (using --tranform) so the dir has the correct relative path, which is why
  # $1 has to be the relative path, as specified in the documentation.
  # Note: You can't put quotes in tar-extra apparently, it'll screw things up.
  if [ "${1}" != "." ]; then
    # Review: Does this transform (multiple) spaces in the path correctly???
    # Does it handle names with | in it?!
    tar_extra+=" --show-transformed --transform s|^\./|./${1}/|"
  fi
}

function caseify()
{
  local cmd="${1}"
  shift 1

  # git ls-files --other never lists .git, so add an exclusion
  local common_vcs_excludes='--exclude=.git'

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
          --tar-extra "${common_vcs_excludes} --exclude=./docs ../.juste_wrapper" \
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

      local excluded_files
      local tar_extra
      makeself_git_prep $1

      # You can't put quotes in tar-extra apparently, it'll screw things up.
      tar_extra+=" ${common_vcs_excludes} --exclude=./docs"
      if [ "${include_unit_tests}" = "0" ]; then
        tar_extra+=' --exclude=test-*.bsh --exclude=quiz-*.bsh'
      fi

      extra_args+=1
      if [ "$#" -ge "2" ]; then
        tar_extra+=" ${2}"
        extra_args+=1
      fi

      # Start by adding only vsi_common; it will be transformed (due to makeself_git_prep)
      # to have the same relative path as vsi_common_dir really has.
      /makeself/makeself.sh \
          --header /makeself/makeself-header_just.sh \
          --noprogress --nomd5 --nocrc --nox11 --keep-umask \
          --tar-extra "${tar_extra}" \
          "${just_project_src_dir}/${1}" \
          "${just_project_dist_dir}/${MAKESELF_NAME-just}" \
          "${MAKESELF_LABEL-just_label}" \
          "./${1}/freeze/just_wrapper"
      ;;

    # 1 - Relative path to dir of files to add
    # [2] tar_extra flags
    add-git-files) # Append files from a git repo to a makeself executable
      local excluded_files
      local tar_extra
      makeself_git_prep "${1}"

      extra_args=1
      tar_extra+=" ${common_vcs_excludes}"
      if [ "$#" -ge "2" ]; then
        tar_extra+=" ${2}"
        extra_args+=1
      fi

      MAKESELF_PARSE=true /makeself/makeself.sh \
        --header /makeself/makeself-header_just.sh \
        --noprogress --nomd5 --nocrc --nox11 --keep-umask \
        --tar-extra "${tar_extra}" --append \
        "${just_project_src_dir}/${1}" \
        "${just_project_dist_dir}/${MAKESELF_NAME-just}"
      ;;

    add-files) # Append files to a makeself executable
      pushd "${just_project_src_dir}" > /dev/null
        MAKESELF_PARSE=true /makeself/makeself.sh \
            --header /makeself/makeself-header_just.sh \
            --noprogress --nomd5 --nocrc --nox11 --keep-umask \
            --tar-extra "${1-}" --append \
            . "${just_project_dist_dir}/${MAKESELF_NAME-just}"

        if [ -n "${1+set}" ]; then
          extra_args=1
        fi
      popd > /dev/null
      ;;

    *)
      exec "${cmd}" ${@+"${@}"}
      ;;
  esac
}
