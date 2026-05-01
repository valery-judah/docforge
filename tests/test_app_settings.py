from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from doc_forge.app.settings import EmbeddingModelRegime, Settings


def test_settings_defaults_to_deterministic_embedding_model() -> None:
    settings = Settings(_env_file=None)

    assert settings.embedding_model is EmbeddingModelRegime.DETERMINISTIC


def test_settings_supports_transformer_embedding_model() -> None:
    settings = Settings(embedding_model="transformer", _env_file=None)

    assert settings.embedding_model is EmbeddingModelRegime.TRANSFORMER


def test_settings_rejects_unknown_embedding_model() -> None:
    with pytest.raises(ValidationError, match="embedding_model"):
        Settings(embedding_model="unknown", _env_file=None)


def test_settings_models_current_runtime_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment == "dev"
    assert settings.artifact_root == Path("./data")
    assert settings.service_name == "doc_forge-api"
    assert settings.json_log_path is None
    assert settings.hf_home == Path("data/huggingface")
    assert settings.torchinductor_cache_dir == Path("data/torchinductor-cache")
    assert settings.hf_hub_offline is False
    assert settings.transformers_offline is False


def test_settings_accepts_namespaced_runtime_fields(tmp_path: Path) -> None:
    settings = Settings(
        artifact_root=tmp_path / "artifacts",
        json_log_path=tmp_path / "logs" / "api.jsonl",
        hf_home=tmp_path / "huggingface",
        torchinductor_cache_dir=tmp_path / "torch",
        hf_hub_offline=True,
        transformers_offline=True,
        _env_file=None,
    )

    assert settings.artifact_root == tmp_path / "artifacts"
    assert settings.json_log_path == tmp_path / "logs" / "api.jsonl"
    assert settings.hf_home == tmp_path / "huggingface"
    assert settings.torchinductor_cache_dir == tmp_path / "torch"
    assert settings.hf_hub_offline is True
    assert settings.transformers_offline is True


def test_settings_derives_transformer_cache_paths_from_artifact_root(tmp_path: Path) -> None:
    settings = Settings(artifact_root=tmp_path / "artifacts", _env_file=None)

    assert settings.hf_home == tmp_path / "artifacts" / "huggingface"
    assert settings.torchinductor_cache_dir == tmp_path / "artifacts" / "torchinductor-cache"


def test_settings_ignores_legacy_transformer_env_aliases(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("DOC_FORGE_HF_HOME", raising=False)
    monkeypatch.delenv("DOC_FORGE_TORCHINDUCTOR_CACHE_DIR", raising=False)
    monkeypatch.delenv("DOC_FORGE_HF_HUB_OFFLINE", raising=False)
    monkeypatch.delenv("DOC_FORGE_TRANSFORMERS_OFFLINE", raising=False)
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hf"))
    monkeypatch.setenv("TORCHINDUCTOR_CACHE_DIR", str(tmp_path / "torch"))
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "true")

    settings = Settings(_env_file=None)

    assert settings.hf_home == Path("data/huggingface")
    assert settings.torchinductor_cache_dir == Path("data/torchinductor-cache")
    assert settings.hf_hub_offline is False
    assert settings.transformers_offline is False


def test_settings_safe_summary_redacts_transformer_cache_paths(tmp_path: Path) -> None:
    settings = Settings(
        hf_home=tmp_path / "hf",
        torchinductor_cache_dir=tmp_path / "torch",
        _env_file=None,
    )

    assert settings.safe_summary() == {
        "environment": "dev",
        "artifact_root": "data",
        "service_name": "doc_forge-api",
        "json_log_path": None,
        "embedding_model": "deterministic",
        "hf_home_configured": True,
        "torchinductor_cache_dir_configured": True,
        "hf_hub_offline": False,
        "transformers_offline": False,
    }
