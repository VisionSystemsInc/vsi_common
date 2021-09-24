ARG OS
ARG DOCKER_COMPOSE_VERSION=1.26.2

FROM docker/compose:alpine-${DOCKER_COMPOSE_VERSION} as docker-compose_musl
FROM docker/compose:debian-${DOCKER_COMPOSE_VERSION} as docker-compose_glib
FROM vsiri/recipe:docker as docker
FROM vsiri/recipe:docker-compose as docker-compose
FROM vsiri/recipe:git-lfs as git-lfs
FROM vsiri/recipe:jq as jq
FROM vsiri/recipe:conda-python as conda-python

# FROM busybox:latest as wget

FROM ${OS}

# COPY --from=wget /bin/wget /musl/wget

RUN set -euxv; \
    if command -v yum; then \
      # Redhat 6's git is too old, bring in outside help
      if [ -f /etc/redhat-release ] && [[ $(cat /etc/redhat-release) =~ .*release\ 6.* ]]; then \
        yum install -y http://opensource.wandisco.com/centos/6/git/x86_64/wandisco-git-release-6-1.noarch.rpm; \
      fi; \
      other_packages=''; \
      if [ -f /etc/os-release ] && [ "$(source /etc/os-release; echo "${ID}")" = "fedora" ]; then \
        # docker-compose won't work without libcrypt.so.1
        other_packages='libxcrypt-compat'; \
      fi; \
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
          # git_mirror tests/lfs.zip
          tar unzip \
          git ca-certificates \
          ${other_packages} ; \
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
             git ca-certificates \
             # lfs.zip and download_to_stdout
             unzip curl; \
    elif command -v zypper; then \
      other='git curl'; \
      if [ -f /etc/os-release ] && [[ $(source /etc/os-release; echo "${ID} ${VERSION}") = sles\ 11.* ]]; then \
        zypper --gpg-auto-import-keys --non-interactive install -y \
               http://opensource.wandisco.com/suse/11/git/x86_64/wandisco-git-suse-release-11-1.noarch.rpm; \
        rpm --import http://opensource.wandisco.com/RPM-GPG-KEY-WANdisco; \
        # This must be done separate from other call becuase the -f flag will
        # break util-linux
        zypper --gpg-auto-import-keys --non-interactive install -y -f git; \
        other=''; \
      fi; \
      zypper --gpg-auto-import-keys --non-interactive install -y \
             # column for unit tests
             util-linux \
             # cmp for unit tests
             diffutils \
             # nm for lwhich
             binutils \
             # xxd for unit tests
             vim \
             ${other} ca-certificates\
             gzip tar unzip; \
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
          # A realpath that works with non-existing files.
          coreutils \
          git ca-certificates \
          curl tar unzip; \
    elif command -v slackpkg; then \
      # Shhhhh! Make wget quiet
      echo "quiet = on" >> /etc/wgetrc; \
      slackpkg update; \
      # Is there a "right" way to do this?
                             # xxd for unit tests
      yes | slackpkg install vim \
                             # nm for lwhich
                             binutils \
                             git perl ca-certificates \
                             # unzip
                             infozip \
                             # needed for update-ca-certificates
                             perl \
                             # libcurl -> git won't work without this
                             cyrus-sasl; \
      # Needed for ssl to work, or else curl, wget, et al would fail
      /usr/sbin/update-ca-certificates --fresh; \
    elif command -v emerge; then \
      emerge --sync --quiet; \
      # xxd Test dependencies
      emerge vim \
             dev-vcs/git ca-certificates; \
    elif command -v pacman; then \
      # Test dependencies
      pacman --noconfirm -S vim binutils diffutils git ca-certificates; \
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
                            gawk sed git ca-certificates; \
      ln -s /opt/bin/gawk /opt/bin/awk; \
    elif [ -f /etc/os-release ]; then \
      source /etc/os-release; \
      if [ "${ID}" = "clear-linux-os" ]; then \
        swupd bundle-add --no-progress \
              # cmp for unit tests
              diffutils \
              # xxd for unit tests
              vim \
              # nm for lwhich
              binutils \
              git \
              # For lfs.zip
              unzip; \
      fi; \
    fi

SHELL ["/usr/bin/env", "bash", "-euxvc"]

COPY --from=conda-python /usr/local /opt/python
COPY --from=docker /usr/local /usr/local
COPY --from=docker-compose /usr/local /usr/local
COPY --from=docker-compose_musl /usr/local/bin/docker-compose /usr/local/bin/docker-compose_musl
COPY --from=docker-compose_glib /usr/local/bin/docker-compose /usr/local/bin/docker-compose_glib
COPY --from=git-lfs /usr/local /usr/local
COPY --from=jq /usr/local /usr/local
RUN shopt -s nullglob; for patch in /usr/local/share/just/container_build_patch/*; do "${patch}"; done

# TODO: I want to (use just install functions? and) "fix" docker-compose using conda,
# in a container_build_patch, instead here, so that would mean conda only gets
# added to the image in that case, right now its there 100% of the time, and only
# used for a few images.
# This is basically only needed for pre glibc 2.14
RUN if ! docker-compose --version; then \
      rm /usr/local/bin/docker-compose; \
      # Handle symlink dirs, grrr
      cd /opt/python; \
      for d in *; do \
        mkdir -p "/usr/local/${d}"; \
        if [ -L "${d}" ]; then \
          cp -r "${d}/"* "/usr/local/${d}/"; \
        else \
          cp -r "${d}" "/usr/local/"; \
        fi; \
      done; \
      # Patch for old linuxes
      # latest cryptography use abi wheels requrire glibc 2.24, so use an older one
      pip install cryptography==3.2; \
      pip install docker-compose; \
      docker-compose --version; \
    fi

# Please leave code snippet for future use
# # A statically linked curl will support tls3 on older OSes
# ADD https://github.com/dtschan/curl-static/releases/download/v7.63.0/curl /opt/curl
#
#     # Docker-compose starting 1.20 is compiled using a glibc that is too new
# RUN if ! docker-compose --version; then \
#       # Finish setting up curl, cause most likely will need it.
#       chmod 755 /opt/curl; \
#       mv /opt/curl `command -v curl`; \
#       if [ ! -f /etc/ssl/cert.pem ]; then \
#         if [ -f /etc/ssl/ca-bundle.pem ]; then \
#           ln -s /etc/ssl/ca-bundle.pem /etc/ssl/cert.pem; \
#         fi; \
#       fi; \
#       # For now, docker-compose 1.19 is good enough, if not, will have to install
#       # python (conda's python?) and then pip install docker compose
#       curl -fsSLRo /usr/local/bin/docker-compose_glib\
#         https://github.com/docker/compose/releases/download/1.19.0/docker-compose-Linux-x86_64; \
#       chmod 755 /usr/local/bin/docker-compose_glib; \
#     fi

ENV JUSTFILE=/vsi/Justfile

ENTRYPOINT ["/usr/bin/env", "bash", "-c", "cd /vsi; source setup.env; \"${@}\"", "bash"]

CMD just test