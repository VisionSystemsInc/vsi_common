FROM vsiri/recipe:pipenv as pipenv

FROM python:3 as dep_stage
SHELL ["/usr/bin/env", "bash", "-euxvc"]

# For wxPython, which I don't actually need
# RUN apt-get update; \
#     DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
#       libgtk-3-0 libglu1-mesa freeglut3 gstreamer1.0-plugins-base \
#       libwebkitgtk-3.0-0 libjpeg62-turbo-dev libtiff5 libpng12-0 libsdl2-2.0-0\
#       libnotify4 libsm6 libgstreamer1.0-0; \
#     rm -r /var/lib/apt/lists/*

COPY --from=pipenv /tmp/pipenv /tmp/pipenv
RUN /tmp/pipenv/get-pipenv; rm -rf /tmp/pipenv || :

ENV WORKON_HOME=/venv \
    PIPENV_PIPFILE=/vsi/docker/tests/Pipfile3 \
    PIPENV_CACHE_DIR=/venv/cache \
    PYENV_SHELL=/bin/bash \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

###############################################################################

FROM dep_stage as pipenv_cache

# For wxPython, which I don't actually need
# RUN apt-get update; \
#     DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
#       libgtk-3-dev mesa-common-dev libglu1-mesa-dev freeglut3-dev \
#       libwebkitgtk-3.0-dev libjpeg62-turbo-dev libtiff5-dev libpng12-dev \
#       libsdl2-dev libnotify-dev libsm-dev libgstreamer1.0-dev \
#       libgstreamer-plugins-base1.0-dev; \
#     rm -r /var/lib/apt/lists/*

ADD Pipfile3 Pipfile3.lock /vsi/docker/tests/

RUN mkdir /opt/wx; \
    echo "from setuptools import setup, find_packages; setup(name='wxpython', version='4.0.3')" > /opt/wx/setup.py; \
    pipenv install --keep-outdated /opt/wx; \
    cp /vsi/docker/tests/Pipfile3.lock /venv; \
    rm -rf /vsi/* /tmp/pip*

###############################################################################

FROM dep_stage

COPY --from=pipenv_cache /venv /venv