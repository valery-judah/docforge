from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from doc_forge.app.dependencies import create_app_container, get_document_service
from doc_forge.app.settings import Settings
from doc_forge.documents import (
    DocumentNotFound,
    DocumentType,
    InvalidDocumentEncoding,
    UnsupportedDocumentType,
)
from doc_forge.processing.document_structure import DocumentPassageKind
from doc_forge.services import (
    DocumentInspection,
    DocumentService,
    DocumentSummary,
    IngestMarkdownDocumentCommand,
)

router = APIRouter()
STATIC_DIR = Path(__file__).parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = create_app_container(settings)
        try:
            yield
        finally:
            app.state.container = None

    app = FastAPI(title="DocForge", lifespan=lifespan)
    app.mount("/ui/static", StaticFiles(directory=STATIC_DIR), name="ui-static")
    app.include_router(router)
    return app


@router.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ok"}


class DocumentResponse(BaseModel):
    document_id: str
    corpus_id: str
    filename: str
    document_type: DocumentType


class PassageEmbeddingResponse(BaseModel):
    embedding_id: str
    ordinal: int
    vector_dimensions: int


class DocumentPassageInspectionResponse(BaseModel):
    passage_id: str
    kind: DocumentPassageKind
    ordinal: int
    text: str
    start_line: int
    end_line: int
    heading_path: tuple[str, ...]
    embedding: PassageEmbeddingResponse | None


class DocumentSectionInspectionResponse(BaseModel):
    section_id: str
    ordinal: int
    heading_level: int | None
    heading_title: str | None
    section_path: tuple[str, ...]
    start_line: int
    end_line: int
    token_count: int
    passages: tuple[DocumentPassageInspectionResponse, ...]


class DocumentInspectionResponse(BaseModel):
    document_id: str
    corpus_id: str
    filename: str
    document_type: DocumentType
    body: str
    sections: tuple[DocumentSectionInspectionResponse, ...]


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/ui")


@router.get("/ui", include_in_schema=False)
def web_ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@router.post(
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


@router.get(
    "/corpora/{corpus_id}/documents/{document_id}/inspection",
    response_model=DocumentInspectionResponse,
)
def inspect_document(
    corpus_id: str,
    document_id: str,
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentInspection:
    try:
        return document_service.inspect_document(
            corpus_id=corpus_id,
            document_id=document_id,
        )
    except DocumentNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in corpus.",
        ) from exc


@router.get("/corpora/{corpus_id}/documents", response_model=list[DocumentResponse])
def list_documents(
    corpus_id: str,
    document_service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[DocumentSummary]:
    return document_service.list_documents(corpus_id=corpus_id)


@router.get("/corpora/{corpus_id}/documents/{document_id}", response_model=DocumentResponse)
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
