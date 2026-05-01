from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingModelRegime(StrEnum):
    DETERMINISTIC = "deterministic"
    TRANSFORMER = "transformer"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DOC_FORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    embedding_model: EmbeddingModelRegime = EmbeddingModelRegime.DETERMINISTIC


@lru_cache
def get_settings() -> Settings:
    return Settings()
