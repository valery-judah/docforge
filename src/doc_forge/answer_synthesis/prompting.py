from __future__ import annotations

from .contracts import AnswerEvidence, AnswerSynthesisRequest


def build_synthesis_prompt(request: AnswerSynthesisRequest) -> str:
    evidence_blocks = "\n\n".join(
        _format_evidence(index=index, evidence=evidence)
        for index, evidence in enumerate(request.evidence, start=1)
    )
    return (
        "Answer the question using only the provided evidence.\n"
        "If the evidence does not support the answer, do not invent facts.\n"
        "Return plain text only, with no markdown fences or extra commentary.\n\n"
        f"Question:\n{request.question}\n\n"
        f"Evidence:\n{evidence_blocks}"
    )


def _format_evidence(*, index: int, evidence: AnswerEvidence) -> str:
    heading_path = " > ".join(evidence.heading_path) if evidence.heading_path else "(root)"
    return f"[Passage {index}]\nHeading Path: {heading_path}\nText: {evidence.text}"
