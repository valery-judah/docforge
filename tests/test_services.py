from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from doc_forge.documents import (
    DocumentNotFound,
    DocumentRecord,
    DocumentType,
)
from doc_forge.embedding.records import PassageEmbeddingRecord
from doc_forge.services import (
    DocumentService,
    DocumentSummary,
    IngestMarkdownDocumentCommand,
)


@dataclass
class RecordingDocumentRepository:
    saved_documents: list[DocumentRecord] = field(default_factory=list)

    def list_for_corpus(self, corpus_id: str) -> list[DocumentRecord]:
        return [document for document in self.saved_documents if document.corpus_id == corpus_id]

    def get(self, *, corpus_id: str, document_id: str) -> DocumentRecord:
        for document in reversed(self.saved_documents):
            if document.corpus_id == corpus_id and document.document_id == document_id:
                return document

        raise DocumentNotFound


@dataclass
class RecordingDocumentIngestionRepository:
    documents: RecordingDocumentRepository
    embeddings: RecordingEmbeddingRepository

    def save_document_with_embeddings(
        self,
        document: DocumentRecord,
        embeddings: list[PassageEmbeddingRecord],
    ) -> None:
        self.documents.saved_documents.append(document)
        self.embeddings.saved_embeddings.extend(embeddings)


@dataclass
class RecordingEmbeddingRepository:
    saved_embeddings: list[PassageEmbeddingRecord] = field(default_factory=list)

    def list_for_document(
        self,
        *,
        corpus_id: str,
        document_id: str,
    ) -> list[PassageEmbeddingRecord]:
        return [
            record
            for record in self.saved_embeddings
            if record.corpus_id == corpus_id and record.document_id == document_id
        ]


class RecordingEmbeddingModel:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(index), float(len(text))] for index, text in enumerate(texts)]


class FailingEmbeddingModel:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        _ = texts
        raise RuntimeError("embedding failed")


def _service_with(
    embedding_model: RecordingEmbeddingModel | FailingEmbeddingModel | None = None,
) -> tuple[DocumentService, RecordingDocumentRepository, RecordingEmbeddingRepository]:
    documents = RecordingDocumentRepository()
    embeddings = RecordingEmbeddingRepository()
    ingestion = RecordingDocumentIngestionRepository(documents, embeddings)
    service = DocumentService(
        documents,
        ingestion,
        embeddings,
        embedding_model or RecordingEmbeddingModel(),
    )
    return service, documents, embeddings


def test_document_service_synchronously_ingests_markdown_document() -> None:
    service, documents, ingestion = _service_with()

    document = service.ingest_markdown(
        IngestMarkdownDocumentCommand(
            corpus_id="corpus-a",
            filename="notes.md",
            raw_content=b"# Overview\n\nBody.",
        )
    )

    saved_document = documents.saved_documents[0]
    assert document == DocumentSummary(
        document_id=saved_document.document_id,
        corpus_id="corpus-a",
        filename="notes.md",
        document_type=DocumentType.MARKDOWN,
    )
    assert not hasattr(document, "body")
    assert not hasattr(document, "status")
    assert not hasattr(saved_document, "status")
    assert [record.text for record in ingestion.saved_embeddings] == ["Body."]
    assert ingestion.saved_embeddings[0].vector == (0.0, 5.0)


def test_document_service_preserves_heading_context_and_passage_order() -> None:
    service, _documents, ingestion = _service_with()

    service.ingest_markdown(
        IngestMarkdownDocumentCommand(
            corpus_id="corpus-a",
            filename="notes.md",
            raw_content=(
                b"# Guide\n\nOverview paragraph.\n\n## Details\n\n- first\n- second\n\nAfter list."
            ),
        )
    )

    assert [
        (record.ordinal, record.text, record.heading_path) for record in ingestion.saved_embeddings
    ] == [
        (0, "Overview paragraph.", ("Guide",)),
        (1, "- first\n- second", ("Guide", "Details")),
        (2, "After list.", ("Guide", "Details")),
    ]


def test_document_service_embedding_failure_does_not_persist_partial_ingestion() -> None:
    service, documents, ingestion = _service_with(FailingEmbeddingModel())

    with pytest.raises(RuntimeError, match="embedding failed"):
        service.ingest_markdown(
            IngestMarkdownDocumentCommand(
                corpus_id="corpus-a",
                filename="notes.md",
                raw_content=b"# Overview\n\nBody.",
            )
        )

    assert documents.saved_documents == []
    assert ingestion.saved_embeddings == []


def test_document_service_lists_documents_by_corpus() -> None:
    service, _documents, _ingestion = _service_with()
    corpus_document = service.ingest_markdown(
        IngestMarkdownDocumentCommand(
            corpus_id="corpus-a",
            filename="a.md",
            raw_content=b"# A",
        )
    )
    service.ingest_markdown(
        IngestMarkdownDocumentCommand(
            corpus_id="corpus-b",
            filename="b.md",
            raw_content=b"# B",
        )
    )

    assert service.list_documents(corpus_id="corpus-a") == [corpus_document]


def test_document_service_gets_document_by_corpus_and_id() -> None:
    service, _documents, _ingestion = _service_with()
    document = service.ingest_markdown(
        IngestMarkdownDocumentCommand(
            corpus_id="corpus-a",
            filename="notes.md",
            raw_content=b"# Overview",
        )
    )

    assert service.get_document(corpus_id="corpus-a", document_id=document.document_id) == document

    with pytest.raises(DocumentNotFound):
        service.get_document(corpus_id="corpus-b", document_id=document.document_id)


def test_document_service_inspects_processed_document_structure_and_embeddings() -> None:
    service, _documents, _embeddings = _service_with()
    document = service.ingest_markdown(
        IngestMarkdownDocumentCommand(
            corpus_id="corpus-a",
            filename="notes.md",
            raw_content=(
                b"# Guide\n\nIntro paragraph.\n\n## Setup\n\n- install\n- run\n\n```text\nok\n```"
            ),
        )
    )

    inspection = service.inspect_document(
        corpus_id="corpus-a",
        document_id=document.document_id,
    )

    assert inspection.document_id == document.document_id
    assert inspection.body.startswith("# Guide")
    assert [(section.heading_title, section.section_path) for section in inspection.sections] == [
        ("Guide", ("Guide",)),
        ("Setup", ("Guide", "Setup")),
    ]
    assert [
        (
            passage.kind,
            passage.text,
            passage.start_line,
            passage.end_line,
            passage.heading_path,
            passage.embedding.vector_dimensions if passage.embedding else None,
        )
        for section in inspection.sections
        for passage in section.passages
    ] == [
        ("paragraph", "Intro paragraph.", 3, 3, ("Guide",), 2),
        ("list", "- install\n- run", 7, 8, ("Guide", "Setup"), 2),
        ("code", "```text\nok\n```", 10, 12, ("Guide", "Setup"), 2),
    ]


def test_document_service_inspection_lookup_is_limited_to_corpus() -> None:
    service, _documents, _embeddings = _service_with()
    document = service.ingest_markdown(
        IngestMarkdownDocumentCommand(
            corpus_id="corpus-a",
            filename="notes.md",
            raw_content=b"# Overview\n\nBody.",
        )
    )

    with pytest.raises(DocumentNotFound):
        service.inspect_document(corpus_id="corpus-b", document_id=document.document_id)
