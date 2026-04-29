from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256


class DocumentStatus(StrEnum):
    READY = "ready"


class DocumentType(StrEnum):
    MARKDOWN = "markdown"


class DocumentError(Exception):
    """Base error for document domain failures."""


class UnsupportedDocumentType(DocumentError):
    pass


class InvalidDocumentEncoding(DocumentError):
    pass


class DocumentNotFound(DocumentError):
    pass


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    corpus_id: str
    filename: str
    status: DocumentStatus
    document_type: DocumentType
    body: str


def ingest_markdown_document(
    *,
    corpus_id: str,
    filename: str | None,
    raw_content: bytes,
) -> DocumentRecord:
    if filename is None or not _is_supported_markdown_file(filename):
        raise UnsupportedDocumentType

    body = _decode_markdown(raw_content)
    return DocumentRecord(
        document_id=_document_id_for(
            corpus_id=corpus_id,
            filename=filename,
            raw_content=raw_content,
        ),
        corpus_id=corpus_id,
        filename=filename,
        status=DocumentStatus.READY,
        document_type=DocumentType.MARKDOWN,
        body=body,
    )


def _is_supported_markdown_file(filename: str) -> bool:
    normalized_filename = filename.lower()
    return normalized_filename.endswith((".md", ".markdown"))


def _decode_markdown(raw_content: bytes) -> str:
    try:
        return raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidDocumentEncoding from exc


def _document_id_for(*, corpus_id: str, filename: str, raw_content: bytes) -> str:
    digest = sha256()
    digest.update(corpus_id.encode("utf-8"))
    digest.update(b"\0")
    digest.update(filename.encode("utf-8"))
    digest.update(b"\0")
    digest.update(raw_content)
    return digest.hexdigest()[:24]
