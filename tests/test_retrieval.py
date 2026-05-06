from __future__ import annotations

from math import isclose

import pytest

from doc_forge.embedding.records import PassageEmbeddingRecord
from doc_forge.embedding.vectors import EmbeddingBatch, EmbeddingVector
from doc_forge.persistence.in_memory_embeddings import InMemoryEmbeddingStore
from doc_forge.retrieval import RetrievalQuery, RetrievalResult, RetrievalService


class StaticEmbeddingModel:
    # Retrieval ranking tests need exact vector control; the real deterministic model would couple
    # these scenarios to hashing behavior instead of the ranking invariant under test.
    def __init__(self, vectors_by_text: dict[str, list[float]]) -> None:
        self._vectors_by_text = vectors_by_text

    def embed_text(self, text: str) -> EmbeddingVector:
        return EmbeddingVector(self._vectors_by_text[text])

    def embed_texts(self, texts: list[str]) -> EmbeddingBatch:
        return EmbeddingBatch(EmbeddingVector(self._vectors_by_text[text]) for text in texts)


class CapturingEmbeddingModel:
    # This model keeps the assertion focused on query normalization by recording the text passed
    # to embedding, while still returning a predictable vector for retrieval.
    def __init__(self, vector: list[float]) -> None:
        self._vector = vector
        self.requests: list[str] = []

    def embed_text(self, text: str) -> EmbeddingVector:
        self.requests.append(text)
        return EmbeddingVector(self._vector)

    def embed_texts(self, texts: list[str]) -> EmbeddingBatch:
        return EmbeddingBatch(EmbeddingVector(self._vector) for _text in texts)


def given_passage_embedding(
    *,
    corpus_id: str,
    document_id: str,
    passage_id: str,
    ordinal: int,
    text: str,
    vector: EmbeddingVector,
    section_id: str | None = None,
    heading_path: tuple[str, ...] = ("Guide",),
    start_line: int | None = None,
    end_line: int | None = None,
) -> PassageEmbeddingRecord:
    return PassageEmbeddingRecord(
        embedding_id=f"{passage_id}:embedding:0",
        corpus_id=corpus_id,
        document_id=document_id,
        section_id=section_id or f"{passage_id}:section",
        passage_id=passage_id,
        ordinal=ordinal,
        text=text,
        heading_path=heading_path,
        start_line=start_line or ordinal + 1,
        end_line=end_line or ordinal + 1,
        vector=vector,
    )


def given_retrieval_service(
    *,
    embeddings: list[PassageEmbeddingRecord],
    query_vectors: dict[str, list[float]],
) -> RetrievalService:
    embedding_store = InMemoryEmbeddingStore()
    embedding_store.save_many(embeddings)
    return RetrievalService(embedding_store, StaticEmbeddingModel(query_vectors))


def when_retrieving(
    retrieval: RetrievalService,
    *,
    question: str,
    corpus_id: str = "corpus-a",
    top_k: int = 5,
) -> RetrievalResult:
    return retrieval.retrieve(RetrievalQuery(corpus_id=corpus_id, question=question, top_k=top_k))


def then_passages_are(result: RetrievalResult, passage_ids: list[str]) -> None:
    assert [candidate.passage_id for candidate in result.candidates] == passage_ids


def test_given_matching_passage_when_retrieving_then_it_ranks_first() -> None:
    retrieval = given_retrieval_service(
        embeddings=[
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="irrelevant",
                ordinal=0,
                text="The release notes describe deployment windows.",
                vector=EmbeddingVector([0.0, 1.0]),
            ),
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="setup",
                ordinal=1,
                text="Setup requires installing dependencies before running checks.",
                vector=EmbeddingVector([1.0, 0.0]),
            ),
        ],
        query_vectors={"setup question": [1.0, 0.0]},
    )

    result = when_retrieving(retrieval, question="setup question", top_k=2)

    assert [(candidate.rank, candidate.passage_id) for candidate in result.candidates] == [
        (1, "setup"),
        (2, "irrelevant"),
    ]
    assert result.candidates[0].score == 1.0
    assert result.candidates[0].heading_path == ("Guide",)


def test_given_vectors_with_different_magnitudes_when_retrieving_then_cosine_ranks_them() -> None:
    retrieval = given_retrieval_service(
        embeddings=[
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="large-dot",
                ordinal=0,
                text="Large vector points partly away from the query.",
                vector=EmbeddingVector([10.0, 10.0]),
            ),
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="exact-direction",
                ordinal=1,
                text="Smaller vector has the same direction as the query.",
                vector=EmbeddingVector([1.0, 0.0]),
            ),
        ],
        query_vectors={"direction question": [1.0, 0.0]},
    )

    result = when_retrieving(retrieval, question="direction question", top_k=2)

    then_passages_are(result, ["exact-direction", "large-dot"])
    assert result.candidates[0].score == 1.0
    assert isclose(result.candidates[1].score, 0.70710678, rel_tol=1e-8)


def test_given_more_matches_than_top_k_when_retrieving_then_results_are_limited() -> None:
    retrieval = given_retrieval_service(
        embeddings=[
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="first",
                ordinal=0,
                text="Best match.",
                vector=EmbeddingVector([1.0, 0.0]),
            ),
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="second",
                ordinal=1,
                text="Second best match.",
                vector=EmbeddingVector([0.8, 0.6]),
            ),
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="third",
                ordinal=2,
                text="Lowest match.",
                vector=EmbeddingVector([0.0, 1.0]),
            ),
        ],
        query_vectors={"limit question": [1.0, 0.0]},
    )

    result = when_retrieving(retrieval, question="limit question", top_k=2)

    assert [(candidate.rank, candidate.passage_id) for candidate in result.candidates] == [
        (1, "first"),
        (2, "second"),
    ]


