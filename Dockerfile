# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_CACHE_DIR=/tmp/.uv-cache \
    DOC_FORGE_ARTIFACT_ROOT=/artifacts

WORKDIR /app

COPY pyproject.toml uv.lock README.md alembic.ini ./
COPY scripts/container-log-wrapper.sh /usr/local/bin/container-log-wrapper.sh

RUN --mount=type=cache,target=/tmp/.uv-cache \
    uv sync --frozen --no-dev --no-install-project --group llm

COPY src ./src

RUN --mount=type=cache,target=/tmp/.uv-cache \
    uv sync --frozen --no-dev --group llm

ENV PATH="/app/.venv/bin:${PATH}"

RUN groupadd --system --gid 1000 doc-forge \
    && useradd --system --uid 1000 --gid 1000 --create-home --home-dir /home/doc-forge doc-forge \
    && install -d --owner=doc-forge --group=doc-forge /artifacts \
    && chmod +x /usr/local/bin/container-log-wrapper.sh

USER doc-forge

EXPOSE 8000

ENTRYPOINT ["container-log-wrapper.sh"]
CMD ["sh", "-c", "uvicorn doc_forge.app.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
