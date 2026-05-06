from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from doc_forge import __version__
from doc_forge.answering import AnswerService
from doc_forge.app import dependencies
from doc_forge.app.api import create_app, readyz
from doc_forge.app.dependencies import (
    get_answer_service,
    get_document_service,
    get_retrieval_service,
)
from doc_forge.app.settings import Settings
from doc_forge.embedding.deterministic import DeterministicEmbeddingModel
from doc_forge.embedding.vectors import EmbeddingBatch, EmbeddingVector
from doc_forge.persistence.in_memory_documents import InMemoryDocumentStore
from doc_forge.persistence.in_memory_embeddings import InMemoryEmbeddingStore
from doc_forge.persistence.in_memory_ingestion import InMemoryDocumentIngestionRepository
from doc_forge.retrieval import RetrievalService
from doc_forge.services import DocumentService


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(Settings(embedding_model="deterministic", _env_file=None))
    documents = InMemoryDocumentStore()
    embeddings = InMemoryEmbeddingStore()
    ingestion = InMemoryDocumentIngestionRepository(
        documents=documents,
        embeddings=embeddings,
    )
    embedding_model = DeterministicEmbeddingModel()
    document_service = DocumentService(documents, ingestion, embeddings, embedding_model)
    retrieval_service = RetrievalService(embeddings, embedding_model)
    answer_service = AnswerService(retrieval_service)
    app.dependency_overrides[get_document_service] = lambda: document_service
    app.dependency_overrides[get_retrieval_service] = lambda: retrieval_service
    app.dependency_overrides[get_answer_service] = lambda: answer_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_package_imports() -> None:
    assert __version__ == "0.1.0"


def test_readyz_payload() -> None:
    assert readyz() == {"status": "ok"}


