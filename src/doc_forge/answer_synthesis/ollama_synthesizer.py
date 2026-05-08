from __future__ import annotations

from .contracts import AnswerSynthesisRequest
from .ollama_client import OllamaSynthesisClient
from .prompting import build_synthesis_prompt


class OllamaAnswerSynthesizer:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float,
        client: OllamaSynthesisClient | None = None,
    ) -> None:
        self._client = client or OllamaSynthesisClient(
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )

    def synthesize_answer(self, request: AnswerSynthesisRequest) -> str:
        prompt = build_synthesis_prompt(request)
        return self._client.synthesize(prompt, question=request.question)
