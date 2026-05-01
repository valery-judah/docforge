from __future__ import annotations

from doc_forge.app.settings import EmbeddingModelRegime, get_settings
from doc_forge.embeddings import DeterministicEmbeddingModel, SentenceTransformerEmbeddingModel
from doc_forge.persistence.in_memory_documents import InMemoryDocumentStore
from doc_forge.persistence.in_memory_embeddings import InMemoryEmbeddingStore
from doc_forge.persistence.in_memory_ingestion import InMemoryDocumentIngestionRepository
from doc_forge.ports import EmbeddingModel
from doc_forge.services import DocumentService

_document_repository = InMemoryDocumentStore()
_embedding_repository = InMemoryEmbeddingStore()
_document_ingestion_repository = InMemoryDocumentIngestionRepository(
    documents=_document_repository,
    embeddings=_embedding_repository,
)
_settings = get_settings()
_embedding_model: EmbeddingModel
if _settings.embedding_model is EmbeddingModelRegime.DETERMINISTIC:
    _embedding_model = DeterministicEmbeddingModel()
elif _settings.embedding_model is EmbeddingModelRegime.TRANSFORMER:
    _embedding_model = SentenceTransformerEmbeddingModel()
else:
    raise RuntimeError("DOC_FORGE_EMBEDDING_MODEL must be one of: deterministic, transformer")

_document_service = DocumentService(
    document_repository=_document_repository,
    document_ingestion_repository=_document_ingestion_repository,
    embedding_model=_embedding_model,
)


def get_document_service() -> DocumentService:
    return _document_service