def test_given_equal_scores_when_retrieving_then_ties_are_stable() -> None:
    retrieval = given_retrieval_service(
        embeddings=[
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-b",
                passage_id="doc-b-second",
                ordinal=1,
                text="Same score in doc B.",
                vector=EmbeddingVector([1.0, 0.0]),
            ),
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="doc-a-second",
                ordinal=1,
                text="Same score in doc A, ordinal 1.",
                vector=EmbeddingVector([1.0, 0.0]),
            ),
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="doc-a-first",
                ordinal=0,
                text="Same score in doc A, ordinal 0.",
                vector=EmbeddingVector([1.0, 0.0]),
            ),
        ],
        query_vectors={"tie question": [1.0, 0.0]},
    )

    result = when_retrieving(retrieval, question="tie question", top_k=3)

    then_passages_are(result, ["doc-a-first", "doc-a-second", "doc-b-second"])


def test_given_multiple_corpora_when_retrieving_then_only_requested_corpus_is_visible() -> None:
    retrieval = given_retrieval_service(
        embeddings=[
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="a-only",
                ordinal=0,
                text="Visible only to corpus A.",
                vector=EmbeddingVector([1.0, 0.0]),
            ),
            given_passage_embedding(
                corpus_id="corpus-b",
                document_id="doc-b",
                passage_id="b-only",
                ordinal=0,
                text="Visible only to corpus B.",
                vector=EmbeddingVector([1.0, 0.0]),
            ),
        ],
        query_vectors={"scope question": [1.0, 0.0]},
    )

    result = when_retrieving(retrieval, question="scope question", top_k=5)

    assert [candidate.document_id for candidate in result.candidates] == ["doc-a"]


def test_given_embedding_record_when_retrieving_then_document_id_is_preserved() -> None:
    retrieval = given_retrieval_service(
        embeddings=[
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="missing-doc",
                passage_id="orphan",
                ordinal=0,
                text="This embedding has no active document.",
                vector=EmbeddingVector([1.0, 0.0]),
            ),
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="active",
                ordinal=1,
                text="This embedding belongs to the active corpus document.",
                vector=EmbeddingVector([0.0, 1.0]),
            ),
        ],
        query_vectors={"orphan question": [1.0, 0.0]},
    )

    result = when_retrieving(retrieval, question="orphan question", top_k=1)

    assert result.candidates[0].document_id == "missing-doc"


def test_given_passage_provenance_when_retrieving_then_result_preserves_it() -> None:
    retrieval = given_retrieval_service(
        embeddings=[
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="install-passage",
                section_id="install-section",
                ordinal=3,
                text="Run uv sync before verification.",
                heading_path=("Guide", "Install"),
                start_line=12,
                end_line=13,
                vector=EmbeddingVector([1.0, 0.0]),
            ),
        ],
        query_vectors={"provenance question": [1.0, 0.0]},
    )

    result = when_retrieving(retrieval, question="provenance question", top_k=1)

    assert result.candidates[0].document_id == "doc-a"
    assert result.candidates[0].section_id == "install-section"
    assert result.candidates[0].passage_id == "install-passage"
    assert result.candidates[0].heading_path == ("Guide", "Install")
    assert result.candidates[0].start_line == 12
    assert result.candidates[0].end_line == 13
    assert result.candidates[0].text == "Run uv sync before verification."


def test_given_padded_question_when_retrieving_then_embedding_uses_stripped_question() -> None:
    embeddings = InMemoryEmbeddingStore()
    embeddings.save_many(
        [
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="match",
                ordinal=0,
                text="Question normalization passage.",
                vector=EmbeddingVector([1.0, 0.0]),
            )
        ]
    )
    embedding_model = CapturingEmbeddingModel([1.0, 0.0])
    retrieval = RetrievalService(embeddings, embedding_model)

    result = when_retrieving(retrieval, question="  normalized question\n", top_k=1)

    assert embedding_model.requests == ["normalized question"]
    assert result.question == "normalized question"


def test_given_zero_vector_when_retrieving_then_score_is_zero() -> None:
    retrieval = given_retrieval_service(
        embeddings=[
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="zero",
                ordinal=0,
                text="Zero vector passage.",
                vector=EmbeddingVector([0.0, 0.0]),
            ),
        ],
        query_vectors={"zero question": [1.0, 0.0]},
    )

    result = when_retrieving(retrieval, question="zero question", top_k=1)

    assert result.candidates[0].score == 0.0


def test_given_mismatched_vector_dimensions_when_retrieving_then_it_fails() -> None:
    retrieval = given_retrieval_service(
        embeddings=[
            given_passage_embedding(
                corpus_id="corpus-a",
                document_id="doc-a",
                passage_id="wrong-dimensions",
                ordinal=0,
                text="Mismatched vector passage.",
                vector=EmbeddingVector([1.0, 0.0, 0.0]),
            ),
        ],
        query_vectors={"dimension question": [1.0, 0.0]},
    )

    with pytest.raises(ValueError, match="different dimensions"):
        when_retrieving(retrieval, question="dimension question", top_k=1)


def test_given_empty_corpus_when_retrieving_then_candidates_are_empty() -> None:
    retrieval = given_retrieval_service(
        embeddings=[],
        query_vectors={"missing question": [1.0, 0.0]},
    )

    result = when_retrieving(retrieval, corpus_id="empty", question=" missing question ")

    assert result.question == "missing question"
    assert result.candidates == ()
