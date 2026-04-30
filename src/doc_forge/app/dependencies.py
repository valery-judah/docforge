from __future__ import annotations

from doc_forge.embeddings import DeterministicEmbeddingModel
from doc_forge.persistence.in_memory_documents import InMemoryDocumentStore
from doc_forge.persistence.in_memory_embeddings import InMemoryEmbeddingStore
from doc_forge.persistence.in_memory_ingestion import InMemoryDocumentIngestionRepository
from doc_forge.services import DocumentService

_document_repository = InMemoryDocumentStore()
_embedding_repository = InMemoryEmbeddingStore()
_document_ingestion_repository = InMemoryDocumentIngestionRepository(
    documents=_document_repository,
    embeddings=_embedding_repository,
)
_embedding_model = DeterministicEmbeddingModel()

_document_service = DocumentService(
    document_repository=_document_repository,
    document_ingestion_repository=_document_ingestion_repository,
    embedding_model=_embedding_model,
)


def get_document_service() -> DocumentService:
    return _document_service
