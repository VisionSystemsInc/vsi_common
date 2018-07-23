FROM vsiri/recipe:gosu as gosu
FROM vsiri/recipe:tini as tini

FROM python:2.7

RUN pip install pipenv

ENV WORKON_HOME=/venv \
    PIPENV_PIPFILE=/vsi/docs/Pipfile \
    PYENV_SHELL=/bin/bash \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8
ADD Pipfile Pipfile.lock /vsi/docs/
RUN if [ ! -s Pipfile.lock ]; then \
      pipenv lock; \
    fi; \
    pipenv install; \
    rm -r /src

ADD docs_entrypoint.bsh /
ENTRYPOINT ["/usr/local/bin/tini", "/usr/bin/env", "bash", "/docs_entrypoint.bsh"]

CMD ["docs"]