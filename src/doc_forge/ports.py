from __future__ import annotations

from typing import Protocol

from doc_forge.documents import DocumentRecord
from doc_forge.embedding.records import PassageEmbeddingRecord


class DocumentRepository(Protocol):
    def list_for_corpus(self, corpus_id: str) -> list[DocumentRecord]: ...

    def get(self, *, corpus_id: str, document_id: str) -> DocumentRecord: ...


class EmbeddingRepository(Protocol):
    def list_for_document(
        self,
        *,
        corpus_id: str,
        document_id: str,
    ) -> list[PassageEmbeddingRecord]: ...


class DocumentIngestionRepository(Protocol):
    def save_document_with_embeddings(
        self,
        document: DocumentRecord,
        embeddings: list[PassageEmbeddingRecord],
    ) -> None: ...
