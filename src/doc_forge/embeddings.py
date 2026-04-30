from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import sqrt


@dataclass(frozen=True)
class PassageEmbeddingRecord:
    embedding_id: str
    corpus_id: str
    document_id: str
    section_id: str
    passage_id: str
    ordinal: int
    text: str
    heading_path: tuple[str, ...]
    start_line: int
    end_line: int
    vector: tuple[float, ...]


class DeterministicEmbeddingModel:
    def __init__(self, *, dimensions: int = 8) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self._dimensions = dimensions

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
