from __future__ import annotations

from typing import Protocol

from doc_forge.documents import DocumentRecord


class DocumentRepository(Protocol):
    def save(self, document: DocumentRecord) -> None: ...

    def list_for_corpus(self, corpus_id: str) -> list[DocumentRecord]: ...

    def get(self, *, corpus_id: str, document_id: str) -> DocumentRecord: ...
