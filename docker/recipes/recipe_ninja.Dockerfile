FROM alpine:latest

SHELL ["sh", "-euxvc"]

ONBUILD ARG NINJA_VERSION=v1.8.2
#No signature :(
ONBUILD RUN apk add --no-cache --virtual .ninja-deps unzip curl ca-certificates; \
            cd /usr/local/bin; \
            curl -sLo ninja-linux.zip https://github.com/ninja-build/ninja/releases/download/${NINJA_VERSION}/ninja-linux.zip; \
            unzip ninja-linux.zip; \
            chmod +x /usr/local/bin/ninja; \
            rm ninja-linux.zip; \
            apk del .ninja-deps
