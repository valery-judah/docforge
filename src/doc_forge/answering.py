from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from doc_forge.answer_synthesis import (
    AnswerEvidence,
    AnswerSynthesisRequest,
    AnswerSynthesizer,
)
from doc_forge.retrieval import RetrievalQuery, RetrievalService, RetrievedPassage


class AnswerState(StrEnum):
    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True)
class AnswerQuery:
    corpus_id: str
    question: str


@dataclass(frozen=True)
class AnswerResult:
    corpus_id: str
    question: str
    state: AnswerState
    answer: str | None
    source_passages: tuple[RetrievedPassage, ...]


class AnswerService:
    def __init__(
        self,
        retrieval_service: RetrievalService,
        answer_synthesizer: AnswerSynthesizer,
        *,
        top_k: int,
        min_score: float,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._answer_synthesizer = answer_synthesizer
        self._top_k = top_k
        self._min_score = min_score

    def answer(self, query: AnswerQuery) -> AnswerResult:
        retrieval = self._retrieval_service.retrieve(
            RetrievalQuery(
                corpus_id=query.corpus_id,
                question=query.question,
                top_k=self._top_k,
            )
        )
        source_passages = self._filter_source_passages(retrieval.candidates)

        if not source_passages:
            return AnswerResult(
                corpus_id=retrieval.corpus_id,
                question=retrieval.question,
                state=AnswerState.INSUFFICIENT_EVIDENCE,
                answer=None,
                source_passages=(),
            )

        answer = self._answer_synthesizer.synthesize_answer(
            AnswerSynthesisRequest(
                question=retrieval.question,
                evidence=tuple(
                    AnswerEvidence(
                        passage_id=passage.passage_id,
                        heading_path=passage.heading_path,
                        text=passage.text,
                    )
                    for passage in source_passages
                ),
            )
        )

        return AnswerResult(
            corpus_id=retrieval.corpus_id,
            question=retrieval.question,
            state=AnswerState.ANSWERED,
            answer=answer,
            source_passages=source_passages,
        )

    def _filter_source_passages(
        self,
        candidates: tuple[RetrievedPassage, ...],
    ) -> tuple[RetrievedPassage, ...]:
        return tuple(
            passage for passage in candidates[: self._top_k] if passage.score >= self._min_score
        )
