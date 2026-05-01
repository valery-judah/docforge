"""Prepare local embedding model artifacts for Docker-backed runs."""

from __future__ import annotations

import argparse
import importlib
import re
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol, cast

DEFAULT_MODEL_ROOT = Path("data/models")


class _SentenceTransformerModel(Protocol):
    def save(self, path: str) -> None: ...


def model_directory_name(model_id: str) -> str:
    """Return the local directory name used for a model identifier."""

    normalized = model_id.strip().replace("\\", "/").rstrip("/")
    if not normalized:
        raise ValueError("model identifier must not be empty")

    name = normalized.rsplit("/", maxsplit=1)[-1]
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    if not safe_name:
        raise ValueError(f"model identifier does not contain a usable directory name: {model_id!r}")
    return safe_name


def require_sentence_transformers() -> None:
    try:
        importlib.import_module("sentence_transformers")
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "sentence-transformers is not installed. Run `uv sync --group llm` "
            "to prepare local embedding models."
        ) from exc


def _default_loader(model_id: str) -> _SentenceTransformerModel:
    require_sentence_transformers()
    sentence_transformers = importlib.import_module("sentence_transformers")
    sentence_transformer_cls = cast(Any, sentence_transformers).SentenceTransformer
    return cast(_SentenceTransformerModel, sentence_transformer_cls(model_id))


def prepare_sentence_transformer_model(
    model_id: str,
    *,
    output_root: Path = DEFAULT_MODEL_ROOT,
    loader: Callable[[str], _SentenceTransformerModel] | None = None,
) -> Path:
    """Download/load a sentence-transformers model and save it under output_root."""

    target = output_root / model_directory_name(model_id)
    target.mkdir(parents=True, exist_ok=True)
    model = (loader or _default_loader)(model_id)
    model.save(str(target))
    return target


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m doc_forge.devtools.embedding_models")
    parser.add_argument("model", help="Sentence-transformers model identifier to prepare.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_MODEL_ROOT,
        help="Directory where local model folders are written.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        path = prepare_sentence_transformer_model(args.model, output_root=args.output_root)
    except (RuntimeError, ValueError, OSError) as exc:
        parser.exit(1, f"{exc}\n")

    print(path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
