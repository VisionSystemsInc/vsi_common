# Docker recipes

A docker recipe is a (usually very small) docker image that is included in a
multi-stage build so that you don't always have to find and repeat that "prefect
set of docker file lines to include software XYZ", such as gosu, tini, etc...
They are based heavily on ONBUILD and meant to be used as their own stage.

## Example

```Dockerfile
FROM vsiri/recipe:tini as tini
FROM vsiri/recipe:gosu as gosu
FROM debian:9 #My real docker image

RUN echo stuff

COPY --from=tini /usr/local/bin/tini /usr/local/bin/tini
COPY --from=gosu /usr/local/bin/gosu /usr/local/bin/gosu
```

## tini

|Name|tini|
|--|--|
|Build Args|TINI_VERSION - Release name downloaded|
|Output files|/usr/local/bin/tini|

Tini is a process reaper, and should be used in docker that spawn new processes

## gosu

|Name|gosu|
|--|--|
|Build Args|GOSU_VERSION - Release name downloaded|
|Output files|/usr/local/bin/gosu|

Sudo written with docker automation in mind (no passwords ever)

## ep - envplate

|Name|ep|
|--|--|
|Build Args|EP_VERSION - Release name downloaded|
|Output files|/usr/local/bin/ep|

Sudo written with docker automation in mind (no passwords ever)

## Amanda debian packages

|Name|Amanda|
|--|--|
|Build Args|AMANDA_VERSION - Branch name to build off of (can be a sha)|
|Output files|/amanda-backup-client_${AMANDA_VERSION}-1Debian82_amd64.deb<BR>/amanda-backup-server_${AMANDA_VERSION}-1Debian82_amd64.deb|

Complies debian packages for the tape backup software Amanda

# J.U.S.T.

To define the "build recipes" target, J.U.S.T. add this to your `Justfile`

    source "${VSI_COMMON_DIR}/linux/just_docker_functions.bsh"

And add `(justify build recipes)` do any fully automatic docker building targets