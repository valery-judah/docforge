from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from doc_forge.answering import AnswerService
from doc_forge.app.api import create_app
from doc_forge.app.dependencies import (
    get_answer_service,
    get_document_service,
    get_retrieval_service,
)
from doc_forge.app.settings import Settings
from doc_forge.embedding.deterministic import DeterministicEmbeddingModel
from doc_forge.persistence.in_memory_documents import InMemoryDocumentStore
from doc_forge.persistence.in_memory_embeddings import InMemoryEmbeddingStore
from doc_forge.persistence.in_memory_ingestion import InMemoryDocumentIngestionRepository
from doc_forge.retrieval import RetrievalService
from doc_forge.services import DocumentService


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(Settings(embedding_model="deterministic", _env_file=None))
    documents = InMemoryDocumentStore()
    embeddings = InMemoryEmbeddingStore()
    ingestion = InMemoryDocumentIngestionRepository(
        documents=documents,
        embeddings=embeddings,
    )
    embedding_model = DeterministicEmbeddingModel()
    document_service = DocumentService(documents, ingestion, embeddings, embedding_model)
    retrieval_service = RetrievalService(embeddings, embedding_model)
    answer_service = AnswerService(retrieval_service)
    app.dependency_overrides[get_document_service] = lambda: document_service
    app.dependency_overrides[get_retrieval_service] = lambda: retrieval_service
    app.dependency_overrides[get_answer_service] = lambda: answer_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
