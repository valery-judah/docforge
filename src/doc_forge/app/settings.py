from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingModelRegime(StrEnum):
    DETERMINISTIC = "deterministic"
    TRANSFORMER = "transformer"


_DEFAULT_SECRETS_DIR = Path("/run/secrets")
_SETTINGS_SECRETS_DIR = _DEFAULT_SECRETS_DIR if _DEFAULT_SECRETS_DIR.is_dir() else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DOC_FORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        secrets_dir=_SETTINGS_SECRETS_DIR,
    )

    environment: str = "dev"
    artifact_root: Path = Path("./data")
    service_name: str = "doc_forge-api"
    json_log_path: Path | None = None
    embedding_model: EmbeddingModelRegime = EmbeddingModelRegime.TRANSFORMER
    hf_home: Path | None = None
    torchinductor_cache_dir: Path | None = None
    hf_hub_offline: bool = False
    transformers_offline: bool = False

    @model_validator(mode="after")
    def default_transformer_cache_paths(self) -> Self:
        if self.hf_home is None:
            self.hf_home = self.artifact_root / "huggingface"
        if self.torchinductor_cache_dir is None:
            self.torchinductor_cache_dir = self.artifact_root / "torchinductor-cache"
        return self

    def safe_summary(self) -> dict[str, str | bool | None]:
        return {
            "environment": self.environment,
            "artifact_root": str(self.artifact_root),
            "service_name": self.service_name,
            "json_log_path": str(self.json_log_path) if self.json_log_path else None,
            "embedding_model": self.embedding_model.value,
            "hf_home_configured": self.hf_home is not None,
            "torchinductor_cache_dir_configured": self.torchinductor_cache_dir is not None,
            "hf_hub_offline": self.hf_hub_offline,
            "transformers_offline": self.transformers_offline,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
