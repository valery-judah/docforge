from __future__ import annotations

from dataclasses import dataclass

from doc_forge.retrieval import RetrievalQuery, RetrievalService, RetrievedPassage


@dataclass(frozen=True)
class AnswerQuery:
    corpus_id: str
    question: str


@dataclass(frozen=True)
class AnswerResult:
    corpus_id: str
    question: str
    answer: str | None
    source_passages: tuple[RetrievedPassage, ...]


class AnswerService:
    def __init__(self, retrieval_service: RetrievalService) -> None:
        self._retrieval_service = retrieval_service

    def answer(self, query: AnswerQuery) -> AnswerResult:
        retrieval = self._retrieval_service.retrieve(
            RetrievalQuery(
                corpus_id=query.corpus_id,
                question=query.question,
            )
        )
        top_passage = retrieval.candidates[0] if retrieval.candidates else None

        if top_passage is None or top_passage.score <= 0.0:
            return AnswerResult(
                corpus_id=retrieval.corpus_id,
                question=retrieval.question,
                answer=None,
                source_passages=(),
            )

        return AnswerResult(
            corpus_id=retrieval.corpus_id,
            question=retrieval.question,
            answer=top_passage.text,
            source_passages=(top_passage,),
        )
