ARG BASH_VERSION=5.0
ARG DOCKER_COMPOSE_VERSION=1.25.0-rc4
FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:tini-musl as tini
FROM vsiri/recipe:jq as jq
# FROM vsiri/recipe:vsi as vsi
FROM vsiri/recipe:docker as docker
FROM docker/compose:${DOCKER_COMPOSE_VERSION} as docker-compose

FROM bash:${BASH_VERSION}

SHELL ["/usr/bin/env", "bash", "-euxvc"]

RUN apk add --no-cache \
      # Better awk
      gawk \
      # Better sed, that supports \x00 notation
      sed \
      # column
      util-linux \
      # Better xargs command
      findutils \
      # nm
      binutils \
      # for better realpath, and id that supports -z
      coreutils \
      # For tests like time-tools/timeout
      perl \
      # git for git... pretty self explanitory
      git \
      # unit test interactive shells
      screen \
      # For git_mirror
      git-lfs \
      # Make typeing in the docker easier (for debugging)
      readline; \
    command -v xxd &> /dev/null || apk add --no-cache vim

ENV JUSTFILE=/vsi/docker/tests/bash_test.Justfile \
    JUST_SETTINGS=/vsi/vsi_common.env
COPY --from=tini /usr/local /usr/local
COPY --from=gosu /usr/local/bin/gosu /usr/local/bin/gosu
COPY --from=jq /usr/local/bin/jq /usr/local/bin/jq
COPY --from=docker /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker-compose /usr/local/bin/docker-compose /usr/local/bin/docker-compose
# COPY --from=vsi /vsi /vsi

ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env", "bash", "/vsi/linux/just_files/just_entrypoint.sh"]
CMD ["test"]
