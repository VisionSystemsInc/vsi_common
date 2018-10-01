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

RUN packages=(wxpython pyopencl boxm2_adaptor boxm2_scene_adaptor brl_init vtk vpgl_adaptor_boxm2_batch); \
    versions=(4.0.3 2018.2 1.0 1.0 1.0 1.0 1.0); \
    for x in "${!packages[@]}"; do \
        mkdir -p "/opt/fake_package_${packages[$x]}/${packages[$x]}"; \
        touch "/opt/fake_package_${packages[$x]}/${packages[$x]}/__init__.py"; \
        echo "from setuptools import setup, find_packages; setup(name='${packages[$x]}', packages=['${packages[$x]}'], version='${versions[$x]}')" > "/opt/fake_package_${packages[$x]}/setup.py"; \
    done; \
    echo "boxm2_scene_adaptor=1" >> /opt/fake_package_boxm2_scene_adaptor/boxm2_scene_adaptor/__init__.py; \
    echo "create_scene_and_blocks=1; ocl_info=2" >> /opt/fake_package_boxm2_adaptor/boxm2_adaptor/__init__.py; \
    pipenv install --keep-outdated /opt/fake_package_*; \
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