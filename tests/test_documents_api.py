from __future__ import annotations

from fastapi.testclient import TestClient


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
