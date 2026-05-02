from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from doc_forge import __version__
from doc_forge.app import dependencies
from doc_forge.app.api import create_app, readyz
from doc_forge.app.dependencies import get_document_service
from doc_forge.app.settings import Settings
from doc_forge.embedding.deterministic import DeterministicEmbeddingModel
from doc_forge.persistence.in_memory_documents import InMemoryDocumentStore
from doc_forge.persistence.in_memory_embeddings import InMemoryEmbeddingStore
from doc_forge.persistence.in_memory_ingestion import InMemoryDocumentIngestionRepository
from doc_forge.services import DocumentService


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(Settings(embedding_model="deterministic", _env_file=None))
    documents = InMemoryDocumentStore()
    embeddings = InMemoryEmbeddingStore()
    ingestion = InMemoryDocumentIngestionRepository(
        documents=documents,
        embeddings=embeddings,
    )
    service = DocumentService(documents, ingestion, embeddings, DeterministicEmbeddingModel())
    app.dependency_overrides[get_document_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


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

        def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[] for _text in texts]

    monkeypatch.setattr(
        dependencies,
        "SentenceTransformerEmbeddingModel",
        FakeTransformerEmbeddingModel,
    )

    model = dependencies._create_embedding_model(Settings(_env_file=None))

    assert isinstance(model, FakeTransformerEmbeddingModel)
    assert created_transformer_models == 1


def test_upload_markdown_document(client: TestClient) -> None:
    response = client.post(
        "/corpora/product-notes/documents",
        files={
            "file": (
                "notes.md",
                b"# Overview\n\nBody text.\n\n## Details\n\nMore body text.",
                "text/markdown",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["corpus_id"] == "product-notes"
    assert payload["filename"] == "notes.md"
    assert payload["document_type"] == "markdown"
    assert "status" not in payload
    assert "content_type" not in payload
    assert "heading_paths" not in payload
    assert "body" not in payload
    assert len(payload["document_id"]) == 24


def test_markdown_document_can_be_read_from_its_corpus(client: TestClient) -> None:
    upload_response = client.post(
        "/corpora/research/documents",
        files={"file": ("paper.markdown", b"# Findings\n\nEvidence.", "text/markdown")},
    )
    document_id = upload_response.json()["document_id"]

    response = client.get(f"/corpora/research/documents/{document_id}")

    assert response.status_code == 200
    assert response.json()["document_id"] == document_id


def test_markdown_document_inspection_returns_structure_and_embedding_metadata(
    client: TestClient,
) -> None:
    upload_response = client.post(
        "/corpora/research/documents",
        files={
            "file": (
                "paper.markdown",
                b"# Findings\n\nEvidence.\n\n## Setup\n\n- install\n- run",
                "text/markdown",
            )
        },
    )
    document_id = upload_response.json()["document_id"]

    response = client.get(f"/corpora/research/documents/{document_id}/inspection")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["body"].startswith("# Findings")
    assert [
        (section["heading_title"], section["section_path"]) for section in payload["sections"]
    ] == [
        ("Findings", ["Findings"]),
        ("Setup", ["Findings", "Setup"]),
    ]
    assert [
        (
            passage["kind"],
            passage["text"],
            passage["start_line"],
            passage["end_line"],
            passage["embedding"]["vector_dimensions"],
        )
        for section in payload["sections"]
        for passage in section["passages"]
    ] == [
        ("paragraph", "Evidence.", 3, 3, 8),
        ("list", "- install\n- run", 7, 8, 8),
    ]


def test_document_lookup_is_limited_to_corpus(client: TestClient) -> None:
    upload_response = client.post(
        "/corpora/corpus-a/documents",
        files={"file": ("brief.md", b"# Corpus\n\nA-only.", "text/markdown")},
    )
    document_id = upload_response.json()["document_id"]

    response = client.get(f"/corpora/corpus-b/documents/{document_id}")

    assert response.status_code == 404

    inspection_response = client.get(f"/corpora/corpus-b/documents/{document_id}/inspection")

    assert inspection_response.status_code == 404


def test_rejects_non_markdown_upload(client: TestClient) -> None:
    response = client.post(
        "/corpora/product-notes/documents",
        files={"file": ("notes.txt", b"# Looks like markdown.", "text/plain")},
    )

    assert response.status_code == 415
    assert (
        response.json()["detail"]
        == "Only Markdown files with .md or .markdown extensions are supported."
    )
