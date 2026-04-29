from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from doc_forge.documents import DocumentNotFound, DocumentRecord, DocumentType
from doc_forge.services import (
    DocumentService,
    DocumentSummary,
    IngestMarkdownDocumentCommand,
)


@dataclass
class RecordingDocumentRepository:
    saved_documents: list[DocumentRecord] = field(default_factory=list)

    def save(self, document: DocumentRecord) -> None:
        self.saved_documents.append(document)

    def list_for_corpus(self, corpus_id: str) -> list[DocumentRecord]:
        return [document for document in self.saved_documents if document.corpus_id == corpus_id]

    def get(self, *, corpus_id: str, document_id: str) -> DocumentRecord:
        for document in self.saved_documents:
            if document.corpus_id == corpus_id and document.document_id == document_id:
                return document

        raise DocumentNotFound


def test_document_service_saves_accepted_markdown_document() -> None:
    repository = RecordingDocumentRepository()
    service = DocumentService(repository)

    document = service.ingest_markdown(
        IngestMarkdownDocumentCommand(
            corpus_id="corpus-a",
            filename="notes.md",
            raw_content=b"# Overview\n\nBody.",
        )
    )

    saved_document = repository.saved_documents[0]
    assert document == DocumentSummary(
        document_id=saved_document.document_id,
        corpus_id="corpus-a",
        filename="notes.md",
        status=saved_document.status,
        document_type=DocumentType.MARKDOWN,
    )
    assert not hasattr(document, "body")
    assert document.corpus_id == "corpus-a"
    assert document.filename == "notes.md"


def test_document_service_lists_documents_by_corpus() -> None:
    repository = RecordingDocumentRepository()
    service = DocumentService(repository)
    corpus_document = service.ingest_markdown(
        IngestMarkdownDocumentCommand(
            corpus_id="corpus-a",
            filename="a.md",
            raw_content=b"# A",
        )
    )
    service.ingest_markdown(
        IngestMarkdownDocumentCommand(
            corpus_id="corpus-b",
            filename="b.md",
            raw_content=b"# B",
        )
    )

    assert service.list_documents(corpus_id="corpus-a") == [corpus_document]


def test_document_service_gets_document_by_corpus_and_id() -> None:
    repository = RecordingDocumentRepository()
    service = DocumentService(repository)
    document = service.ingest_markdown(
        IngestMarkdownDocumentCommand(
            corpus_id="corpus-a",
            filename="notes.md",
            raw_content=b"# Overview",
        )
    )

    assert service.get_document(corpus_id="corpus-a", document_id=document.document_id) == document

    with pytest.raises(DocumentNotFound):
        service.get_document(corpus_id="corpus-b", document_id=document.document_id)
