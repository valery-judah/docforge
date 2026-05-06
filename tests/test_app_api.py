from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from doc_forge import __version__
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


def test_web_ui_static_asset_is_served(client: TestClient) -> None:
    response = client.get("/ui/static/app.js")

    assert response.status_code == 200
    assert "loadDocuments" in response.text


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
