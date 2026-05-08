from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from doc_forge.app.settings import AnswerSynthesizerBackend, EmbeddingModelRegime, Settings


def test_settings_defaults_to_transformer_embedding_model() -> None:
    settings = Settings(_env_file=None)

    assert settings.embedding_model is EmbeddingModelRegime.TRANSFORMER


def test_settings_defaults_to_ollama_answer_synthesizer() -> None:
    settings = Settings(_env_file=None)

    assert settings.answer_synthesizer_backend is AnswerSynthesizerBackend.OLLAMA


def test_settings_supports_deterministic_embedding_model() -> None:
    settings = Settings(embedding_model="deterministic", _env_file=None)

    assert settings.embedding_model is EmbeddingModelRegime.DETERMINISTIC


def test_settings_supports_deterministic_answer_synthesizer() -> None:
    settings = Settings(answer_synthesizer_backend="deterministic", _env_file=None)

    assert settings.answer_synthesizer_backend is AnswerSynthesizerBackend.DETERMINISTIC


def test_settings_rejects_unknown_embedding_model() -> None:
    with pytest.raises(ValidationError, match="embedding_model"):
        Settings(embedding_model="unknown", _env_file=None)


def test_settings_rejects_unknown_answer_synthesizer_backend() -> None:
    with pytest.raises(ValidationError, match="answer_synthesizer_backend"):
        Settings(answer_synthesizer_backend="unknown", _env_file=None)


def test_settings_rejects_invalid_answering_and_synthesis_values() -> None:
    with pytest.raises(ValidationError, match="answering_top_k"):
        Settings(answering_top_k=0, _env_file=None)
    with pytest.raises(ValidationError, match="answering_min_score"):
        Settings(answering_min_score=1.1, _env_file=None)
    with pytest.raises(ValidationError, match="answer_synthesis_timeout_seconds"):
        Settings(answer_synthesis_timeout_seconds=0.0, _env_file=None)


def test_settings_models_current_runtime_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment == "dev"
    assert settings.artifact_root == Path("./data")
    assert settings.service_name == "doc_forge-api"
    assert settings.json_log_path is None
    assert settings.embedding_model is EmbeddingModelRegime.TRANSFORMER
    assert settings.answer_synthesizer_backend is AnswerSynthesizerBackend.OLLAMA
    assert settings.answer_synthesizer_model == "qwen3.5:9b"
    assert settings.ollama_base_url == "http://127.0.0.1:11434"
    assert settings.answering_top_k == 3
    assert settings.answering_min_score == 0.3
    assert settings.answer_synthesis_timeout_seconds == 90.0
    assert settings.hf_home == Path("data/huggingface")
    assert settings.torchinductor_cache_dir == Path("data/torchinductor-cache")
    assert settings.hf_hub_offline is False
    assert settings.transformers_offline is False


def test_settings_accepts_namespaced_runtime_fields(tmp_path: Path) -> None:
    settings = Settings(
        artifact_root=tmp_path / "artifacts",
        json_log_path=tmp_path / "logs" / "api.jsonl",
        answer_synthesizer_model="test-model",
        ollama_base_url="http://ollama.local:11434",
        answering_top_k=5,
        answering_min_score=0.4,
        answer_synthesis_timeout_seconds=12.5,
        hf_home=tmp_path / "huggingface",
        torchinductor_cache_dir=tmp_path / "torch",
        hf_hub_offline=True,
        transformers_offline=True,
        _env_file=None,
    )

    assert settings.artifact_root == tmp_path / "artifacts"
    assert settings.json_log_path == tmp_path / "logs" / "api.jsonl"
    assert settings.answer_synthesizer_model == "test-model"
    assert settings.ollama_base_url == "http://ollama.local:11434"
    assert settings.answering_top_k == 5
    assert settings.answering_min_score == 0.4
    assert settings.answer_synthesis_timeout_seconds == 12.5
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
        "embedding_model": "transformer",
        "answer_synthesizer_backend": "ollama",
        "answer_synthesizer_model": "qwen3.5:9b",
        "ollama_base_url": "http://127.0.0.1:11434",
        "answering_top_k": 3,
        "answering_min_score": 0.3,
        "answer_synthesis_timeout_seconds": 90.0,
        "hf_home_configured": True,
        "torchinductor_cache_dir_configured": True,
        "hf_hub_offline": False,
        "transformers_offline": False,
    }
