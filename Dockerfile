FROM python:3.12-slim AS source

FROM source AS build
WORKDIR /
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY uv.lock pyproject.toml /
RUN --mount=type=cache,target=/root/.cache \
    uv sync --no-dev --locked --no-install-project \
    && uv pip install --no-cache-dir 'setuptools >= 69.1.1'

FROM source AS deploy
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
COPY entrypoint.sh /entrypoint.sh
ADD --chmod=755 https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/local/bin/aws-lambda-rie

COPY --from=build /.venv /.venv/
COPY . /app
ENV PATH="/.venv/bin:$PATH"

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "main.handler" ]
