from __future__ import annotations

from dataclasses import dataclass

from doc_forge.documents import (
    DocumentRecord,
    DocumentStatus,
    DocumentType,
    ingest_markdown_document,
)
from doc_forge.ports import DocumentRepository


@dataclass(frozen=True)
class IngestMarkdownDocumentCommand:
    corpus_id: str
    filename: str | None
    raw_content: bytes


@dataclass(frozen=True)
class DocumentSummary:
    document_id: str
    corpus_id: str
    filename: str
    status: DocumentStatus
    document_type: DocumentType


class DocumentService:
    def __init__(self, document_repository: DocumentRepository) -> None:
        self._document_repository = document_repository

    def ingest_markdown(
        self,
        command: IngestMarkdownDocumentCommand,
    ) -> DocumentSummary:
        document = ingest_markdown_document(
            corpus_id=command.corpus_id,
            filename=command.filename,
            raw_content=command.raw_content,
        )
        self._document_repository.save(document)
        return _to_document_summary(document)

    def list_documents(self, *, corpus_id: str) -> list[DocumentSummary]:
        return [
            _to_document_summary(document)
            for document in self._document_repository.list_for_corpus(corpus_id)
        ]

    def get_document(self, *, corpus_id: str, document_id: str) -> DocumentSummary:
        return _to_document_summary(
            self._document_repository.get(corpus_id=corpus_id, document_id=document_id)
        )


def _to_document_summary(document: DocumentRecord) -> DocumentSummary:
    return DocumentSummary(
        document_id=document.document_id,
        corpus_id=document.corpus_id,
        filename=document.filename,
        status=document.status,
        document_type=document.document_type,
    )
