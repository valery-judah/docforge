from __future__ import annotations

from doc_forge.embeddings import SentenceTransformerEmbeddingModel


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
    ) -> list[list[float | int | str]]:
        assert normalize_embeddings is True
        assert convert_to_numpy is True
        assert show_progress_bar is False
        self.calls.append(list(sentences))
        return [[0.5, -0.25], [1, "2.5"]]


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
    assert vectors == [[0.5, -0.25], [1.0, 2.5]]
