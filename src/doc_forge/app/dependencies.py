from __future__ import annotations

from doc_forge.persistence.in_memory_documents import InMemoryDocumentStore
from doc_forge.services import DocumentService

_document_repository = InMemoryDocumentStore()
_document_service = DocumentService(_document_repository)


def get_document_service() -> DocumentService:
    return _document_service
