from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from doc_forge.app.settings import EmbeddingModelRegime, Settings

_REQUIRED_TRANSFORMER_CACHE_ENV = ("HF_HOME", "TORCHINDUCTOR_CACHE_DIR")


def validate_runtime(
    settings: Settings,
    environ: Mapping[str, str] | None = None,
) -> None:
    if settings.embedding_model is not EmbeddingModelRegime.TRANSFORMER:
        return

    if environ is None:
        environ = os.environ

    for env_name in _REQUIRED_TRANSFORMER_CACHE_ENV:
        path = environ.get(env_name)
        if not path:
            raise RuntimeError(
                f"{env_name} must be set to a writable directory for transformer embeddings."
            )
        _ensure_runtime_directory(env_name, path)


def _ensure_runtime_directory(env_name: str, path: str) -> None:
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Could not create {env_name} directory at {path!r}. "
            f"Set {env_name} to a writable directory."
        ) from exc
