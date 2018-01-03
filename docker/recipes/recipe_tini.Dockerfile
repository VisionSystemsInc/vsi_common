FROM alpine:latest

SHELL ["sh", "-euxvc"]

ONBUILD ARG TINI_VERSION=v0.16.1
ONBUILD RUN apk add --no-cache --virtual .tini-deps gnupg curl ca-certificates; \
            # download tini
            curl -Lo /usr/local/bin/tini https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini; \
            chmod +x /usr/local/bin/tini; \
            # verify the signature
            curl -Lo /dev/shm/tini.asc https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini.asc; \
            export GNUPGHOME=/dev/shm; \
            for server in $(shuf -e ha.pool.sks-keyservers.net \
                                    hkp://p80.pool.sks-keyservers.net:80 \
                                    keyserver.ubuntu.com \
                                    hkp://keyserver.ubuntu.com:80 \
                                    pgp.mit.edu) ; do \
                gpg --keyserver "$server" --recv-keys 595E85A6B1B4779EA4DAAEC70B588DFF0527A9B7 && break || : ; \
            done; \
            gpg --batch --verify /dev/shm/tini.asc /usr/local/bin/tini; \
            # cleanup to keep intermediate image samell
            apk del .tini-deps