from __future__ import annotations

from io import StringIO

import pytest

from doc_forge.devtools import demo_answer_smoke


def test_run_smoke_check_passes_when_responses_match_expectations(monkeypatch) -> None:
    responses = {
        demo_answer_smoke.DEMO_QUESTIONS[0].question: {
            "corpus_id": "default",
            "question": demo_answer_smoke.DEMO_QUESTIONS[0].question,
            "state": "answered",
            "answer": "The target is under 2.5 seconds.",
            "source_passages": [
                {"text": "The target is under 2.5 seconds median end-to-end latency."}
            ],
        },
        demo_answer_smoke.DEMO_QUESTIONS[1].question: {
            "corpus_id": "default",
            "question": demo_answer_smoke.DEMO_QUESTIONS[1].question,
            "state": "answered",
            "answer": "The maximum length for request_id is 128 characters.",
            "source_passages": [{"text": "Requirements:\n\n- maximum length: 128 characters."}],
        },
        demo_answer_smoke.DEMO_QUESTIONS[2].question: {
            "corpus_id": "default",
            "question": demo_answer_smoke.DEMO_QUESTIONS[2].question,
            "state": "insufficient_evidence",
            "answer": None,
            "source_passages": [],
        },
    }

    def fake_fetch_answer_response(
        *,
        base_url: str,
        corpus_id: str,
        question: str,
        timeout_seconds: float,
    ) -> dict[str, object]:
        assert base_url == "http://127.0.0.1:8000"
        assert corpus_id == "default"
        assert timeout_seconds == 120.0
        return responses[question]

    monkeypatch.setattr(demo_answer_smoke, "fetch_answer_response", fake_fetch_answer_response)

    output = StringIO()
    demo_answer_smoke.run_smoke_check(
        base_url="http://127.0.0.1:8000",
        corpus_id="default",
        timeout_seconds=120.0,
        output=output,
    )

    rendered = output.getvalue()
    assert "Running QA smoke check against http://127.0.0.1:8000/corpora/default" in rendered
    assert "[1/3] PASS answered:" in rendered
    assert "[2/3] PASS answered:" in rendered
    assert "[3/3] PASS insufficient_evidence:" in rendered
    assert "Smoke check passed: 3/3 questions." in rendered


def test_validate_answer_payload_fails_when_expected_evidence_is_missing() -> None:
    with pytest.raises(
        demo_answer_smoke.SmokeCheckError,
        match="No source passage contained expected evidence",
    ):
        demo_answer_smoke.validate_answer_payload(
            response_payload={
                "corpus_id": "default",
                "question": demo_answer_smoke.DEMO_QUESTIONS[0].question,
                "state": "answered",
                "answer": "The target is low latency.",
                "source_passages": [{"text": "Latency matters."}],
            },
            question=demo_answer_smoke.DEMO_QUESTIONS[0],
            corpus_id="default",
        )


def test_main_reports_live_503_with_ollama_hint(
    monkeypatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_smoke_check(
        *,
        base_url: str,
        corpus_id: str,
        timeout_seconds: float,
        output,
    ) -> None:
        raise demo_answer_smoke.SmokeCheckError(
            "Answer endpoint returned 503. Ensure Ollama is running and reachable from the API."
        )

    class FakeResolution:
        base_url = "http://127.0.0.1:8000"

    monkeypatch.setattr(
        demo_answer_smoke,
        "resolve_api_base_url",
        lambda **_: FakeResolution(),
    )
    monkeypatch.setattr(demo_answer_smoke, "run_smoke_check", fake_run_smoke_check)

    with pytest.raises(SystemExit) as exc_info:
        demo_answer_smoke.main([])

    assert exc_info.value.code == 1
    assert "Ensure Ollama is running and reachable from the API." in capsys.readouterr().err
