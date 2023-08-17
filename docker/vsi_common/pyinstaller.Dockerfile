FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:tini as tini
FROM vsiri/recipe:pipenv as pipenv
FROM vsiri/recipe:vsi as vsi

FROM centos:6

SHELL ["/usr/bin/env", "bash", "-euxvc"]

ARG PYTHON_VERSION=3.7.7
    # Curl already installed, updating
RUN yum install -y curl ca-certificates; \
    curl -L -o /conda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh; \
    chmod 755 /conda.sh; \
    bash /conda.sh -b -p /tmp/conda -s; \
    /tmp/conda/bin/conda create -y -p "/usr/local" "python=${PYTHON_VERSION}"; \
    rm -rf /tmp/conda /conda.sh

ENV WORKON_HOME=/venv \
    PIPENV_PIPFILE=/vsi/docker/vsi_common/pyinstaller.Pipfile \
    PIPENV_CACHE_DIR=/venv/cache \
    PYENV_SHELL=/bin/bash \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    JUSTFILE=/vsi/docker/vsi_common/pyinstaller.Justfile

COPY --from=pipenv /usr/local /usr/local
RUN shopt -s nullglob; for patch in /usr/local/share/just/container_build_patch/*; do "${patch}"; done

ARG PYINSTALLER_VERSION=3.6
RUN pip3 install pyinstaller=="${PYINSTALLER_VERSION}"

COPY --from=tini /usr/local /usr/local
COPY --from=gosu /usr/local /usr/local
# Allow non-privileged to run gosu (remove this to take root away from user)
RUN chmod u+s /usr/local/bin/gosu

COPY --from=vsi /vsi /vsi

ENTRYPOINT ["/usr/local/bin/tini", "--", "/usr/bin/env", "bash", "/vsi/linux/just_files/just_entrypoint.sh"]

CMD ["pyinstaller"]