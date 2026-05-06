from __future__ import annotations

from typing import Protocol, runtime_checkable

from doc_forge.embedding.vectors import EmbeddingBatch, EmbeddingVector


@runtime_checkable
class EmbeddingModel(Protocol):
    def embed_text(self, text: str) -> EmbeddingVector: ...

    def embed_texts(self, texts: list[str]) -> EmbeddingBatch: ...
