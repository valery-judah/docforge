from __future__ import annotations

import pytest
from pydantic import ValidationError

from doc_forge.app.settings import EmbeddingModelRegime, Settings


def test_settings_defaults_to_deterministic_embedding_model() -> None:
    settings = Settings()

    assert settings.embedding_model is EmbeddingModelRegime.DETERMINISTIC


def test_settings_supports_transformer_embedding_model() -> None:
    settings = Settings(embedding_model="transformer")

    assert settings.embedding_model is EmbeddingModelRegime.TRANSFORMER


def test_settings_rejects_unknown_embedding_model() -> None:
    with pytest.raises(ValidationError, match="embedding_model"):
        Settings(embedding_model="unknown")
