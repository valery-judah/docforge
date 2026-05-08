from __future__ import annotations

from fastapi.testclient import TestClient


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
    assert payload["state"] == "answered"
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
        "state": "insufficient_evidence",
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
        "state",
        "answer",
        "source_passages",
    }
    assert (
        response_schema["properties"]["source_passages"]["items"]["$ref"]
        == "#/components/schemas/RetrievedPassageResponse"
    )
