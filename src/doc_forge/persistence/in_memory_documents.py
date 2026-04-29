from __future__ import annotations

from doc_forge.documents import DocumentNotFound, DocumentRecord


class InMemoryDocumentStore:
    def __init__(self) -> None:
        self._documents_by_corpus: dict[str, dict[str, DocumentRecord]] = {}

    def save(self, document: DocumentRecord) -> None:
        corpus_documents = self._documents_by_corpus.setdefault(document.corpus_id, {})
        corpus_documents[document.document_id] = document

    def list_for_corpus(self, corpus_id: str) -> list[DocumentRecord]:
        return list(self._documents_by_corpus.get(corpus_id, {}).values())

    def get(self, *, corpus_id: str, document_id: str) -> DocumentRecord:
        document = self._documents_by_corpus.get(corpus_id, {}).get(document_id)
        if document is None:
            raise DocumentNotFound

        return document
