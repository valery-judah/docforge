from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from fastapi import Request

from doc_forge.app.runtime_checks import validate_runtime
from doc_forge.app.settings import EmbeddingModelRegime, Settings, get_settings
from doc_forge.embedding.contracts import EmbeddingModel
from doc_forge.embedding.deterministic import DeterministicEmbeddingModel
from doc_forge.embedding.sentence_transformer import SentenceTransformerEmbeddingModel
from doc_forge.persistence.in_memory_documents import InMemoryDocumentStore
from doc_forge.persistence.in_memory_embeddings import InMemoryEmbeddingStore
from doc_forge.persistence.in_memory_ingestion import InMemoryDocumentIngestionRepository
from doc_forge.services import DocumentService


@dataclass(frozen=True)
class AppContainer:
    settings: Settings
    document_service: DocumentService


def create_app_container(settings: Settings | None = None) -> AppContainer:
    if settings is None:
        settings = get_settings()
    validate_runtime(settings)
    return AppContainer(
        settings=settings,
        document_service=_create_document_service(settings),
    )


def _create_embedding_model(settings: Settings) -> EmbeddingModel:
    if settings.embedding_model is EmbeddingModelRegime.DETERMINISTIC:
        return DeterministicEmbeddingModel()
    if settings.embedding_model is EmbeddingModelRegime.TRANSFORMER:
        return SentenceTransformerEmbeddingModel()
    raise RuntimeError("DOC_FORGE_EMBEDDING_MODEL must be one of: deterministic, transformer")


def _create_document_service(settings: Settings) -> DocumentService:
    embedding_model = _create_embedding_model(settings)

    document_repository = InMemoryDocumentStore()
    embedding_repository = InMemoryEmbeddingStore()
    document_ingestion_repository = InMemoryDocumentIngestionRepository(
        documents=document_repository,
        embeddings=embedding_repository,
    )

    return DocumentService(
        document_repository=document_repository,
        document_ingestion_repository=document_ingestion_repository,
        embedding_repository=embedding_repository,
        embedding_model=embedding_model,
    )


def get_document_service(request: Request) -> DocumentService:
    container = cast(AppContainer | None, getattr(request.app.state, "container", None))
    if container is None:
        raise RuntimeError("Application container is not initialized.")
    return container.document_service
