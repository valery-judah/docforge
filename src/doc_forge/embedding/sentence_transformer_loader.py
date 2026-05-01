from __future__ import annotations

import importlib
from collections.abc import Sequence
from typing import Any, Protocol, cast


class SentenceTransformerBackend(Protocol):
    def encode(
        self,
        sentences: Sequence[str],
        *,
        normalize_embeddings: bool = True,
        convert_to_numpy: bool = True,
        show_progress_bar: bool = False,
    ) -> object: ...


def load_sentence_transformer_model(model_name: str) -> SentenceTransformerBackend:
    _require_sentence_transformers()
    sentence_transformers = importlib.import_module("sentence_transformers")
    sentence_transformer_cls = cast(Any, sentence_transformers).SentenceTransformer
    return cast(SentenceTransformerBackend, sentence_transformer_cls(model_name))


def _require_sentence_transformers() -> None:
    try:
        importlib.import_module("sentence_transformers")
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "sentence-transformers is not installed. Run `uv sync --group llm` "
            "to enable model-backed embeddings."
        ) from exc
