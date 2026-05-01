from __future__ import annotations

import os
from collections.abc import MutableMapping
from pathlib import Path

from doc_forge.app.settings import EmbeddingModelRegime, Settings

_TRANSFORMER_CACHE_ENV_BY_SETTING = {
    "hf_home": "HF_HOME",
    "torchinductor_cache_dir": "TORCHINDUCTOR_CACHE_DIR",
}
_TRANSFORMER_BOOL_ENV_BY_SETTING = {
    "hf_hub_offline": "HF_HUB_OFFLINE",
    "transformers_offline": "TRANSFORMERS_OFFLINE",
}


def validate_runtime(
    settings: Settings,
    environ: MutableMapping[str, str] | None = None,
) -> None:
    if settings.embedding_model is not EmbeddingModelRegime.TRANSFORMER:
        return

    if environ is None:
        environ = os.environ

    for setting_name, env_name in _TRANSFORMER_CACHE_ENV_BY_SETTING.items():
        path = getattr(settings, setting_name)
        config_env_name = f"DOC_FORGE_{env_name}"
        if not path:
            raise RuntimeError(
                f"{config_env_name} must be set to a writable directory for transformer embeddings."
            )
        _ensure_runtime_directory(config_env_name, path)
        environ[env_name] = str(path)

    for setting_name, env_name in _TRANSFORMER_BOOL_ENV_BY_SETTING.items():
        value = getattr(settings, setting_name)
        environ[env_name] = "1" if value else "0"


def _ensure_runtime_directory(config_env_name: str, path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Could not create {config_env_name} directory at {str(path)!r}. "
            f"Set {config_env_name} to a writable directory."
        ) from exc
