from __future__ import annotations

import io
import json
import logging
import urllib.error

import pytest

from doc_forge.answer_synthesis import (
    AnswerEvidence,
    AnswerSynthesisError,
    AnswerSynthesisRequest,
    DeterministicAnswerSynthesizer,
    OllamaAnswerSynthesizer,
)


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        _ = exc_type, exc, traceback
        return None

    def read(self) -> bytes:
        return self._payload


def given_request() -> AnswerSynthesisRequest:
    return AnswerSynthesisRequest(
        question="What is the answer path?",
        evidence=(
            AnswerEvidence(
                passage_id="passage-a",
                heading_path=("Answering",),
                text="The answer path uses retrieved evidence.",
            ),
        ),
    )


def test_deterministic_answer_synthesizer_returns_answer_text() -> None:
    synthesizer = DeterministicAnswerSynthesizer()

    assert (
        synthesizer.synthesize_answer(given_request()) == "The answer path uses retrieved evidence."
    )


def test_deterministic_answer_synthesizer_requires_passages() -> None:
    synthesizer = DeterministicAnswerSynthesizer()

    with pytest.raises(AnswerSynthesisError, match="requires at least one passage"):
        synthesizer.synthesize_answer(AnswerSynthesisRequest(question="Q", evidence=()))


def test_ollama_answer_synthesizer_posts_expected_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_urlopen(request, *, timeout: float):  # type: ignore[no-untyped-def]
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        seen["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(b'{"response":"  Grounded answer.  "}')

    monkeypatch.setattr(
        "doc_forge.answer_synthesis.ollama_client.urllib.request.urlopen", fake_urlopen
    )
    synthesizer = OllamaAnswerSynthesizer(
        base_url="http://ollama.local:11434/",
        model="qwen3.5:9b",
        timeout_seconds=12.5,
    )

    answer = synthesizer.synthesize_answer(given_request())

    assert answer == "Grounded answer."
    assert seen["url"] == "http://ollama.local:11434/api/generate"
    assert seen["timeout"] == 12.5
    assert seen["payload"] == {
        "model": "qwen3.5:9b",
        "prompt": (
            "Answer the question using only the provided evidence.\n"
            "If the evidence does not support the answer, do not invent facts.\n"
            "Return plain text only, with no markdown fences or extra commentary.\n\n"
            "Question:\nWhat is the answer path?\n\n"
            "Evidence:\n[Passage 1]\n"
            "Heading Path: Answering\n"
            "Text: The answer path uses retrieved evidence."
        ),
        "think": False,
        "stream": False,
        "options": {"temperature": 0},
    }


def test_ollama_answer_synthesizer_raises_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fake_urlopen(request, *, timeout: float):  # type: ignore[no-untyped-def]
        _ = request, timeout
        raise urllib.error.HTTPError(
            url="http://ollama.local:11434/api/generate",
            code=503,
            msg="unavailable",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"model overloaded"}'),
        )

    monkeypatch.setattr(
        "doc_forge.answer_synthesis.ollama_client.urllib.request.urlopen", fake_urlopen
    )
    synthesizer = OllamaAnswerSynthesizer(
        base_url="http://ollama.local:11434",
        model="qwen3.5:9b",
        timeout_seconds=12.5,
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(AnswerSynthesisError, match="HTTP 503: model overloaded"):
            synthesizer.synthesize_answer(given_request())

    assert "Ollama answer synthesis failed with HTTP 503" in caplog.text
    assert "model overloaded" in caplog.text
    assert "qwen3.5:9b" in caplog.text


def test_ollama_answer_synthesizer_parses_plain_text_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request, *, timeout: float):  # type: ignore[no-untyped-def]
        _ = request, timeout
        return _FakeResponse(b'{"response":"Answer from retrieved evidence."}')

    monkeypatch.setattr(
        "doc_forge.answer_synthesis.ollama_client.urllib.request.urlopen", fake_urlopen
    )
    synthesizer = OllamaAnswerSynthesizer(
        base_url="http://ollama.local:11434",
        model="qwen3.5:9b",
        timeout_seconds=12.5,
    )

    assert synthesizer.synthesize_answer(given_request()) == "Answer from retrieved evidence."


def test_ollama_answer_synthesizer_raises_on_invalid_or_blank_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = iter(
        (
            b"{bad json",
            b'{"response":"   "}',
            b'{"response":null}',
        )
    )

    def fake_urlopen(request, *, timeout: float):  # type: ignore[no-untyped-def]
        _ = request, timeout
        return _FakeResponse(next(payloads))

    monkeypatch.setattr(
        "doc_forge.answer_synthesis.ollama_client.urllib.request.urlopen", fake_urlopen
    )
    synthesizer = OllamaAnswerSynthesizer(
        base_url="http://ollama.local:11434",
        model="qwen3.5:9b",
        timeout_seconds=12.5,
    )

    with pytest.raises(AnswerSynthesisError, match="invalid JSON"):
        synthesizer.synthesize_answer(given_request())
    with pytest.raises(AnswerSynthesisError, match="blank text"):
        synthesizer.synthesize_answer(given_request())
    with pytest.raises(AnswerSynthesisError, match="missing text"):
        synthesizer.synthesize_answer(given_request())
