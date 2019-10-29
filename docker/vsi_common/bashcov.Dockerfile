FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:tini as tini
FROM vsiri/recipe:vsi as vsi

FROM ruby:2.6.5-buster

SHELL ["/usr/bin/env", "bash", "-euxvc"]

ARG BASHCOV_VERSION=1.8.2
RUN gem install bashcov --version "${BASHCOV_VERSION}"

ENV JUST_SETTINGS
ADD bashcov.Justfile /vsi/docker/vsi_common/
COPY --from=tini /usr/local/bin/tini /usr/local/bin/tini
COPY --from=gosu /usr/local/bin/gosu /usr/local/bin/gosu
COPY --from=vsi /vsi /vsi
ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env", "bash", "/vsi/linux/just_entrypoint.sh"]
CMD ["docs"]