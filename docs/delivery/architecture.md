# Current Architecture

DocForge is currently an API-first Markdown ingestion service.

Markdown uploads enter through `POST /corpora/{corpus_id}/documents`. The API
validates Markdown support and delegates to `DocumentService`.

The service decodes the upload, creates a stable document id, parses Markdown
into sections and passages, generates one embedding per passage, and commits the
document plus passage embeddings through a single write-side persistence port.
A successful upload returns `201` only after that synchronous processing and
commit finish.

Unexpected parse, embedding, or persistence failures fail the upload request and
do not create a partial document record.

The default app runtime uses in-memory repositories. Parsed document structure is
an intermediate representation in this slice, not persisted state.

Application composition lives in the FastAPI app boundary. The runtime entrypoint
uses the `create_app` factory, and FastAPI lifespan startup creates one
application container holding validated `Settings` plus the singleton
`DocumentService`. `DOC_FORGE_EMBEDDING_MODEL` accepts `deterministic` or
`transformer`; transformer is the default runtime. Transformer mode uses the
default sentence-transformers adapter. Compose builds the default image with the
LLM dependency group so the default runtime has that backend installed. Hugging
Face and Torch cache directories default under
`DOC_FORGE_ARTIFACT_ROOT`; startup preflight validates those paths before model
construction.
