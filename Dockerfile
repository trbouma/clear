# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm AS builder

ARG POETRY_VERSION=1.8.2

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1

# These packages support native dependency builds on architectures where a
# prebuilt secp256k1 wheel is unavailable.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        autoconf \
        automake \
        build-essential \
        libffi-dev \
        libtool \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
COPY src /app/src
RUN poetry install --only main --no-ansi


FROM python:3.11-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 clear \
    && useradd --uid 10001 --gid clear --create-home --shell /usr/sbin/nologin clear \
    && install -d -o clear -g clear /app/data

WORKDIR /app

COPY --from=builder --chown=clear:clear /app/.venv /app/.venv
COPY --from=builder --chown=clear:clear /app/src /app/src

USER clear

EXPOSE 3339

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3339/health', timeout=3).read()"]

CMD ["clear", "--host", "0.0.0.0", "--port", "3339", "--database", "/app/data/clear.sqlite3"]
