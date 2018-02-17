#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then #If being sourced
  set -euE
fi

JUST_PROJECT_PREFIX=VSI_COMMON
source "$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd)/wrap"
cd "$(\dirname "${BASH_SOURCE[0]}")"

source "${VSI_COMMON_DIR}/linux/just_robodoc_functions.bsh"

function caseify()
{
  local just_arg=$1
  shift 1
  case ${just_arg} in
    checkout-just)
      (
        cd "${VSI_COMMON_DIR}"
        # Enable the just submodule
        git config "submodule.internal/just.update" checkout
        git submodule init internal/just
        git submodule update internal/just
      )
      ;;
    tag-just)
      (
        # Get a list of all the files that make up just
        shopt -s dotglob
        shopt -s nocaseglob

        just_files=(linux/*just*)
        support_files=(linux/elements.bsh linux/linux_accounts.bsh linux/mount_tools.bsh linux/docker_compose_override)
        for f in $(ls -I '*just*' -I '*Just*' linux); do
          if grep -q "${f}" "${just_files[@]}"; then
            support_files+=("linux/${f}")
          fi
        done
        # And copy them over
        cp env.bsh "${just_files[@]}" "${support_files[@]}" internal/just/
        cp docker/vsi_common/docker-compose.yml internal/just/robodoc.yml

        # Refactor the code to stand alone
        # Remove unused feature in just
        sed -i -e '/PYTHONPATH/d' -e '/MATLABPATH/d' internal/just/env.bsh
        # Rebrand VSI_COMMON_DIR
        sed -i 's|VSI_COMMON_DIR|JUST_DIR|g' internal/just/*
        # Flatten dir structure
        sed -i 's|${JUST_DIR}/linux|${JUST_DIR}|g' internal/just/*
        # Fix robodoc compose 
        sed -i 's|${JUST_DIR}/docker/vsi_common/docker-compose.yml|${JUST_DIR}/robodoc.yml|' internal/just/just_robodoc_functions.bsh
        # Refactor new_just
        sed -i 's|vsi_common|just|' internal/just/new_just
        sed -i 's|VSI_DIR|JUST_COMMON_DIR|' internal/just/new_just
        sed -i 's|VSI |Just |' internal/just/new_just
        sed -i 's|/vsi|/just|' internal/just/new_just
        sed -i 's|/just/linux|/just|' internal/just/new_just
        
        sed -i 's|/linux/|/|g' internal/just/*
        sed -i 's|/\.\.|/|g' internal/just/*
      )
      ;;
    *)
      defaultify "${just_arg}" ${@+"${@}"}
      ;;
  esac
}

if [ "${JUST_IN_SCRIPT-0}" = "0" ]; then caseify ${@+"${@}"};fi
