FROM python:3.11-alpine as source

FROM source as build

WORKDIR /
COPY requirements.txt .
# hadolint ignore=SC1091
RUN python -m pip install 'uv >= 0.1.21' --no-cache-dir && \
    uv venv .venv && \
    . .venv/bin/activate && \
    uv pip sync requirements.txt

FROM source as run
# hadolint ignore=DL3018
RUN apk add --no-cache supercronic shadow
COPY --from=build /.venv /.venv/
COPY . /app

# Run the command on container startup
CMD ["supercronic", "/app/crontab"]
