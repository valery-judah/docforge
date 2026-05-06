from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, cast

from doc_forge.embedding.contracts import EmbeddingModel
from doc_forge.embedding.sentence_transformer_loader import (
    SentenceTransformerBackend,
    load_sentence_transformer_model,
)
from doc_forge.embedding.vectors import EmbeddingBatch, EmbeddingVector


class SentenceTransformerEmbeddingModel(EmbeddingModel):
    def __init__(
        self,
        *,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        loader: Callable[[str], SentenceTransformerBackend] | None = None,
    ) -> None:
        self.model_name = model_name
        self._model = (loader or load_sentence_transformer_model)(model_name)

    def embed_texts(self, texts: list[str]) -> EmbeddingBatch:
        encoded = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return _coerce_vector_rows(encoded)

    def embed_text(self, text: str) -> EmbeddingVector:
        return self.embed_texts([text]).single()


def _coerce_vector_rows(encoded: object) -> EmbeddingBatch:
    return EmbeddingBatch(
        EmbeddingVector(_coerce_float(value) for value in row) for row in _to_python_rows(encoded)
    )


def _to_python_rows(value: object) -> list[list[object]]:
    if hasattr(value, "tolist"):
        value = cast(Any, value).tolist()
    rows = list(cast(Sequence[object], value))
    normalized: list[list[object]] = []
    for row in rows:
        if hasattr(row, "tolist"):
            row = cast(Any, row).tolist()
        normalized.append(list(cast(Sequence[object], row)))
    return normalized


def _coerce_float(value: object) -> float:
    return float(cast(float | int | str, value))
