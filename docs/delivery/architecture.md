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
