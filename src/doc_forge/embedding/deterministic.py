from __future__ import annotations

from hashlib import sha256
from math import sqrt

from doc_forge.embedding.contracts import EmbeddingModel


class DeterministicEmbeddingModel(EmbeddingModel):
    def __init__(
        self,
        *,
        dimensions: int = 8,
        model_name: str = "deterministic-hash-v1",
    ) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self._dimensions = dimensions
        self.model_name = model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        for token in text.lower().split():
            digest = sha256(token.encode("utf-8")).digest()
            bucket = digest[0] % self._dimensions
            sign = 1.0 if digest[1] % 2 == 0 else -1.0
            vector[bucket] += sign

        magnitude = sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]
