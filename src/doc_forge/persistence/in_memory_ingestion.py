from __future__ import annotations

from threading import Lock

from doc_forge.documents import DocumentRecord
from doc_forge.embeddings import PassageEmbeddingRecord
from doc_forge.persistence.in_memory_documents import InMemoryDocumentStore
from doc_forge.persistence.in_memory_embeddings import InMemoryEmbeddingStore


class InMemoryDocumentIngestionRepository:
    def __init__(
        self,
        *,
        documents: InMemoryDocumentStore,
        embeddings: InMemoryEmbeddingStore,
    ) -> None:
        self._documents = documents
        self._embeddings = embeddings
        self._lock = Lock()

    def save_document_with_embeddings(
        self,
        document: DocumentRecord,
        embeddings: list[PassageEmbeddingRecord],
    ) -> None:
        with self._lock:
            document_snapshot = self._documents.snapshot()
            embedding_snapshot = self._embeddings.snapshot()
            try:
                self._documents.save(document)
                self._embeddings.save_many(embeddings)
            except Exception:
                self._documents.restore(document_snapshot)
                self._embeddings.restore(embedding_snapshot)
                raise
