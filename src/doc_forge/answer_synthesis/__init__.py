from __future__ import annotations

from .contracts import (
    AnswerEvidence,
    AnswerSynthesisError,
    AnswerSynthesisRequest,
    AnswerSynthesizer,
)
from .ollama_synthesizer import OllamaAnswerSynthesizer


class DeterministicAnswerSynthesizer:
    def synthesize_answer(self, request: AnswerSynthesisRequest) -> str:
        top_evidence = request.evidence[0] if request.evidence else None
        if top_evidence is None:
            raise AnswerSynthesisError(
                "deterministic answer synthesizer requires at least one passage"
            )
        return top_evidence.text


__all__ = [
    "AnswerEvidence",
    "AnswerSynthesizer",
    "AnswerSynthesisError",
    "AnswerSynthesisRequest",
    "DeterministicAnswerSynthesizer",
    "OllamaAnswerSynthesizer",
]
