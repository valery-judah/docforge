from __future__ import annotations

from doc_forge.answering import AnswerQuery, AnswerResult, AnswerService
from doc_forge.retrieval import RetrievalQuery, RetrievalResult, RetrievedPassage


class StubRetrievalService:
    def __init__(self, result: RetrievalResult) -> None:
        self._result = result
        self.requests: list[RetrievalQuery] = []

    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        self.requests.append(query)
        return self._result


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


def given_answer_service(result: RetrievalResult) -> tuple[AnswerService, StubRetrievalService]:
    retrieval = StubRetrievalService(result)
    return AnswerService(retrieval), retrieval


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


def when_answering(
    service: AnswerService,
    *,
    question: str = "question",
) -> AnswerResult:
    return service.answer(AnswerQuery(corpus_id="corpus-a", question=question))


def test_given_positive_top_passage_when_answering_then_it_answers_from_that_passage() -> None:
    top_passage = given_passage(
        rank=1,
        score=0.8,
        passage_id="best",
        text="Run uv sync before verification.",
    )
    service, _retrieval = given_answer_service(given_retrieval_result(candidates=(top_passage,)))

    result = when_answering(service)

    assert result.answer == "Run uv sync before verification."
    assert result.source_passages == (top_passage,)


def test_given_multiple_positive_passages_when_answering_then_it_uses_only_top_passage() -> None:
    top_passage = given_passage(rank=1, score=0.9, passage_id="best", text="Best answer.")
    second_passage = given_passage(
        rank=2,
        score=0.7,
        passage_id="second",
        text="Second answer.",
    )
    service, _retrieval = given_answer_service(
        given_retrieval_result(candidates=(top_passage, second_passage))
    )

    result = when_answering(service)

    assert result.answer == "Best answer."
    assert result.source_passages == (top_passage,)


def test_given_empty_retrieval_when_answering_then_it_returns_no_answer() -> None:
    service, _retrieval = given_answer_service(given_retrieval_result(candidates=()))

    result = when_answering(service)

    assert result.answer is None
    assert result.source_passages == ()


def test_given_zero_score_passage_when_answering_then_it_returns_no_answer() -> None:
    service, _retrieval = given_answer_service(
        given_retrieval_result(
            candidates=(given_passage(rank=1, score=0.0, passage_id="weak", text="Weak."),)
        )
    )

    result = when_answering(service)

    assert result.answer is None
    assert result.source_passages == ()


def test_given_negative_score_passage_when_answering_then_it_returns_no_answer() -> None:
    service, _retrieval = given_answer_service(
        given_retrieval_result(
            candidates=(given_passage(rank=1, score=-0.5, passage_id="opposite", text="Opposite."),)
        )
    )

    result = when_answering(service)

    assert result.answer is None
    assert result.source_passages == ()


def test_given_retrieval_normalized_question_when_answering_then_result_uses_it() -> None:
    service, retrieval = given_answer_service(
        given_retrieval_result(
            question="normalized question",
            candidates=(given_passage(rank=1, score=0.6, passage_id="best", text="Answer."),),
        )
    )

    result = when_answering(service, question="  normalized question  ")

    assert retrieval.requests == [
        RetrievalQuery(corpus_id="corpus-a", question="  normalized question  ")
    ]
    assert result.question == "normalized question"
