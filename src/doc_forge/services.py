from __future__ import annotations

from dataclasses import dataclass

from doc_forge.documents import (
    DocumentRecord,
    DocumentType,
    ingest_markdown_document,
)
from doc_forge.embeddings import PassageEmbeddingRecord
from doc_forge.ports import DocumentIngestionRepository, DocumentRepository, EmbeddingModel
from doc_forge.processing.document_structure import parse_document_structure


@dataclass(frozen=True)
class IngestMarkdownDocumentCommand:
    corpus_id: str
    filename: str | None
    raw_content: bytes


@dataclass(frozen=True)
class DocumentSummary:
    document_id: str
    corpus_id: str
    filename: str
    document_type: DocumentType


class DocumentService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        document_ingestion_repository: DocumentIngestionRepository,
        embedding_model: EmbeddingModel,
    ) -> None:
        self._document_repository = document_repository
        self._document_ingestion_repository = document_ingestion_repository
        self._embedding_model = embedding_model

    def ingest_markdown(
        self,
        command: IngestMarkdownDocumentCommand,
    ) -> DocumentSummary:
        document = ingest_markdown_document(
            corpus_id=command.corpus_id,
            filename=command.filename,
            raw_content=command.raw_content,
        )
        embeddings = _embedding_records_for(
            document=document,
            embedding_model=self._embedding_model,
        )
        self._document_ingestion_repository.save_document_with_embeddings(
            document,
            embeddings,
        )
        return _to_document_summary(document)

    def list_documents(self, *, corpus_id: str) -> list[DocumentSummary]:
        return [
            _to_document_summary(document)
            for document in self._document_repository.list_for_corpus(corpus_id)
        ]

    def get_document(self, *, corpus_id: str, document_id: str) -> DocumentSummary:
        return _to_document_summary(
            self._document_repository.get(corpus_id=corpus_id, document_id=document_id)
        )


def _to_document_summary(document: DocumentRecord) -> DocumentSummary:
    return DocumentSummary(
        document_id=document.document_id,
        corpus_id=document.corpus_id,
        filename=document.filename,
        document_type=document.document_type,
    )


def _embedding_records_for(
    *,
    document: DocumentRecord,
    embedding_model: EmbeddingModel,
) -> list[PassageEmbeddingRecord]:
    parsed_document = parse_document_structure(document)
    passages = [passage for section in parsed_document.sections for passage in section.passages]
    vectors = embedding_model.embed_texts([passage.text for passage in passages])
    if len(vectors) != len(passages):
        raise ValueError("embedding model returned an unexpected number of vectors")

    embedding_records: list[PassageEmbeddingRecord] = []
    for section in parsed_document.sections:
        for passage in section.passages:
            vector = vectors[len(embedding_records)]
            embedding_records.append(
                PassageEmbeddingRecord(
                    embedding_id=f"{passage.passage_id}:embedding:0",
                    corpus_id=parsed_document.corpus_id,
                    document_id=parsed_document.document_id,
                    section_id=section.section_id,
                    passage_id=passage.passage_id,
                    ordinal=len(embedding_records),
                    text=passage.text,
                    heading_path=section.section_path,
                    start_line=passage.start_line,
                    end_line=passage.end_line,
                    vector=tuple(vector),
                )
            )

    return embedding_records
