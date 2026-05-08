from __future__ import annotations

from doc_forge.answer_synthesis import (
    AnswerEvidence,
    AnswerSynthesisRequest,
)
from doc_forge.answering import AnswerQuery, AnswerResult, AnswerService, AnswerState
from doc_forge.retrieval import RetrievalQuery, RetrievalResult, RetrievedPassage


class StubRetrievalService:
    def __init__(self, result: RetrievalResult) -> None:
        self._result = result
        self.requests: list[RetrievalQuery] = []

    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        self.requests.append(query)
        return self._result


class StubAnswerSynthesizer:
    def __init__(
        self,
        result: str | None = None,
    ) -> None:
        self.result = result or "Generated answer."
        self.requests: list[AnswerSynthesisRequest] = []

    def synthesize_answer(self, request: AnswerSynthesisRequest) -> str:
        self.requests.append(request)
        return self.result


def given_passage(
    *,
    rank: int,
    score: float,
    passage_id: str,
    text: str,
) -> RetrievedPassage:
    return RetrievedPassage(
        rank=rank,
        score=score,
        document_id="doc-a",
        section_id=f"{passage_id}:section",
        passage_id=passage_id,
        heading_path=("Guide",),
        start_line=rank,
        end_line=rank,
        text=text,
    )


def given_retrieval_result(
    *,
    candidates: tuple[RetrievedPassage, ...],
    question: str = "normalized question",
) -> RetrievalResult:
    return RetrievalResult(
        corpus_id="corpus-a",
        question=question,
        candidates=candidates,
    )


def given_answer_service(
    result: RetrievalResult,
    *,
    synthesis_result: str | None = None,
    top_k: int = 3,
    min_score: float = 0.3,
) -> tuple[AnswerService, StubRetrievalService, StubAnswerSynthesizer]:
    retrieval = StubRetrievalService(result)
    synthesizer = StubAnswerSynthesizer(synthesis_result)
    return (
        AnswerService(
            retrieval,
            synthesizer,
            top_k=top_k,
            min_score=min_score,
        ),
        retrieval,
        synthesizer,
    )


def when_answering(
    service: AnswerService,
    *,
    question: str = "question",
) -> AnswerResult:
    return service.answer(AnswerQuery(corpus_id="corpus-a", question=question))


def test_given_positive_top_passages_when_answering_then_it_generates_from_top_k() -> None:
    top_passage = given_passage(
        rank=1,
        score=0.8,
        passage_id="best",
        text="Run uv sync before verification.",
    )
    second_passage = given_passage(rank=2, score=0.7, passage_id="next", text="Second.")
    third_passage = given_passage(rank=3, score=0.6, passage_id="third", text="Third.")
    fourth_passage = given_passage(rank=4, score=0.5, passage_id="extra", text="Fourth.")
    service, retrieval, synthesizer = given_answer_service(
        given_retrieval_result(
            candidates=(top_passage, second_passage, third_passage, fourth_passage)
        ),
    )

    result = when_answering(service)

    assert retrieval.requests == [
        RetrievalQuery(corpus_id="corpus-a", question="question", top_k=3)
    ]
    assert synthesizer.requests == [
        AnswerSynthesisRequest(
            question="normalized question",
            evidence=(
                AnswerEvidence(
                    passage_id="best",
                    heading_path=("Guide",),
                    text="Run uv sync before verification.",
                ),
                AnswerEvidence(
                    passage_id="next",
                    heading_path=("Guide",),
                    text="Second.",
                ),
                AnswerEvidence(
                    passage_id="third",
                    heading_path=("Guide",),
                    text="Third.",
                ),
            ),
        )
    ]
    assert result.state is AnswerState.ANSWERED
    assert result.answer == "Generated answer."
    assert result.source_passages == (top_passage, second_passage, third_passage)