def test_root_redirects_to_web_ui(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "DocForge" in response.text


def test_web_ui_is_served(client: TestClient) -> None:
    response = client.get("/ui")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DocForge" in response.text


def test_web_ui_static_asset_is_served(client: TestClient) -> None:
    response = client.get("/ui/static/app.js")

    assert response.status_code == 200
    assert "loadDocuments" in response.text


def test_create_app_defers_runtime_validation_until_lifespan(tmp_path: Path) -> None:
    occupied_cache_path = tmp_path / "occupied-cache-path"
    occupied_cache_path.write_text("not a directory", encoding="utf-8")
    app = create_app(
        Settings(
            embedding_model="transformer",
            hf_home=occupied_cache_path,
            _env_file=None,
        )
    )

    with pytest.raises(RuntimeError, match="Set DOC_FORGE_HF_HOME to a writable directory"):
        with TestClient(app):
            pass


def test_lifespan_created_service_handles_documents() -> None:
    app = create_app(Settings(embedding_model="deterministic", _env_file=None))

    with TestClient(app) as client:
        upload_response = client.post(
            "/corpora/lifespan/documents",
            files={"file": ("notes.md", b"# Runtime\n\nConfigured.", "text/markdown")},
        )
        document_id = upload_response.json()["document_id"]

        response = client.get(f"/corpora/lifespan/documents/{document_id}")

    assert upload_response.status_code == 201
    assert response.status_code == 200
    assert response.json()["document_id"] == document_id


def test_default_embedding_model_uses_transformer_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_transformer_models = 0

    class FakeTransformerEmbeddingModel:
        def __init__(self) -> None:
            nonlocal created_transformer_models
            created_transformer_models += 1

        def embed_text(self, text: str) -> EmbeddingVector:
            _ = text
            return EmbeddingVector([0.0])

        def embed_texts(self, texts: list[str]) -> EmbeddingBatch:
            return EmbeddingBatch(EmbeddingVector([0.0]) for _text in texts)

    monkeypatch.setattr(
        dependencies,
        "SentenceTransformerEmbeddingModel",
        FakeTransformerEmbeddingModel,
    )

    model = dependencies._create_embedding_model(Settings(_env_file=None))

    assert isinstance(model, FakeTransformerEmbeddingModel)
    assert created_transformer_models == 1


def test_upload_markdown_document(client: TestClient) -> None:
    response = client.post(
        "/corpora/product-notes/documents",
        files={
            "file": (
                "notes.md",
                b"# Overview\n\nBody text.\n\n## Details\n\nMore body text.",
                "text/markdown",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["corpus_id"] == "product-notes"
    assert payload["filename"] == "notes.md"
    assert payload["document_type"] == "markdown"
    assert "status" not in payload
    assert "content_type" not in payload
    assert "heading_paths" not in payload
    assert "body" not in payload
    assert len(payload["document_id"]) == 24


def test_markdown_document_can_be_read_from_its_corpus(client: TestClient) -> None:
    upload_response = client.post(
        "/corpora/research/documents",
        files={"file": ("paper.markdown", b"# Findings\n\nEvidence.", "text/markdown")},
    )
    document_id = upload_response.json()["document_id"]

    response = client.get(f"/corpora/research/documents/{document_id}")

    assert response.status_code == 200
    assert response.json()["document_id"] == document_id


def test_markdown_document_inspection_returns_structure_and_embedding_metadata(
    client: TestClient,
) -> None:
    upload_response = client.post(
        "/corpora/research/documents",
        files={
            "file": (
                "paper.markdown",
                b"# Findings\n\nEvidence.\n\n## Setup\n\n- install\n- run",
                "text/markdown",
            )
        },
    )
    document_id = upload_response.json()["document_id"]

    response = client.get(f"/corpora/research/documents/{document_id}/inspection")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["body"].startswith("# Findings")
    assert [
        (section["heading_title"], section["section_path"]) for section in payload["sections"]
    ] == [
        ("Findings", ["Findings"]),
        ("Setup", ["Findings", "Setup"]),
    ]
    assert [
        (
            passage["kind"],
            passage["text"],
            passage["start_line"],
            passage["end_line"],
            passage["embedding"]["vector_dimensions"],
        )
        for section in payload["sections"]
        for passage in section["passages"]
    ] == [
        ("paragraph", "Evidence.", 3, 3, 8),
        ("list", "- install\n- run", 7, 8, 8),
    ]


def test_document_lookup_is_limited_to_corpus(client: TestClient) -> None:
    upload_response = client.post(
        "/corpora/corpus-a/documents",
        files={"file": ("brief.md", b"# Corpus\n\nA-only.", "text/markdown")},
    )
    document_id = upload_response.json()["document_id"]

    response = client.get(f"/corpora/corpus-b/documents/{document_id}")

    assert response.status_code == 404

    inspection_response = client.get(f"/corpora/corpus-b/documents/{document_id}/inspection")

    assert inspection_response.status_code == 404


def test_retrieval_query_returns_ranked_markdown_passages(client: TestClient) -> None:
    upload_response = client.post(
        "/corpora/research/documents",
        files={
            "file": (
                "retrieval.md",
                b"# Retrieval\n\nThe retrieval pipeline ranks Markdown passages.",
                "text/markdown",
            )
        },
    )
    document_id = upload_response.json()["document_id"]

    response = client.post(
        "/corpora/research/retrieval/query",
        json={"question": "How does the retrieval pipeline work?", "top_k": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["corpus_id"] == "research"
    assert payload["question"] == "How does the retrieval pipeline work?"
    assert set(payload["candidates"][0]) == {
        "rank",
        "score",
        "document_id",
        "section_id",
        "passage_id",
        "heading_path",
        "start_line",
        "end_line",
        "text",
    }
    assert [
        (
            candidate["rank"],
            candidate["document_id"],
            candidate["section_id"],
            candidate["passage_id"],
            candidate["heading_path"],
            candidate["start_line"],
            candidate["end_line"],
            candidate["text"],
        )
        for candidate in payload["candidates"]
    ] == [
        (
            1,
            document_id,
            f"{document_id}:section:0",
            f"{document_id}:section:0:passage:0",
            ["Retrieval"],
            3,
            3,
            "The retrieval pipeline ranks Markdown passages.",
        )
    ]
    assert isinstance(payload["candidates"][0]["score"], float)


def test_retrieval_query_openapi_uses_passage_naming(client: TestClient) -> None:
    payload = client.get("/openapi.json").json()

    operation = payload["paths"]["/corpora/{corpus_id}/retrieval/query"]["post"]
    response_schema = payload["components"]["schemas"]["RetrievalQueryResponse"]

    assert "passages" in operation["operationId"]
    assert "evidence" not in operation["operationId"].lower()
    assert (
        response_schema["properties"]["candidates"]["items"]["$ref"]
        == "#/components/schemas/RetrievedPassageResponse"
    )


def test_retrieval_query_uses_default_top_k_and_normalizes_question(
    client: TestClient,
) -> None:
    upload_response = client.post(
        "/corpora/research/documents",
        files={
            "file": (
                "many.md",
                (
                    b"# Many\n\n"
                    b"Passage one.\n\n"
                    b"Passage two.\n\n"
                    b"Passage three.\n\n"
                    b"Passage four.\n\n"
                    b"Passage five.\n\n"
                    b"Passage six."
                ),
                "text/markdown",
            )
        },
    )
    assert upload_response.status_code == 201

    response = client.post(
        "/corpora/research/retrieval/query",
        json={"question": "  passages  "},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "passages"
    assert len(payload["candidates"]) == 5
    assert [candidate["rank"] for candidate in payload["candidates"]] == [1, 2, 3, 4, 5]


def test_retrieval_query_returns_empty_candidates_for_empty_corpus(client: TestClient) -> None:
    response = client.post(
        "/corpora/empty/retrieval/query",
        json={"question": "anything", "top_k": 5},
    )

    assert response.status_code == 200
    assert response.json()["candidates"] == []


def test_retrieval_query_validates_question_and_top_k(client: TestClient) -> None:
    blank_question_response = client.post(
        "/corpora/research/retrieval/query",
        json={"question": "   ", "top_k": 5},
    )
    minimum_top_k_response = client.post(
        "/corpora/research/retrieval/query",
        json={"question": "anything", "top_k": 1},
    )
    maximum_top_k_response = client.post(
        "/corpora/research/retrieval/query",
        json={"question": "anything", "top_k": 20},
    )
    zero_top_k_response = client.post(
        "/corpora/research/retrieval/query",
        json={"question": "anything", "top_k": 0},
    )
    invalid_top_k_response = client.post(
        "/corpora/research/retrieval/query",
        json={"question": "anything", "top_k": 21},
    )

    assert blank_question_response.status_code == 422
    assert minimum_top_k_response.status_code == 200
    assert maximum_top_k_response.status_code == 200
    assert zero_top_k_response.status_code == 422
    assert invalid_top_k_response.status_code == 422


def test_answer_query_returns_extractive_answer_with_source_passage(
    client: TestClient,
) -> None:
    upload_response = client.post(
        "/corpora/research/documents",
        files={
            "file": (
                "answer.md",
                b"# Answer\n\nThe answer pipeline returns the top retrieved passage.",
                "text/markdown",
            )
        },
    )
    document_id = upload_response.json()["document_id"]

    response = client.post(
        "/corpora/research/answers/query",
        json={"question": "The answer pipeline returns the top retrieved passage."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["corpus_id"] == "research"
    assert payload["question"] == "The answer pipeline returns the top retrieved passage."
    assert payload["answer"] == "The answer pipeline returns the top retrieved passage."
    assert set(payload["source_passages"][0]) == {
        "rank",
        "score",
        "document_id",
        "section_id",
        "passage_id",
        "heading_path",
        "start_line",
        "end_line",
        "text",
    }
    assert [
        (
            passage["rank"],
            passage["document_id"],
            passage["section_id"],
            passage["passage_id"],
            passage["heading_path"],
            passage["start_line"],
            passage["end_line"],
            passage["text"],
        )
        for passage in payload["source_passages"]
    ] == [
        (
            1,
            document_id,
            f"{document_id}:section:0",
            f"{document_id}:section:0:passage:0",
            ["Answer"],
            3,
            3,
            "The answer pipeline returns the top retrieved passage.",
        )
    ]
    assert isinstance(payload["source_passages"][0]["score"], float)


def test_answer_query_returns_no_answer_for_empty_corpus(
    client: TestClient,
) -> None:
    response = client.post(
        "/corpora/empty/answers/query",
        json={"question": "anything"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "corpus_id": "empty",
        "question": "anything",
        "answer": None,
        "source_passages": [],
    }


def test_answer_query_validates_question_only(client: TestClient) -> None:
    blank_question_response = client.post(
        "/corpora/research/answers/query",
        json={"question": "   "},
    )
    valid_question_response = client.post(
        "/corpora/research/answers/query",
        json={"question": "anything"},
    )
    unexpected_top_k_response = client.post(
        "/corpora/research/answers/query",
        json={"question": "anything", "top_k": 1},
    )

    assert blank_question_response.status_code == 422
    assert valid_question_response.status_code == 200
    assert unexpected_top_k_response.status_code == 422


def test_answer_query_openapi_uses_answer_naming(client: TestClient) -> None:
    payload = client.get("/openapi.json").json()

    operation = payload["paths"]["/corpora/{corpus_id}/answers/query"]["post"]
    request_schema = payload["components"]["schemas"]["AnswerQueryRequest"]
    response_schema = payload["components"]["schemas"]["AnswerQueryResponse"]

    assert "answer" in operation["operationId"]
    assert set(request_schema["properties"]) == {"question"}
    assert set(response_schema["properties"]) == {
        "corpus_id",
        "question",
        "answer",
        "source_passages",
    }
    assert (
        response_schema["properties"]["source_passages"]["items"]["$ref"]
        == "#/components/schemas/RetrievedPassageResponse"
    )


def test_rejects_non_markdown_upload(client: TestClient) -> None:
    response = client.post(
        "/corpora/product-notes/documents",
        files={"file": ("notes.txt", b"# Looks like markdown.", "text/plain")},
    )

    assert response.status_code == 415
    assert (
        response.json()["detail"]
        == "Only Markdown files with .md or .markdown extensions are supported."
    )
