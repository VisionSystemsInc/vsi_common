FROM vsiri/recipe:pipenv AS pipenv

FROM python:2 AS dep_stage
SHELL ["/usr/bin/env", "bash", "-euxvc"]

COPY --from=pipenv /usr/local /usr/local
RUN shopt -s nullglob; for patch in /usr/local/share/just/container_build_patch/*; do "${patch}"; done

ENV WORKON_HOME=/venv \
    PIPENV_PIPFILE=/vsi/docker/tests/Pipfile2 \
    PIPENV_CACHE_DIR=/venv/cache \
    PYENV_SHELL=/bin/bash \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

###############################################################################

FROM dep_stage AS pipenv_cache

ADD Pipfile2 Pipfile2.lock /vsi/docker/tests/

RUN mkdir /opt/wx; \
    echo "from setuptools import setup, find_packages; setup(name='wxpython', version='4.0.3')" > /opt/wx/setup.py; \
    pipenv install --keep-outdated /opt/wx; \
    cp /vsi/docker/tests/Pipfile2.lock /venv; \
    rm -rf /vsi/* /tmp/pip*

###############################################################################

FROM dep_stage

COPY --from=pipenv_cache /venv /venv