from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingModel(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
