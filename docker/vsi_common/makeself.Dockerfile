FROM vsiri/recipe:tini-musl as tini
FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:vsi as vsi

FROM alpine:3.8

RUN apk add --no-cache bash tar

SHELL ["/usr/bin/env", "bash", "-euxvc"]

# Need newer than 2.4.2 for certain features like ARCHIVE_DIR
ARG MAKESELF_VERSION=release-2.4.3

RUN apk add --no-cache --virtual .deps wget; \
    mkdir /makeself; \
    cd /makeself; \
    wget https://github.com/megastep/makeself/archive/${MAKESELF_VERSION}/makeself.tar.gz; \
    tar xf makeself.tar.gz --strip-components=1; \
    rm makeself.tar.gz; \

    # Disable arg parsing by makeself executable, and make executable quietly extract
    sed '1,/^while true/s|^while true|while \\${MAKESELF_PARSE-false}|; 1,/^quiet="n"/s|^quiet="n"|quiet="y"|' \
        "/makeself/makeself-header.sh" > "/makeself/makeself-header_just.sh"; \

    # Add sourcing local.env to the header, to cover corner cases like needing to to change TMPDIR
    sed -i '2r /dev/stdin' "/makeself/makeself-header_just.sh" < \
           <(echo 'for check_dir in "\`dirname \$0\`" "\${PWD}"; do'; \
             echo '  if test -f "\${check_dir}/local.env"; then'; \
             echo '    set -a'; \
             echo '    source "\${check_dir}/local.env"'; \
             echo '    set +a'; \
             echo '  fi'; \
             echo 'done'); \
    apk del .deps

ENV JUSTFILE=/vsi/docker/vsi_common/makeself.Justfile

COPY --from=tini /usr/local /usr/local
COPY --from=gosu /usr/local /usr/local
# Allow non-privileged to run gosu (remove this to take root away from user)
RUN chmod u+s /usr/local/bin/gosu
COPY --from=vsi /vsi /vsi

ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env", "bash", "/vsi/linux/just_files/just_entrypoint.sh"]

CMD ["makeself"]
