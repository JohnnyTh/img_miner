ARG BASE_IMAGE
FROM ${BASE_IMAGE}

USER root

RUN apt-get update -y  \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && apt-get clean  \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install "poetry>=1.7.0"

WORKDIR /workdir

COPY poetry.lock pyproject.toml README.md /workdir/
COPY img_miner /workdir/img_miner

RUN poetry build  \
    && pip install dist/*.whl  \
    && rm -rf dist  \
    && rm -rf img_miner

CMD ["image-miner"]
