ARG BASH_VERSION=5.0
ARG DOCKER_BUILDX_VERSION=0.9.1

FROM vsiri/recipe:gosu AS gosu
FROM vsiri/recipe:tini-musl AS tini
FROM vsiri/recipe:jq AS jq
# FROM vsiri/recipe:vsi AS vsi
FROM vsiri/recipe:docker AS docker
FROM vsiri/recipe:docker-compose AS docker-compose
FROM docker/buildx-bin:${DOCKER_BUILDX_VERSION} AS buildx

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
      # For git_mirror
      git-lfs \
      # GNU tar that supports --concatenate
      tar \
      # unit test interactive shells
      screen \
      # Make typeing in the docker easier (for debugging)
      readline; \
    command -v xxd &> /dev/null || apk add --no-cache vim

# Disable this check; it gets in the way of running tests locally on git 2.31.2 and newer
RUN git config --system --add safe.directory '*'; \
    # Fix for https://bugs.launchpad.net/ubuntu/+source/git/+bug/1993586
    git config --system protocol.file.allow always

ENV JUSTFILE=/vsi/docker/tests/bash_test.Justfile \
    JUST_SETTINGS=/vsi/vsi_common.env
COPY --from=tini /usr/local /usr/local
COPY --from=gosu /usr/local /usr/local
COPY --from=jq /usr/local /usr/local
COPY --from=docker /usr/local /usr/local
COPY --from=docker-compose /usr/local /usr/local
COPY --from=buildx /buildx /usr/local/libexec/docker/cli-plugins/docker-buildx
# COPY --from=vsi /vsi /vsi

ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env", "bash", "/vsi/linux/just_files/just_entrypoint.sh"]
CMD ["test"]
