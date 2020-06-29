ARG OS
FROM ${OS}

RUN set -euxv; \
    if command -v yum; then \
      # column for unit tests
      yum install -y util-linux \
          # xxd for unit tests
          vim \
          # nm for lwhich
          binutils \
          # cmp for unit tests
          diffutils \
          # find and xargs for run tests/dir_tools (and maybe more?)
          findutils; \
    elif command -v apt-get; then \
      apt-get update; \
      DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
             # cmp for unit tests
             diffutils \
             # nm for lwhich
             binutils \
             # column for unit tests
             bsdmainutils \
             # xxd for unit tests
             vim; \
    elif command -v zypper; then \
      zypper --gpg-auto-import-keys --non-interactive install -y \
             # column for unit tests
             util-linux \
             # cmp for unit tests
             diffutils \
             # nm for lwhich
             binutils \
             # xxd for unit tests
             vim; \
    elif [ -f /etc/os-release ]; then \
      source /etc/os-release; \
      if [ "${ID}" = "clear-linux-os" ]; then \
        swupd bundle-add \
              # cmp for unit tests
              diffutils \
              # xxd for unit tests
              vim \
              # nm for lwhich
              binutils; \
      fi; \
    fi

SHELL ["/usr/bin/env", "bash", "-euxvc"]

ENV JUSTFILE=/vsi/Justfile

CMD set +xv; \
    cd /vsi; \
    source setup.env; \
    just test