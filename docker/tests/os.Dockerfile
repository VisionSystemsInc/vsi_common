ARG OS
FROM ${OS}

RUN set -euxv; \
    if command -v yum &>/dev/null; then \
      # column for unit tests
      yum install -y util-linux; \
    fi; \
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
