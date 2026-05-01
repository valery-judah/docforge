from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from doc_forge import __version__
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
    app = create_app(Settings(_env_file=None))
    documents = InMemoryDocumentStore()
    embeddings = InMemoryEmbeddingStore()
    ingestion = InMemoryDocumentIngestionRepository(
        documents=documents,
        embeddings=embeddings,
    )
    service = DocumentService(documents, ingestion, DeterministicEmbeddingModel())
    app.dependency_overrides[get_document_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_package_imports() -> None:
    assert __version__ == "0.1.0"


def test_readyz_payload() -> None:
    assert readyz() == {"status": "ok"}


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
    app = create_app(Settings(_env_file=None))

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


def test_document_lookup_is_limited_to_corpus(client: TestClient) -> None:
    upload_response = client.post(
        "/corpora/corpus-a/documents",
        files={"file": ("brief.md", b"# Corpus\n\nA-only.", "text/markdown")},
    )
    document_id = upload_response.json()["document_id"]

    response = client.get(f"/corpora/corpus-b/documents/{document_id}")

    assert response.status_code == 404


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
