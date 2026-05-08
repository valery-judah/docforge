from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class AnswerEvidence:
    passage_id: str
    heading_path: tuple[str, ...]
    text: str


@dataclass(frozen=True)
class AnswerSynthesisRequest:
    question: str
    evidence: tuple[AnswerEvidence, ...]


class AnswerSynthesisError(RuntimeError):
    """Raised when the configured answer synthesizer cannot produce an answer."""


@runtime_checkable
class AnswerSynthesizer(Protocol):
    def synthesize_answer(self, request: AnswerSynthesisRequest) -> str: ...
