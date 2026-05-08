"""Run a live QA smoke check against the seeded demo corpus."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO, cast

from doc_forge.devtools.api_discovery import normalize_base_url, resolve_api_base_url

DEFAULT_CORPUS_ID = "default"
DEFAULT_HTTP_TIMEOUT_SECONDS = 120.0
DEFAULT_OLLAMA_MODEL = "qwen3.5:9b"
DEFAULT_DOCKER_OLLAMA_BASE_URL = "http://host.docker.internal:11434"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEV_SCRIPT = REPO_ROOT / "scripts" / "dev.sh"


@dataclass(frozen=True)
class SmokeQuestion:
    question: str
    expected_state: str
    expected_evidence_substring: str | None = None


DEMO_QUESTIONS = (
    SmokeQuestion(
        question=(
            "What is the interactive target for the full retrieval and answer generation path?"
        ),
        expected_state="answered",
        expected_evidence_substring="under 2.5 seconds",
    ),
    SmokeQuestion(
        question="What is the maximum length for request_id?",
        expected_state="answered",
        expected_evidence_substring="maximum length: 128 characters.",
    ),
    SmokeQuestion(
        question="What is the CEO approval policy for production incidents?",
        expected_state="insufficient_evidence",
    ),
)


class SmokeCheckError(RuntimeError):
    """Raised when the live smoke check cannot be completed successfully."""


def prepare_demo_runtime(prepare_mode: str, *, output: TextIO) -> None:
    if prepare_mode == "none":
        return

    try:
        subprocess.run(
            [str(DEV_SCRIPT), prepare_mode],
            cwd=REPO_ROOT,
            check=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - exercised through subprocess
        raise SmokeCheckError(
            f"Demo preparation failed while running `{DEV_SCRIPT} {prepare_mode}`."
        ) from exc

    print(f"Prepared demo runtime with `{DEV_SCRIPT} {prepare_mode}`.", file=output)


def fetch_answer_response(
    *,
    base_url: str,
    corpus_id: str,
    question: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    url = (
        f"{normalize_base_url(base_url)}/corpora/"
        f"{urllib.parse.quote(corpus_id, safe='')}/answers/query"
    )
    payload = json.dumps({"question": question}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = cast(bytes, response.read())
    except urllib.error.HTTPError as exc:
        detail = _read_error_detail(exc)
        if exc.code == 503:
            raise SmokeCheckError(
                "Answer endpoint returned 503. Ensure Ollama is running and "
                "reachable from the API. "
                f"Docker default expects {DEFAULT_DOCKER_OLLAMA_BASE_URL} with model "
                f"{DEFAULT_OLLAMA_MODEL}. Server detail: {detail}"
            ) from exc
        raise SmokeCheckError(
            f"Answer request failed with HTTP {exc.code} for question {question!r}. "
            f"Server detail: {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SmokeCheckError(
            f"Could not reach DocForge API at {base_url}. Ensure the demo stack is running."
        ) from exc

    return _decode_json_payload(body, context=f"answer response for question {question!r}")


def _read_error_detail(error: urllib.error.HTTPError) -> str:
    try:
        payload = error.read()
    except OSError:
        return "<unreadable error response>"

    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        text = payload.decode("utf-8", errors="replace").strip()
        return text or "<empty error response>"

    detail = decoded.get("detail")
    if isinstance(detail, str) and detail.strip():
        return detail
    return json.dumps(decoded, sort_keys=True)


def _decode_json_payload(payload: bytes, *, context: str) -> dict[str, Any]:
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SmokeCheckError(f"Received invalid JSON in {context}.") from exc

    if not isinstance(decoded, dict):
        raise SmokeCheckError(f"Expected an object in {context}.")
    return cast(dict[str, Any], decoded)


def validate_answer_payload(
    *,
    response_payload: dict[str, Any],
    question: SmokeQuestion,
    corpus_id: str,
) -> None:
    payload_corpus_id = response_payload.get("corpus_id")
    if payload_corpus_id != corpus_id:
        raise SmokeCheckError(
            f"Expected corpus_id {corpus_id!r} but received {payload_corpus_id!r}."
        )

    payload_question = response_payload.get("question")
    if payload_question != question.question:
        raise SmokeCheckError(
            f"Expected echoed question {question.question!r} but received {payload_question!r}."
        )

    payload_state = response_payload.get("state")
    if payload_state != question.expected_state:
        raise SmokeCheckError(
            f"Expected state {question.expected_state!r} but received {payload_state!r} "
            f"for question {question.question!r}."
        )

    source_passages = response_payload.get("source_passages")
    if not isinstance(source_passages, list):
        raise SmokeCheckError("Expected source_passages to be a JSON array.")
    source_passages_list = cast(list[object], source_passages)

    answer = response_payload.get("answer")
    if question.expected_state == "answered":
        _validate_answered_payload(
            answer=answer,
            source_passages=source_passages_list,
            evidence_substring=question.expected_evidence_substring,
            question_text=question.question,
        )
        return

    if answer is not None:
        raise SmokeCheckError(
            f"Expected a null answer for insufficient evidence on question {question.question!r}."
        )
    if source_passages_list:
        raise SmokeCheckError(
            "Expected no source passages for insufficient evidence on question "
            f"{question.question!r}."
        )


def _validate_answered_payload(
    *,
    answer: Any,
    source_passages: list[object],
    evidence_substring: str | None,
    question_text: str,
) -> None:
    if not isinstance(answer, str) or not answer.strip():
        raise SmokeCheckError(f"Expected a non-empty answer for question {question_text!r}.")
    if not source_passages:
        raise SmokeCheckError(
            f"Expected at least one source passage for question {question_text!r}."
        )
    if evidence_substring is None:
        return

    for passage in source_passages:
        if not isinstance(passage, dict):
            raise SmokeCheckError(
                f"Expected source passage objects for question {question_text!r}."
            )
        passage_dict = cast(dict[str, object], passage)
        text = passage_dict.get("text")
        if isinstance(text, str) and evidence_substring in text:
            return

    raise SmokeCheckError(
        f"No source passage contained expected evidence {evidence_substring!r} "
        f"for question {question_text!r}."
    )


def run_smoke_check(
    *,
    base_url: str,
    corpus_id: str,
    timeout_seconds: float,
    output: TextIO,
) -> None:
    normalized_base_url = normalize_base_url(base_url)
    print(f"Running QA smoke check against {normalized_base_url}/corpora/{corpus_id}", file=output)

    for index, question in enumerate(DEMO_QUESTIONS, start=1):
        response_payload = fetch_answer_response(
            base_url=normalized_base_url,
            corpus_id=corpus_id,
            question=question.question,
            timeout_seconds=timeout_seconds,
        )
        validate_answer_payload(
            response_payload=response_payload,
            question=question,
            corpus_id=corpus_id,
        )
        print(
            f"[{index}/{len(DEMO_QUESTIONS)}] PASS {question.expected_state}: {question.question}",
            file=output,
        )

    print(
        f"Smoke check passed: {len(DEMO_QUESTIONS)}/{len(DEMO_QUESTIONS)} questions.",
        file=output,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m doc_forge.devtools.demo_answer_smoke")
    parser.add_argument(
        "--api-base-url",
        help="Override the DocForge API base URL instead of using discovery.",
    )
    parser.add_argument(
        "--corpus-id",
        default=DEFAULT_CORPUS_ID,
        help=f"Corpus to query. Default: {DEFAULT_CORPUS_ID}",
    )
    parser.add_argument(
        "--prepare-demo",
        choices=("none", "seed-demo", "up-demo"),
        default="none",
        help="Optionally start or reseed the existing demo runtime before running checks.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_HTTP_TIMEOUT_SECONDS,
        help=(
            f"HTTP timeout in seconds for answer requests. Default: {DEFAULT_HTTP_TIMEOUT_SECONDS}"
        ),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        prepare_demo_runtime(args.prepare_demo, output=sys.stdout)
        if args.api_base_url:
            base_url = normalize_base_url(args.api_base_url)
        else:
            base_url = resolve_api_base_url(timeout_seconds=1.0).base_url
        run_smoke_check(
            base_url=base_url,
            corpus_id=args.corpus_id,
            timeout_seconds=args.timeout,
            output=sys.stdout,
        )
    except (RuntimeError, ValueError, SmokeCheckError) as exc:
        parser.exit(1, f"{exc}\n")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
