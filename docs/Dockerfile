FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:tini as tini

FROM python:3.7.0

SHELL ["/usr/bin/env", "bash", "-euxvc"]

RUN pip install pipenv

ENV WORKON_HOME=/venv \
    PIPENV_PIPFILE=/vsi/docs/Pipfile \
    PYENV_SHELL=/bin/bash \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8
ADD Pipfile Pipfile.lock /vsi/docs/

RUN packages=(wxpython pyopencl boxm2_adaptor boxm2_scene_adaptor brl_init vtk); \
    versions=(4.0.3 2018.2 1.0 1.0 1.0 1.0); \
    for x in "${!packages[@]}"; do \
        mkdir -p "/opt/${packages[$x]}/${packages[$x]}"; \
        touch "/opt/${packages[$x]}/${packages[$x]}/__init__.py"; \
        echo "from setuptools import setup, find_packages; setup(name='${packages[$x]}', packages=['${packages[$x]}'], version='${versions[$x]}')" > "/opt/${packages[$x]}/setup.py"; \
    done; \
    pipenv install --keep-outdated /opt/*; \
    cp "${PIPENV_PIPFILE}.lock" /venv; \
    rm -rf /vsi/* /tmp/pip*

# Hack for vsi_domain
RUN ln -s /vsi/docs/vsi_domains.py /venv/docs-*/lib/python3.7/site-packages/

COPY --from=tini /usr/local/bin/tini /usr/local/bin/tini
COPY --from=gosu /usr/local/bin/gosu /usr/local/bin/gosu
# Allow non-privileged to run gosu (remove this to take root away from user)
RUN chmod u+s /usr/local/bin/gosu

ADD docs_entrypoint.bsh /
ENTRYPOINT ["/usr/local/bin/tini", "/usr/bin/env", "bash", "/docs_entrypoint.bsh"]

CMD ["docs"]