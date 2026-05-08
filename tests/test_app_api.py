from __future__ import annotations

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from doc_forge import __version__
from doc_forge.answer_synthesis import AnswerSynthesisError
from doc_forge.app import dependencies
from doc_forge.app.api import create_app, readyz
from doc_forge.app.settings import Settings
from doc_forge.embedding.vectors import EmbeddingBatch, EmbeddingVector


def test_package_imports() -> None:
    assert __version__ == "0.1.0"


def test_readyz_payload() -> None:
    assert readyz() == {"status": "ok"}


def test_root_redirects_to_web_ui(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "DocForge" in response.text


def test_web_ui_is_served(client: TestClient) -> None:
    response = client.get("/ui")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DocForge" in response.text
    assert "Manage corpus" in response.text
    assert "Ask corpus" in response.text
    assert "Question composer" in response.text
    assert "Retrieve candidates" in response.text
    assert "Generate answer" in response.text
    assert "Final result" in response.text
    assert 'type="module"' in response.text
    assert "/ui/static/main.js" in response.text


def test_web_ui_static_asset_is_served(client: TestClient) -> None:
    response = client.get("/ui/static/main.js")

    assert response.status_code == 200
    assert "createControllers" in response.text


def test_create_app_defers_runtime_validation_until_lifespan(tmp_path: Path) -> None:
    occupied_cache_path = tmp_path / "occupied-cache-path"
    occupied_cache_path.write_text("not a directory", encoding="utf-8")
    app = create_app(
        Settings(
            embedding_model="transformer",
            hf_home=occupied_cache_path,
            _env_file=None,
        )
    )

    with pytest.raises(RuntimeError, match="Set DOC_FORGE_HF_HOME to a writable directory"):
        with TestClient(app):
            pass


def test_lifespan_created_service_handles_documents() -> None:
    app = create_app(Settings(embedding_model="deterministic", _env_file=None))

    with TestClient(app) as client:
        upload_response = client.post(
            "/corpora/lifespan/documents",
            files={"file": ("notes.md", b"# Runtime\n\nConfigured.", "text/markdown")},
        )
        document_id = upload_response.json()["document_id"]

        response = client.get(f"/corpora/lifespan/documents/{document_id}")

    assert upload_response.status_code == 201
    assert response.status_code == 200
    assert response.json()["document_id"] == document_id


def test_default_embedding_model_uses_transformer_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_transformer_models = 0

    class FakeTransformerEmbeddingModel:
        def __init__(self) -> None:
            nonlocal created_transformer_models
            created_transformer_models += 1

        def embed_text(self, text: str) -> EmbeddingVector:
            _ = text
            return EmbeddingVector([0.0])

        def embed_texts(self, texts: list[str]) -> EmbeddingBatch:
            return EmbeddingBatch(EmbeddingVector([0.0]) for _text in texts)

    monkeypatch.setattr(
        dependencies,
        "SentenceTransformerEmbeddingModel",
        FakeTransformerEmbeddingModel,
    )

    model = dependencies._create_embedding_model(Settings(_env_file=None))

    assert isinstance(model, FakeTransformerEmbeddingModel)
    assert created_transformer_models == 1


def test_default_answer_synthesizer_uses_ollama_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_ollama_synthesizers = 0

    class FakeOllamaAnswerSynthesizer:
        def __init__(self, *, base_url: str, model: str, timeout_seconds: float) -> None:
            nonlocal created_ollama_synthesizers
            created_ollama_synthesizers += 1
            self.base_url = base_url
            self.model = model
            self.timeout_seconds = timeout_seconds

    monkeypatch.setattr(
        dependencies,
        "OllamaAnswerSynthesizer",
        FakeOllamaAnswerSynthesizer,
    )

    synthesizer = dependencies._create_answer_synthesizer(Settings(_env_file=None))

    assert isinstance(synthesizer, FakeOllamaAnswerSynthesizer)
    assert synthesizer.base_url == "http://127.0.0.1:11434"
    assert synthesizer.model == "qwen3.5:9b"
    assert synthesizer.timeout_seconds == 90.0
    assert created_ollama_synthesizers == 1


def test_explicit_deterministic_answer_synthesizer_is_supported() -> None:
    synthesizer = dependencies._create_answer_synthesizer(
        Settings(answer_synthesizer_backend="deterministic", _env_file=None)
    )

    assert synthesizer.__class__.__name__ == "DeterministicAnswerSynthesizer"


def test_answer_synthesis_failure_returns_503_at_request_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeOllamaAnswerSynthesizer:
        def __init__(self, *, base_url: str, model: str, timeout_seconds: float) -> None:
            _ = base_url, model, timeout_seconds

        def synthesize_answer(self, request) -> str:  # type: ignore[no-untyped-def]
            _ = request
            raise AnswerSynthesisError("ollama answer synthesis is unavailable")

    monkeypatch.setattr(
        dependencies,
        "OllamaAnswerSynthesizer",
        FakeOllamaAnswerSynthesizer,
    )
    app = create_app(
        Settings(
            embedding_model="deterministic",
            answer_synthesizer_backend="ollama",
            _env_file=None,
        )
    )

    with TestClient(app) as client:
        upload_response = client.post(
            "/corpora/lifespan/documents",
            files={"file": ("notes.md", b"# Runtime\n\nConfigured.", "text/markdown")},
        )
        assert upload_response.status_code == 201

        response = client.post(
            "/corpora/lifespan/answers/query",
            json={"question": "Configured."},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "Configured answer synthesizer is unavailable."}


def test_answer_synthesis_failure_is_logged(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FakeOllamaAnswerSynthesizer:
        def __init__(self, *, base_url: str, model: str, timeout_seconds: float) -> None:
            _ = base_url, model, timeout_seconds

        def synthesize_answer(self, request) -> str:  # type: ignore[no-untyped-def]
            _ = request
            raise AnswerSynthesisError("ollama answer synthesis is unavailable")

    monkeypatch.setattr(
        dependencies,
        "OllamaAnswerSynthesizer",
        FakeOllamaAnswerSynthesizer,
    )
    app = create_app(
        Settings(
            embedding_model="deterministic",
            answer_synthesizer_backend="ollama",
            _env_file=None,
        )
    )

    with caplog.at_level(logging.WARNING):
        with TestClient(app) as client:
            upload_response = client.post(
                "/corpora/lifespan/documents",
                files={"file": ("notes.md", b"# Runtime\n\nConfigured.", "text/markdown")},
            )
            assert upload_response.status_code == 201

            response = client.post(
                "/corpora/lifespan/answers/query",
                json={"question": "Configured."},
            )

    assert response.status_code == 503
    assert "Answer request failed: corpus_id=lifespan question='Configured.'" in caplog.text
    assert "ollama answer synthesis is unavailable" in caplog.text
