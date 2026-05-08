from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request

from .contracts import AnswerSynthesisError

logger = logging.getLogger(__name__)


class OllamaSynthesisClient:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds

    def synthesize(self, prompt: str, *, question: str) -> str:
        started_at = time.monotonic()
        payload = json.dumps(
            {
                "model": self._model,
                "prompt": prompt,
                "think": False,
                "stream": False,
                "options": {
                    "temperature": 0,
                },
            }
        ).encode("utf-8")
        http_request = urllib.request.Request(
            url=f"{self._base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                raw_payload = response.read()
        except urllib.error.HTTPError as exc:
            detail = _read_error_detail(exc)
            logger.warning(
                "Ollama answer synthesis failed with HTTP %s: model=%s base_url=%s "
                "timeout_seconds=%.1f elapsed_seconds=%.2f question=%r detail=%s",
                exc.code,
                self._model,
                self._base_url,
                self._timeout_seconds,
                time.monotonic() - started_at,
                question,
                detail,
            )
            raise AnswerSynthesisError(
                f"ollama answer synthesis failed with HTTP {exc.code}: {detail}"
            ) from exc
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            logger.exception(
                "Ollama answer synthesis is unavailable: model=%s base_url=%s "
                "timeout_seconds=%.1f elapsed_seconds=%.2f question=%r",
                self._model,
                self._base_url,
                self._timeout_seconds,
                time.monotonic() - started_at,
                question,
            )
            raise AnswerSynthesisError("ollama answer synthesis is unavailable") from exc

        try:
            parsed_payload = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Ollama answer synthesis returned invalid JSON: model=%s base_url=%s "
                "question=%r payload_size_bytes=%d",
                self._model,
                self._base_url,
                question,
                len(raw_payload),
            )
            raise AnswerSynthesisError("ollama answer synthesis returned invalid JSON") from exc

        answer = parsed_payload.get("response")
        if not isinstance(answer, str):
            logger.warning(
                "Ollama answer synthesis response is missing text: model=%s base_url=%s "
                "question=%r response_keys=%s",
                self._model,
                self._base_url,
                question,
                sorted(parsed_payload.keys()),
            )
            raise AnswerSynthesisError("ollama answer synthesis response is missing text")

        normalized_answer = answer.strip()
        if not normalized_answer:
            logger.warning(
                "Ollama answer synthesis returned blank text: model=%s base_url=%s question=%r",
                self._model,
                self._base_url,
                question,
            )
            raise AnswerSynthesisError("ollama answer synthesis returned blank text")

        return normalized_answer


def _read_error_detail(error: urllib.error.HTTPError) -> str:
    payload_stream = getattr(error, "fp", None)
    if payload_stream is None:
        return "<empty error response>"

    payload = payload_stream.read()
    if not payload:
        return "<empty error response>"

    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return payload.decode("utf-8", errors="replace").strip() or "<empty error response>"

    detail = decoded.get("error")
    if isinstance(detail, str) and detail.strip():
        return detail
    return json.dumps(decoded, sort_keys=True)
