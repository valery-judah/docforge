# Current Architecture

DocForge currently implements the Markdown-only `mvp-0` spine end to end:
document ingestion, passage embeddings, scoped retrieval, answer or abstention,
and source-passage inspection over an in-memory runtime.

Implemented HTTP surface:

- `POST /corpora/{corpus_id}/documents`
- `GET /corpora/{corpus_id}/documents`
- `GET /corpora/{corpus_id}/documents/{document_id}`
- `GET /corpora/{corpus_id}/documents/{document_id}/inspection`
- `POST /corpora/{corpus_id}/retrieval/query`
- `POST /corpora/{corpus_id}/answers/query`

Markdown uploads enter through the document endpoint. The API validates Markdown
support and delegates to `DocumentService`. The service decodes the upload,
creates a stable document id, parses Markdown into sections and passages,
generates one embedding per passage, and commits the document plus passage
embeddings through a single write-side persistence port. A successful upload
returns `201` only after that synchronous processing and commit finish.

Unexpected parse, embedding, or persistence failures fail the upload request and
do not create a partial document record.

Retrieval embeds the normalized question, ranks passage embeddings by cosine
similarity, and returns candidates from the active corpus only.

Answering is a two-step flow:

1. retrieve the top `k` passages from the active corpus;
2. if the top score is below the configured support threshold, return
   `insufficient_evidence`; otherwise generate a plain-text answer from the
   retrieved passages and return `answered`.

The default answer synthesizer backend is Ollama with `qwen3.5:9b`. The
deterministic answer synthesizer remains available for tests and explicitly
offline workflows. Ollama availability is not a startup precondition; if the
configured synthesizer is unavailable, answer requests fail at request time
while ingestion and inspection remain available.

Host-local app runs default `DOC_FORGE_OLLAMA_BASE_URL` to
`http://127.0.0.1:11434`. Docker Compose intentionally uses
`http://host.docker.internal:11434` instead so the API container can reach a
host-local Ollama runtime. The shared `.env.example` leaves that setting
commented to avoid overriding the Compose-safe default with container-local
`127.0.0.1`.

The default app runtime uses in-memory repositories. Parsed document structure
is an intermediate representation in this slice, not persisted state.

Application composition lives in the FastAPI app boundary. The runtime
entrypoint uses the `create_app` factory, and FastAPI lifespan startup creates
one application container holding validated `Settings` plus the singleton
`DocumentService`, `RetrievalService`, and `AnswerService`.

`DOC_FORGE_EMBEDDING_MODEL` accepts `deterministic` or `transformer`;
transformer is the default embedding runtime. Transformer mode uses the default
sentence-transformers adapter. Compose builds the default image with the LLM
dependency group so the default runtime has that backend installed. Hugging Face
and Torch cache directories default under `DOC_FORGE_ARTIFACT_ROOT`; startup
preflight validates those paths before model construction.
