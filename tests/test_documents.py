from __future__ import annotations

import pytest

from doc_forge.documents import (
    DocumentNotFound,
    DocumentType,
    InvalidDocumentEncoding,
    UnsupportedDocumentType,
    ingest_markdown_document,
)
from doc_forge.persistence.in_memory_documents import InMemoryDocumentStore


def test_markdown_ingestion_assigns_deterministic_document_id() -> None:
    first_document = ingest_markdown_document(
        corpus_id="corpus-a",
        filename="notes.md",
        raw_content=b"# Overview\n\nBody.",
    )
    second_document = ingest_markdown_document(
        corpus_id="corpus-a",
        filename="notes.md",
        raw_content=b"# Overview\n\nBody.",
    )

    assert first_document.document_id == second_document.document_id


def test_markdown_ingestion_ids_change_by_corpus_or_content() -> None:
    first_document = ingest_markdown_document(
        corpus_id="corpus-a",
        filename="notes.md",
        raw_content=b"# Overview\n\nBody.",
    )
    other_corpus_document = ingest_markdown_document(
        corpus_id="corpus-b",
        filename="notes.md",
        raw_content=b"# Overview\n\nBody.",
    )
    other_content_document = ingest_markdown_document(
        corpus_id="corpus-a",
        filename="notes.md",
        raw_content=b"# Overview\n\nDifferent body.",
    )

    assert first_document.document_id != other_corpus_document.document_id
    assert first_document.document_id != other_content_document.document_id


def test_markdown_ingestion_sets_document_type() -> None:
    document = ingest_markdown_document(
        corpus_id="corpus-a",
        filename="notes.markdown",
        raw_content=b"# Overview\n\n## Details\n\n### Deep Dive\n\n###### Appendix",
    )

    assert document.document_type == DocumentType.MARKDOWN


def test_markdown_ingestion_rejects_invalid_utf8() -> None:
    with pytest.raises(InvalidDocumentEncoding):
        ingest_markdown_document(
            corpus_id="corpus-a",
            filename="notes.md",
            raw_content=b"\xff",
        )


def test_markdown_ingestion_rejects_unsupported_filenames() -> None:
    with pytest.raises(UnsupportedDocumentType):
        ingest_markdown_document(
            corpus_id="corpus-a",
            filename="notes.txt",
            raw_content=b"# Overview",
        )


def test_document_store_lookup_is_limited_to_corpus() -> None:
    store = InMemoryDocumentStore()
    document = ingest_markdown_document(
        corpus_id="corpus-a",
        filename="notes.md",
        raw_content=b"# Overview",
    )
    store.save(document)

    assert store.get(corpus_id="corpus-a", document_id=document.document_id) == document

    with pytest.raises(DocumentNotFound):
        store.get(corpus_id="corpus-b", document_id=document.document_id)
