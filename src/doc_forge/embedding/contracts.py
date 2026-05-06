from __future__ import annotations

from typing import Protocol, runtime_checkable

from doc_forge.embedding.vectors import EmbeddingBatch


@runtime_checkable
class EmbeddingModel(Protocol):
    def embed_texts(self, texts: list[str]) -> EmbeddingBatch: ...
