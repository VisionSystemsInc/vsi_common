ARG OS
ARG DOCKER_COMPOSE_VERSION=1.26.2

FROM docker/compose:alpine-${DOCKER_COMPOSE_VERSION} as docker-compose_musl
FROM docker/compose:debian-${DOCKER_COMPOSE_VERSION} as docker-compose_glib
FROM vsiri/recipe:docker as docker
FROM vsiri/recipe:docker-compose as docker-compose

# FROM busybox:latest as wget

FROM ${OS}

# COPY --from=wget /bin/wget /musl/wget

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
          findutils \
          git; \
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
             vim \
             git; \
    elif command -v zypper; then \
      zypper --gpg-auto-import-keys --non-interactive install -y \
             # column for unit tests
             util-linux \
             # cmp for unit tests
             diffutils \
             # nm for lwhich
             binutils \
             # xxd for unit tests
             vim \
             git; \
    elif command -v apk; then \
      apk add --no-cache \
          bash \
          # Better awk
          gawk \
          # Better sed, that supports \x00 notation
          sed \
          # column
          util-linux \
          # Better xargs command because ?
          findutils \
          # nm
          binutils \
          git; \
    elif command -v slackpkg; then \
      slackpkg update; \
      # Is there a "right" way to do this?
                             # xxd for unit tests
      yes | slackpkg install vim \
                             # nm for lwhich
                             binutils \
                             git; \
    elif command -v emerge; then \
      emerge --sync; \
      # xxd Test dependencies
      emerge vim \
             git; \
    elif command -v pacman; then \
      # Test dependencies
      pacman -S vim binutils diffutils git; \
    elif command -v busybox; then \
      # if ! command -v wget; then \
      #   export PATH="/musl:${PATH}"; \
      # fi; \
      wget -O - http://bin.entware.net/x64-k3.2/installer/generic.sh | sh; \
      # Make it more linux like
      ln -s /opt/bin /usr/bin; \
      ln -s /bin/env /usr/bin/env || : ; \
                            # Test dependencies
      /opt/bin/opkg install bash column binutils \
                            # just dependencies
                            gawk sed git; \
      ln -s /opt/bin/gawk /opt/bin/awk; \
    elif [ -f /etc/os-release ]; then \
      source /etc/os-release; \
      if [ "${ID}" = "clear-linux-os" ]; then \
        swupd bundle-add \
              # cmp for unit tests
              diffutils \
              # xxd for unit tests
              vim \
              # nm for lwhich
              binutils \
              git; \
      fi; \
    fi

SHELL ["/usr/bin/env", "bash", "-euxvc"]

COPY --from=docker /usr/local /usr/local
COPY --from=docker-compose /usr/local /usr/local
COPY --from=docker-compose_musl /usr/local/bin/docker-compose /usr/local/bin/docker-compose_musl
COPY --from=docker-compose_glib /usr/local/bin/docker-compose /usr/local/bin/docker-compose_glib
RUN shopt -s nullglob; for patch in /usr/local/share/just/container_build_patch/*; do "${patch}"; done

ENV JUSTFILE=/vsi/Justfile

ENTRYPOINT ["/usr/bin/env", "bash", "-c", "cd /vsi; source setup.env; \"${@}\"", "bash"]

CMD just test