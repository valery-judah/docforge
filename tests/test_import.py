from __future__ import annotations

from fastapi.testclient import TestClient

from doc_forge import __version__
from doc_forge.app.api import app, readyz

client = TestClient(app)


def test_package_imports() -> None:
    assert __version__ == "0.1.0"


def test_readyz_payload() -> None:
    assert readyz() == {"status": "ok"}


def test_upload_markdown_document() -> None:
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
    assert payload["status"] == "ready"
    assert payload["document_type"] == "markdown"
    assert "content_type" not in payload
    assert "heading_paths" not in payload
    assert "body" not in payload
    assert len(payload["document_id"]) == 24


def test_markdown_document_can_be_read_from_its_corpus() -> None:
    upload_response = client.post(
        "/corpora/research/documents",
        files={"file": ("paper.markdown", b"# Findings\n\nEvidence.", "text/markdown")},
    )
    document_id = upload_response.json()["document_id"]

    response = client.get(f"/corpora/research/documents/{document_id}")

    assert response.status_code == 200
    assert response.json()["document_id"] == document_id


def test_document_lookup_is_limited_to_corpus() -> None:
    upload_response = client.post(
        "/corpora/corpus-a/documents",
        files={"file": ("brief.md", b"# Corpus\n\nA-only.", "text/markdown")},
    )
    document_id = upload_response.json()["document_id"]

    response = client.get(f"/corpora/corpus-b/documents/{document_id}")

    assert response.status_code == 404


def test_rejects_non_markdown_upload() -> None:
    response = client.post(
        "/corpora/product-notes/documents",
        files={"file": ("notes.txt", b"# Looks like markdown.", "text/plain")},
    )

    assert response.status_code == 415
    assert (
        response.json()["detail"]
        == "Only Markdown files with .md or .markdown extensions are supported."
    )
