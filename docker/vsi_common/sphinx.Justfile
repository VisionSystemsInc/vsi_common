#!/usr/bin/env false bash

function caseify()
{
  local cmd="${1}"
  shift 1
  case "${cmd}" in
    docs) # Build docs
      source "${VSI_COMMON_DIR}/linux/elements.bsh"

      cd /docs

      pipenv run python -c "import conf,os; [os.makedirs(x) for x in conf.html_static_path if not os.path.exists(x)]"

      src_files=()
      doc_files=()

      pushd /src > /dev/null # make exclude and autodoc_dirs relative to /src
        echo "Pre parsing autodoc sphinx files..."
        split_s autodoc_dirs ${DOCS_AUTODOC_DIRS-}
        split_s autodoc_output_dirs ${DOCS_AUTODOC_OUTPUT_DIRS-}
        split_s autodoc_exclude_dirs ${DOCS_AUTODOC_EXCLUDE_DIRS-}
        for x in "${!autodoc_output_dirs[@]}"; do
          pipenv run sphinx-apidoc -o "/docs/${autodoc_output_dirs[x]}" "${autodoc_dirs[x]}" ${autodoc_exclude_dirs+"${autodoc_exclude_dirs[@]}"}
        done
      popd > /dev/null

      echo "Pre parsing sphinx files..."
      split_s exclude_dirs ${DOCS_EXCLUDE_DIRS-}
      find_flags=()
      for x in "${exclude_dirs[@]}"; do
        find_flags+=(-path "/src/${x}" -prune -o)
      done

      # For now, all languages we are using can use ## as comments. When this
      # is no longer true, the find will need to be extension specific, or
      # some mechanism will be needed to determine type, say `file`
      while read -r line; do
        # Will not work if path has newlines in it, but in the container, that
        # won't happen
        if [[ ${line} =~ (^.*):$'\t'\ *\#\*\#\ *(.*$) ]]; then
          src_files+=("${BASH_REMATCH[1]}")
          doc_files+=("${BASH_REMATCH[2]}")
        else
          echo "'${line}'"
          echo "Pattern does not match"
          continue
        fi
      done < <(find /src "${find_flags[@]}" -type f -not -name '*.md' -not -name PKG-INFO -print0 | xargs -0 grep -T -H '^ *#\*# *' || :)

      echo "Processing sphinx files..."

      [ "${#src_files[@]}" = "${#doc_files[@]}" ]

      for idx in "${!src_files[@]}"; do
        doc_file="${doc_files[${idx}]}"
        src_file="${src_files[${idx}]}"

        # Remove newline fun, thanks to windows
        doc_file="${doc_file//[$'\r\n']}"
        src_file="${src_file//[$'\r\n']}"

        if [ ${#doc_file} -eq 0 ]; then
          continue
        fi
        if [[ ${doc_file::1} =~ ^[./] ]] || [[ ${doc_file} =~ \.\. ]]; then
          echo "${src_file} skipped. Invalid document name ${doc_file}"
          continue
        fi

        # echo "Processing ${doc_file}"

        doc_file="/docs/${doc_file}"
        doc_dir="$(dirname "${doc_file}")"
        doc_file="$(basename "${doc_file}")"

        doc_ext="${doc_file##*.}"
        if [ "${doc_ext}" == "${doc_file}" ]; then
          doc_ext='rst'
        fi
        doc_file="${doc_file%.*}.auto.${doc_ext}"

        mkdir -p "${doc_dir}"

        sed -nE  ':block_start
                  # If the beginning pattern matched, start reading the block
                  /^ *#\*\*/b read_block
                  # Else do not print, goes to next line
                  b noprint
                  :read_block
                  # read the next line
                  n
                  # If the end of doc comment, move on to noprint
                  /^ *#\*\*/{
                    # Print a blank line. This removes the requirement that
                    # the doc writer has to add blank # lines at the end of
                    # a comment block. Other wise you get a lot of "Explicit
                    # markup ends without a blank line; unexpected unindent."
                    # warnings
                    s/.*//
                    p
                    b noprint
                  }
                  # If a line starting with #
                  /^ *#/{
                    # Remove those extra spaced, #, and an optional space
                    s/^ *#+ ?//
                    # print it
                    p
                  }
                  # continue reading the block
                  b read_block
                  # Move on
                  :noprint
                ' "${src_file}" > "${doc_dir}/${doc_file}"
      done

      if [ -n "${DOCS_PRECOMPILE_SCRIPT:+set}" ]; then
        echo "Running Pre-compile script ${DOCS_PRECOMPILE_SCRIPT}" >&2
        "${DOCS_PRECOMPILE_SCRIPT}"
      fi

      exec pipenv run make SPHINXOPTS="${SPHINXOPTS-}" html
      ;;
    intersphinx) # Show links from one intersphinx mapping
      # https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#showing-all-links-of-an-intersphinx-mapping-file
      cd /docs
      if [ "${#}" -lt "1" ]; then
        URL="$(find /docs -name objects.inv)"
      else
        INPUT="${1}"
        URL=$(pipenv run python -c "if True:
            import conf, posixpath
            url = (conf.intersphinx_mapping['${INPUT}'][1] or
                   posixpath.join(conf.intersphinx_mapping['${INPUT}'][0], 'objects.inv'))
            print(url)
            ")
        echo "Fetch intersphinx mapping from <${URL}>..."
      fi
      exec pipenv run python -m sphinx.ext.intersphinx "${URL}"
      ;;
    intersphinx-list) # List available intersphinx mapping
      cd /docs
      exec pipenv run python -c "import conf,json; print(json.dumps(conf.intersphinx_mapping, indent=2))"
      ;;
    nopipenv) # Run command not in pipenv
      exec "${@}"
      ;;
    *) # Run command in pipenv
      exec pipenv run "${cmd}" "${@}"
      ;;
  esac
}
