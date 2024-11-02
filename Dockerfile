FROM python:3.12-alpine AS source

FROM source AS build

WORKDIR /
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY uv.lock pyproject.toml /
RUN --mount=type=cache,target=/root/.cache \
    uv sync --no-dev --locked --no-install-project \
    && uv pip install --no-cache-dir 'setuptools >= 69.1.1'

FROM source AS run
# hadolint ignore=DL3018
RUN apk add --no-cache supercronic shadow
COPY --from=build /.venv /.venv/
COPY . /app

# Run the command on container startup
CMD ["supercronic", "/app/crontab"]
