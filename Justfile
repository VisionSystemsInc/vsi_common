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
    test) # Run unit and integration tests
      "${VSI_COMMON_DIR}/tests/run_tests.bsh" ${@+"${@}"}
      extra_args+=$#
      ;;
    test_darling) # Run unit and integration tests using darline
        (
          cd "${VSI_COMMON_DIR}"
          env -i HOME="${HOME}" darling shell ./tests/run_tests.bsh ${@+"${@}"}
        )
        extra_args+=$#
      ;;
    run_wine) # Start a wine bash window
      docker run -it --rm --cap-add=SYS_PTRACE \
                 -e USER_ID="$(id -u)"
                 -e VSI_COMMON_IS_POWERSHELL=1 \
                 -e WINEDEBUG=fixme-all,err-winediag,err-menubuilder \
                 -v vsi_common_wine_home:/home/.user_wine \
                 -v "${VSI_COMMON_DIR}":/vsi_common:ro \
                 -w /vsi_common \
                 andyneff/wine_msys64:ubuntu_14.04 bash -c "cd /z/vsi_common; bash -l"
      ;;
    run_wine-gui) # Start a wine bash window in gui mode
      docker run --rm --cap-add=SYS_PTRACE -e DISPLAY \
                 -e USER_ID="$(id -u)" \
                 -e VSI_COMMON_IS_POWERSHELL=1 \
                 -e WINEDEBUG=fixme-all,err-winediag,err-menubuilder \
                 -v vsi_common_wine_home:/home/.user_wine \
                 -v /tmp/.X11-unix:/tmp/.X11-unix \
                 -v "${VSI_COMMON_DIR}":/vsi_common:ro \
                 -w /vsi_common \
                 andyneff/wine_msys64:ubuntu_14.04 &
      ;;
    test_wine)
      docker run -it --rm --cap-add=SYS_PTRACE \
                 -e VSI_COMMON_IS_POWERSHELL=1 \
                 -e WINEDEBUG=fixme-all,err-winediag,err-menubuilder \
                 -v "${VSI_COMMON_DIR}":/root/.wine/drive_c/vsi_common \
                 -w /root/.wine/drive_c/vsi_common \
                 andyneff/wine_msys64:ubuntu_14.04 -c \
                 "cd /root/.wine/drive_c/vsi_common
                  . setup.env
                  just test ${*}
                  read -p 'Press any key to close' -r -e -n1"
      extra_args+=$#
      ;;
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
        shopt -s nocaseglob

        just_files=()
        more_files=(env.bsh
                    linux/example_just
                    linux/just linux/new_just
                    linux/just_*functions.bsh
                    linux/.just)
        # more_files+=(linux/real_path)
        while [ -n "${more_files+set}" ]; do
          just_files+=("${more_files[@]}")
          more_files=()
          while IFS= read -r -d '' f; do
            if grep -q "^[^#].*$(basename ${f})" "${just_files[@]}"; then
              if ! isin "${f}" "${just_files[@]}" ${more_files+"${more_files[@]}"}; then
                more_files+=("${f}")
              fi
            fi
          done < <(find linux -type f -not -name '.git*' -print0)
        done

        # And copy all of the just files
        cp "${just_files[@]}" internal/just/

        # Refactor the code to stand alone
        # Remove unused feature in just
        sed -i -e '/PYTHONPATH/d' -e '/MATLABPATH/d' internal/just/env.bsh
        # Rebrand VSI_COMMON_DIR
        sed -i 's|VSI_COMMON_DIR|JUST_DIR|g' internal/just/* internal/just/.just
        # Flatten dir structure
        sed -i 's|${JUST_DIR}/linux|${JUST_DIR}|g' internal/just/* internal/just/.just
        # Refactor new_just
        sed -i 's|vsi_common|just|' internal/just/new_just
        sed -i 's|VSI_DIR|JUST_COMMON_DIR|' internal/just/new_just
        sed -i 's|VSI |Just |' internal/just/new_just
        sed -i 's|/vsi|/just|' internal/just/new_just
        sed -i 's|/just/linux|/just|' internal/just/new_just
        sed -i 's|/linux/|/|g' internal/just/*  internal/just/.just
        sed -i 's|/\.\.|/|g' internal/just/*  internal/just/.just
        grep -Zl '^#!/usr/bin/env' internal/just/* | xargs -0 chmod 755
        grep -ZL '^#!/usr/bin/env' internal/just/* | xargs -0 chmod 644

        # Special patch for just_robodoc_functions.bsh
        cp docker/vsi_common/docker-compose.yml internal/just/robodoc.yml
        sed -i 's|${JUST_DIR}/docker/vsi_common/docker-compose.yml|${JUST_DIR}/robodoc.yml|' internal/just/just_robodoc_functions.bsh
      )
      ;;
    *)
      defaultify "${just_arg}" ${@+"${@}"}
      ;;
  esac
}

if [ "${JUST_IN_SCRIPT-0}" = "0" ]; then caseify ${@+"${@}"};fi
