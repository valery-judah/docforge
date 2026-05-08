from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from fastapi import Request

from doc_forge.answer_synthesis import (
    AnswerSynthesizer,
    DeterministicAnswerSynthesizer,
    OllamaAnswerSynthesizer,
)
from doc_forge.answering import AnswerService
from doc_forge.app.runtime_checks import validate_runtime
from doc_forge.app.settings import (
    AnswerSynthesizerBackend,
    EmbeddingModelRegime,
    Settings,
    get_settings,
)
from doc_forge.embedding.contracts import EmbeddingModel
from doc_forge.embedding.deterministic import DeterministicEmbeddingModel
from doc_forge.embedding.sentence_transformer import SentenceTransformerEmbeddingModel
from doc_forge.persistence.in_memory_documents import InMemoryDocumentStore
from doc_forge.persistence.in_memory_embeddings import InMemoryEmbeddingStore
from doc_forge.persistence.in_memory_ingestion import InMemoryDocumentIngestionRepository
from doc_forge.retrieval import RetrievalService
from doc_forge.services import DocumentService


@dataclass(frozen=True)
class AppContainer:
    settings: Settings
    document_service: DocumentService
    retrieval_service: RetrievalService
    answer_service: AnswerService


def create_app_container(settings: Settings | None = None) -> AppContainer:
    if settings is None:
        settings = get_settings()
    validate_runtime(settings)
    document_service, retrieval_service, answer_service = _create_services(settings)
    return AppContainer(
        settings=settings,
        document_service=document_service,
        retrieval_service=retrieval_service,
        answer_service=answer_service,
    )


def _create_embedding_model(settings: Settings) -> EmbeddingModel:
    if settings.embedding_model is EmbeddingModelRegime.DETERMINISTIC:
        return DeterministicEmbeddingModel()
    if settings.embedding_model is EmbeddingModelRegime.TRANSFORMER:
        return SentenceTransformerEmbeddingModel()
    raise RuntimeError("DOC_FORGE_EMBEDDING_MODEL must be one of: deterministic, transformer")


def _create_answer_synthesizer(settings: Settings) -> AnswerSynthesizer:
    if settings.answer_synthesizer_backend is AnswerSynthesizerBackend.DETERMINISTIC:
        return DeterministicAnswerSynthesizer()
    if settings.answer_synthesizer_backend is AnswerSynthesizerBackend.OLLAMA:
        return OllamaAnswerSynthesizer(
            base_url=settings.ollama_base_url,
            model=settings.answer_synthesizer_model,
            timeout_seconds=settings.answer_synthesis_timeout_seconds,
        )
    raise RuntimeError("DOC_FORGE_ANSWER_SYNTHESIZER_BACKEND must be one of: deterministic, ollama")


def _create_services(settings: Settings) -> tuple[DocumentService, RetrievalService, AnswerService]:
    embedding_model = _create_embedding_model(settings)
    answer_synthesizer = _create_answer_synthesizer(settings)

    document_repository = InMemoryDocumentStore()
    embedding_repository = InMemoryEmbeddingStore()
    document_ingestion_repository = InMemoryDocumentIngestionRepository(
        documents=document_repository,
        embeddings=embedding_repository,
    )

    document_service = DocumentService(
        document_repository=document_repository,
        document_ingestion_repository=document_ingestion_repository,
        embedding_repository=embedding_repository,
        embedding_model=embedding_model,
    )
    retrieval_service = RetrievalService(
        embedding_repository=embedding_repository,
        embedding_model=embedding_model,
    )
    answer_service = AnswerService(
        retrieval_service,
        answer_synthesizer,
        top_k=settings.answering_top_k,
        min_score=settings.answering_min_score,
    )
    return document_service, retrieval_service, answer_service


def get_document_service(request: Request) -> DocumentService:
    container = cast(AppContainer | None, getattr(request.app.state, "container", None))
    if container is None:
        raise RuntimeError("Application container is not initialized.")
    return container.document_service


def get_retrieval_service(request: Request) -> RetrievalService:
    container = cast(AppContainer | None, getattr(request.app.state, "container", None))
    if container is None:
        raise RuntimeError("Application container is not initialized.")
    return container.retrieval_service


def get_answer_service(request: Request) -> AnswerService:
    container = cast(AppContainer | None, getattr(request.app.state, "container", None))
    if container is None:
        raise RuntimeError("Application container is not initialized.")
    return container.answer_service
