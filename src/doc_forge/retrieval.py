from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from doc_forge.embedding.contracts import EmbeddingModel
from doc_forge.embedding.records import PassageEmbeddingRecord
from doc_forge.embedding.vectors import EmbeddingVector
from doc_forge.ports import EmbeddingRepository


@dataclass(frozen=True)
class RetrievalQuery:
    corpus_id: str
    question: str
    top_k: int = 5


@dataclass(frozen=True)
class RetrievedPassage:
    rank: int
    score: float
    document_id: str
    section_id: str
    passage_id: str
    heading_path: tuple[str, ...]
    start_line: int
    end_line: int
    text: str

    @classmethod
    def from_embedding_record(
        cls,
        *,
        rank: int,
        score: float,
        record: PassageEmbeddingRecord,
    ) -> RetrievedPassage:
        return cls(
            rank=rank,
            score=score,
            document_id=record.document_id,
            section_id=record.section_id,
            passage_id=record.passage_id,
            heading_path=record.heading_path,
            start_line=record.start_line,
            end_line=record.end_line,
            text=record.text,
        )


@dataclass(frozen=True)
class RetrievalResult:
    corpus_id: str
    question: str
    candidates: tuple[RetrievedPassage, ...]


class RetrievalService:
    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
        embedding_model: EmbeddingModel,
    ) -> None:
        self._embedding_repository = embedding_repository
        self._embedding_model = embedding_model

    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        question = query.question.strip()
        query_vector = self._embedding_model.embed_text(question)
        ranked_records = sorted(
            (
                (_cosine_similarity(query_vector, record.vector), record)
                for record in self._embedding_repository.list_by_corpus(query.corpus_id)
            ),
            key=lambda scored_record: (
                -scored_record[0],
                scored_record[1].document_id,
                scored_record[1].ordinal,
            ),
        )

        candidates: list[RetrievedPassage] = []
        for rank, (score, record) in enumerate(ranked_records[: query.top_k], start=1):
            candidates.append(
                RetrievedPassage.from_embedding_record(
                    rank=rank,
                    score=score,
                    record=record,
                )
            )

        return RetrievalResult(
            corpus_id=query.corpus_id,
            question=question,
            candidates=tuple(candidates),
        )


def _cosine_similarity(left: EmbeddingVector, right: EmbeddingVector) -> float:
    if left.dimensions != right.dimensions:
        raise ValueError("cannot compare embedding vectors with different dimensions")

    numerator = sum(
        left_value * right_value for left_value, right_value in zip(left, right, strict=True)
    )
    left_magnitude = sqrt(sum(value * value for value in left))
    right_magnitude = sqrt(sum(value * value for value in right))
    if left_magnitude == 0.0 or right_magnitude == 0.0:
        return 0.0

    return numerator / (left_magnitude * right_magnitude)
