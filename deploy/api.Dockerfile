FROM python:3.10 as python-deps

LABEL apex_res.api.version="0.0.1"

ENV POETRY_VERSION=1.3.1 \
    PIP_NO_CACHE_DIR=1

RUN pip install --upgrade pip
RUN pip install "poetry==$POETRY_VERSION"

COPY ./pyproject.toml ./pyproject.toml
COPY ./mixer ./mixer
COPY ./README.md ./README.md

RUN poetry config virtualenvs.in-project true && \
    poetry build

FROM python-deps as runtime

COPY --from=python-deps /.venv ./.venv
COPY --from=python-deps /dist .

RUN ./.venv/bin/pip install *.whl

RUN . .venv/bin/activate

EXPOSE 8000

CMD ["poetry", "run", "hypercorn", "mixer.main:app", "--bind", "0.0.0.0:8080"]
