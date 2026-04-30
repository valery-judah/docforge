from __future__ import annotations

from doc_forge.embeddings import PassageEmbeddingRecord


class InMemoryEmbeddingStore:
    def __init__(self) -> None:
        self._records_by_corpus: dict[str, dict[str, PassageEmbeddingRecord]] = {}

    def save_many(self, records: list[PassageEmbeddingRecord]) -> None:
        for record in records:
            corpus_records = self._records_by_corpus.setdefault(record.corpus_id, {})
            corpus_records[record.embedding_id] = record

    def list_for_corpus(self, corpus_id: str) -> list[PassageEmbeddingRecord]:
        return list(self._records_by_corpus.get(corpus_id, {}).values())

    def snapshot(self) -> dict[str, dict[str, PassageEmbeddingRecord]]:
        return {corpus_id: dict(records) for corpus_id, records in self._records_by_corpus.items()}

    def restore(self, snapshot: dict[str, dict[str, PassageEmbeddingRecord]]) -> None:
        self._records_by_corpus = {
            corpus_id: dict(records) for corpus_id, records in snapshot.items()
        }
