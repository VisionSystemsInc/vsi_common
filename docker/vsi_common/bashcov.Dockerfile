FROM vsiri/recipe:gosu AS gosu
FROM vsiri/recipe:tini AS tini
FROM vsiri/recipe:jq AS jq
FROM vsiri/recipe:vsi AS vsi
FROM vsiri/recipe:docker AS docker
FROM docker/compose:alpine-1.25.4 AS docker-compose

FROM ruby:2.6.5-buster

SHELL ["/usr/bin/env", "bash", "-euxvc"]

ARG BASHCOV_VERSION=1.8.2
RUN gem install bashcov --version "${BASHCOV_VERSION}"

RUN apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      xxd bsdmainutils gawk; \
    rm -r /var/lib/apt/lists/*

ENV JUSTFILE=/vsi/docker/vsi_common/bashcov.Justfile
COPY --from=tini /usr/local /usr/local
COPY --from=gosu /usr/local /usr/local
COPY --from=jq /usr/local /usr/local
COPY --from=docker /usr/local /usr/local
COPY --from=docker-compose /usr/local /usr/local
COPY --from=vsi /vsi /vsi

ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env", "bash", "/vsi/linux/just_files/just_entrypoint.sh"]
CMD ["bashcov"]
