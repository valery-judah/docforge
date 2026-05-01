from __future__ import annotations

import importlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from hashlib import sha256
from math import sqrt
from typing import Any, Protocol, cast


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


class _SentenceTransformerModel(Protocol):
    def encode(
        self,
        sentences: Sequence[str],
        *,
        normalize_embeddings: bool = True,
        convert_to_numpy: bool = True,
        show_progress_bar: bool = False,
    ) -> object: ...


def require_sentence_transformers() -> None:
    try:
        importlib.import_module("sentence_transformers")
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "sentence-transformers is not installed. Run `uv sync --group llm` "
            "to enable model-backed embeddings."
        ) from exc


def _default_sentence_transformer_loader(model_name: str) -> _SentenceTransformerModel:
    require_sentence_transformers()
    sentence_transformers = importlib.import_module("sentence_transformers")
    sentence_transformer_cls = cast(Any, sentence_transformers).SentenceTransformer
    return cast(_SentenceTransformerModel, sentence_transformer_cls(model_name))


class SentenceTransformerEmbeddingModel:
    def __init__(
        self,
        *,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        loader: Callable[[str], _SentenceTransformerModel] | None = None,
    ) -> None:
        self.model_name = model_name
        self._model = (loader or _default_sentence_transformer_loader)(model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        encoded = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return _coerce_vector_rows(encoded)


def _coerce_vector_rows(encoded: object) -> list[list[float]]:
    return [[_coerce_float(value) for value in row] for row in _to_python_rows(encoded)]


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
