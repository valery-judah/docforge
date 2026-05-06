from __future__ import annotations

import pytest

from doc_forge.embedding import EmbeddingModel
from doc_forge.embedding.deterministic import DeterministicEmbeddingModel
from doc_forge.embedding.sentence_transformer import SentenceTransformerEmbeddingModel
from doc_forge.embedding.vectors import EmbeddingBatch, EmbeddingVector


class _ArrayLike:
    def __init__(self, value: list[list[float | int | str]]) -> None:
        self._value = value

    def tolist(self) -> list[list[float | int | str]]:
        return self._value


class _FakeSentenceTransformerModel:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def encode(
        self,
        sentences,
        *,
        normalize_embeddings: bool = True,
        convert_to_numpy: bool = True,
        show_progress_bar: bool = False,
    ) -> _ArrayLike:
        assert normalize_embeddings is True
        assert convert_to_numpy is True
        assert show_progress_bar is False
        self.calls.append(list(sentences))
        return _ArrayLike([[0.5, -0.25], [1, "2.5"]])


def test_sentence_transformer_embedding_model_uses_loader_and_coerces_vectors() -> None:
    fake_model = _FakeSentenceTransformerModel()
    seen_model_names: list[str] = []

    def _loader(model_name: str) -> _FakeSentenceTransformerModel:
        seen_model_names.append(model_name)
        return fake_model

    model = SentenceTransformerEmbeddingModel(
        model_name="sentence-transformers/test-model",
        loader=_loader,
    )

    vectors = model.embed_texts(["alpha", "beta"])

    assert seen_model_names == ["sentence-transformers/test-model"]
    assert fake_model.calls == [["alpha", "beta"]]
    assert vectors == EmbeddingBatch(
        [
            EmbeddingVector([0.5, -0.25]),
            EmbeddingVector([1.0, 2.5]),
        ]
    )


def test_embedding_vector_coerces_values_and_exposes_dimensions() -> None:
    vector = EmbeddingVector([0.5, 1, "2.5"])

    assert vector.values == (0.5, 1.0, 2.5)
    assert vector.dimensions == 3
    assert list(vector) == [0.5, 1.0, 2.5]


def test_embedding_vector_rejects_empty_values() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        EmbeddingVector([])


def test_embedding_batch_allows_empty_batches() -> None:
    batch = EmbeddingBatch([])

    assert len(batch) == 0
    assert list(batch) == []


def test_embedding_batch_rejects_mixed_dimensions() -> None:
    with pytest.raises(ValueError, match="consistent dimensions"):
        EmbeddingBatch(
            [
                EmbeddingVector([1.0]),
                EmbeddingVector([1.0, 2.0]),
            ]
        )


def test_embedding_models_expose_embedding_contract() -> None:
    fake_model = _FakeSentenceTransformerModel()

    deterministic_model = DeterministicEmbeddingModel()
    transformer_model = SentenceTransformerEmbeddingModel(loader=lambda _model_name: fake_model)

    assert isinstance(deterministic_model, EmbeddingModel)
    assert isinstance(transformer_model, EmbeddingModel)