def test_answering_uses_available_passages_when_fewer_than_top_k() -> None:
    top_passage = given_passage(rank=1, score=0.9, passage_id="best", text="Best answer.")
    second_passage = given_passage(rank=2, score=0.7, passage_id="second", text="Second answer.")
    service, _retrieval, synthesizer = given_answer_service(
        given_retrieval_result(candidates=(top_passage, second_passage))
    )

    result = when_answering(service)

    assert synthesizer.requests == [
        AnswerSynthesisRequest(
            question="normalized question",
            evidence=(
                AnswerEvidence(
                    passage_id="best",
                    heading_path=("Guide",),
                    text="Best answer.",
                ),
                AnswerEvidence(
                    passage_id="second",
                    heading_path=("Guide",),
                    text="Second answer.",
                ),
            ),
        )
    ]
    assert result.state is AnswerState.ANSWERED
    assert result.source_passages == (top_passage, second_passage)


def test_answering_filters_out_below_threshold_source_passages() -> None:
    top_passage = given_passage(rank=1, score=0.9, passage_id="best", text="Best answer.")
    second_passage = given_passage(rank=2, score=0.45, passage_id="second", text="Second answer.")
    weak_passage = given_passage(rank=3, score=0.2, passage_id="weak", text="Weak answer.")
    service, _retrieval, synthesizer = given_answer_service(
        given_retrieval_result(candidates=(top_passage, second_passage, weak_passage)),
        min_score=0.3,
    )

    result = when_answering(service)

    assert synthesizer.requests == [
        AnswerSynthesisRequest(
            question="normalized question",
            evidence=(
                AnswerEvidence(
                    passage_id="best",
                    heading_path=("Guide",),
                    text="Best answer.",
                ),
                AnswerEvidence(
                    passage_id="second",
                    heading_path=("Guide",),
                    text="Second answer.",
                ),
            ),
        )
    ]
    assert result.state is AnswerState.ANSWERED
    assert result.source_passages == (top_passage, second_passage)


def test_given_empty_retrieval_when_answering_then_it_returns_insufficient_evidence() -> None:
    service, _retrieval, synthesizer = given_answer_service(given_retrieval_result(candidates=()))

    result = when_answering(service)

    assert synthesizer.requests == []
    assert result.state is AnswerState.INSUFFICIENT_EVIDENCE
    assert result.answer is None
    assert result.source_passages == ()


def test_answering_abstains_when_top_passage_is_below_threshold() -> None:
    service, _retrieval, synthesizer = given_answer_service(
        given_retrieval_result(
            candidates=(given_passage(rank=1, score=0.19, passage_id="weak", text="Weak."),)
        )
    )

    result = when_answering(service)

    assert synthesizer.requests == []
    assert result.state is AnswerState.INSUFFICIENT_EVIDENCE
    assert result.answer is None
    assert result.source_passages == ()


def test_given_threshold_matching_top_passage_when_answering_then_it_generates_an_answer() -> None:
    top_passage = given_passage(rank=1, score=0.3, passage_id="supported", text="Support.")
    service, _retrieval, synthesizer = given_answer_service(
        given_retrieval_result(candidates=(top_passage,))
    )

    result = when_answering(service)

    assert synthesizer.requests == [
        AnswerSynthesisRequest(
            question="normalized question",
            evidence=(
                AnswerEvidence(
                    passage_id="supported",
                    heading_path=("Guide",),
                    text="Support.",
                ),
            ),
        )
    ]
    assert result.state is AnswerState.ANSWERED
    assert result.answer == "Generated answer."
    assert result.source_passages == (top_passage,)


def test_given_retrieval_normalized_question_when_answering_then_result_uses_it() -> None:
    service, retrieval, synthesizer = given_answer_service(
        given_retrieval_result(
            question="normalized question",
            candidates=(given_passage(rank=1, score=0.6, passage_id="best", text="Answer."),),
        )
    )

    result = when_answering(service, question="  normalized question  ")

    assert retrieval.requests == [
        RetrievalQuery(corpus_id="corpus-a", question="  normalized question  ", top_k=3)
    ]
    assert synthesizer.requests[0].question == "normalized question"
    assert result.question == "normalized question"
