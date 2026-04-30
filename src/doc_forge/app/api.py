from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from doc_forge.app.dependencies import get_document_service
from doc_forge.documents import (
    DocumentNotFound,
    DocumentType,
    InvalidDocumentEncoding,
    UnsupportedDocumentType,
)
from doc_forge.services import (
    DocumentService,
    DocumentSummary,
    IngestMarkdownDocumentCommand,
)

app = FastAPI(title="DocForge")


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ok"}


class DocumentResponse(BaseModel):
    document_id: str
    corpus_id: str
    filename: str
    document_type: DocumentType


@app.post(
    "/corpora/{corpus_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_markdown_document(
    corpus_id: str,
    file: Annotated[UploadFile, File()],
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentSummary:
    raw_content = await file.read()

    try:
        document = document_service.ingest_markdown(
            IngestMarkdownDocumentCommand(
                corpus_id=corpus_id,
                filename=file.filename,
                raw_content=raw_content,
            )
        )
    except UnsupportedDocumentType as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only Markdown files with .md or .markdown extensions are supported.",
        ) from exc
    except InvalidDocumentEncoding as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Markdown documents must be UTF-8 encoded.",
        ) from exc

    return document


@app.get("/corpora/{corpus_id}/documents", response_model=list[DocumentResponse])
def list_documents(
    corpus_id: str,
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[DocumentSummary]:
    return document_service.list_documents(corpus_id=corpus_id)


@app.get("/corpora/{corpus_id}/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    corpus_id: str,
    document_id: str,
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentSummary:
    try:
        document = document_service.get_document(
            corpus_id=corpus_id,
            document_id=document_id,
        )
    except DocumentNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in corpus.",
        ) from exc

    return document
