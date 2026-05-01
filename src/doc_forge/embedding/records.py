from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PassageEmbeddingRecord:
    embedding_id: str
    corpus_id: str
    document_id: str
    section_id: str
    passage_id: str
    ordinal: int
    text: str
    heading_path: tuple[str, ...]
    start_line: int
    end_line: int
    vector: tuple[float, ...]
