# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_CACHE_DIR=/tmp/.uv-cache \
    PORT=8000 \
    DOC_FORGE_ARTIFACT_ROOT=/artifacts

WORKDIR /app

ARG DOC_FORGE_UV_SYNC_GROUPS=""

COPY pyproject.toml uv.lock README.md ./
COPY scripts/container-log-wrapper.sh /usr/local/bin/container-log-wrapper.sh

RUN --mount=type=cache,target=/tmp/.uv-cache \
    uv sync --frozen --no-dev --no-install-project ${DOC_FORGE_UV_SYNC_GROUPS}

COPY src ./src

RUN --mount=type=cache,target=/tmp/.uv-cache \
    uv sync --frozen --no-dev ${DOC_FORGE_UV_SYNC_GROUPS}

FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    DOC_FORGE_ARTIFACT_ROOT=/artifacts \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /usr/local/bin/container-log-wrapper.sh /usr/local/bin/container-log-wrapper.sh

RUN chmod +x /usr/local/bin/container-log-wrapper.sh \
    && install -d -m 0777 /artifacts /logs /tmp/torch_cache

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import os, sys, urllib.request; port = os.environ.get('PORT', '8000'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{port}/readyz', timeout=2).status == 200 else 1)"

ENTRYPOINT ["container-log-wrapper.sh"]
CMD ["sh", "-c", "exec python -m uvicorn doc_forge.app.api:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
