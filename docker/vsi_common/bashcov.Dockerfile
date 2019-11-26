FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:tini as tini
FROM vsiri/recipe:jq as jq
FROM vsiri/recipe:vsi as vsi
FROM vsiri/recipe:docker as docker
FROM vsiri/recipe:docker-compose as docker-compose

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
COPY --from=gosu /usr/local/bin/gosu /usr/local/bin/gosu
COPY --from=jq /usr/local/bin/jq /usr/local/bin/jq
COPY --from=docker /usr/local/bin /usr/local/bin
COPY --from=docker-compose /usr/local/bin/docker-compose /usr/local/bin/docker-compose
COPY --from=vsi /vsi /vsi

ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env", "bash", "/vsi/linux/just_entrypoint.sh"]
CMD ["bashcov"]
