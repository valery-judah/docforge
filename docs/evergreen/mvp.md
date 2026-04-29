# MVP-0: Markdown-Only Base Slice

## 1. Purpose

`mvp-0` is the smallest executable delivery slice for the document question-answering MVP.

It proves one end-to-end product invariant over Markdown files:

```text
uploaded Markdown
  -> accepted document in a query scope
  -> retrievable Markdown evidence
  -> corpus-scoped retrieval
  
query lifecycle
  -> grounded answer or abstention
  -> inspectable Markdown source reference
```

`mvp-0` is not the full MVP. It excludes PDFs, mixed-format corpora, partial-support handling, ambiguity handling, advanced retrieval, production observability, rich UI, and full evaluation infrastructure.

## 2. Relationship To The Full MVP

The full MVP, defined in `docs/archive/mvp.md`, is a trust-first question-answering and evidence-inspection service over a bounded uploaded corpus of text-based PDFs and Markdown files.

`mvp-0` is a narrower delivery slice under that product direction. It validates the product spine with Markdown only before adding PDF extraction, page provenance, mixed-format synthesis, and richer support-state behavior.

This document does not broaden MVP scope. If this document conflicts with `docs/archive/mvp.md`, `docs/archive/functional-requirements.md`, `docs/archive/architecture.md`, or `docs/archive/api-contracts.md`, the evergreen document wins.

## 3. Scope

### 3.1 In Scope

`mvp-0` includes:

1. Markdown upload or registration into a bounded query scope.
2. Stable document identity.
3. Markdown body text available for retrieval.
4. Recoverable Markdown heading context where available.
5. Retrieval limited to the active query scope.

???
1. Simple grounded answering from retrieved evidence only.
2. Basic abstention when retrieved evidence is absent or too weak.
3. Source references tied to retrieved Markdown evidence.
4. Minimal query traceability for debugging trust failures.

### 3.2 Out Of Scope

`mvp-0` excludes:

1. PDF upload, PDF parsing, and page provenance.
2. OCR, scanned documents, and visual understanding.
3. Table-centric parsing or table-centric question answering.
4. Mixed PDF/Markdown querying or synthesis.
5. Partial-support, ambiguity, conflict, or unsupported-question-type classification.
6. Advanced hybrid retrieval, lexical search, or advanced reranking.
7. Exhaustive multi-document synthesis.
8. Collaboration, sharing, version history, cloud-drive sync, billing, or admin controls.
9. Production observability or production-grade background job semantics.
10. Document deletion, reindexing, and versioning semantics.
11. Exact scholarly citation formatting.
12. Frontend polish beyond what is needed to exercise the flow.

## 4. Minimal User Flow

1. User provides one or more Markdown files in a bounded query scope.
2. System makes Markdown text and recoverable heading context available as traceable evidence.
3. User asks a natural-language question against the active query scope.
4. System retrieves relevant evidence from that scope only.

## 5. Minimal Functional Contract

### M0-1. Markdown Ingestion

Users can provide Markdown files for processing within a bounded query scope.

Acceptance criteria:

- A valid Markdown file is accepted for processing.
- Unsupported file types are rejected or clearly marked unsupported.
- Each accepted document can be referred to consistently after ingestion.
- Each accepted document belongs to one active query scope.
- The system exposes whether the document is still processing, ready for querying, or failed.

### M0-2. Bounded Query Scope

Questions are answered only from documents in the selected query scope.

Acceptance criteria:

- A user can ask a question against a specific scope.
- Retrieval and answering are limited to documents in that scope.
- Evidence from outside the selected scope is not returned or cited.
- Cross-scope leakage is detectable in smoke testing.

### M0-3. Markdown Evidence

The system turns Markdown content into evidence that can later be retrieved, inspected, and cited.

Acceptance criteria:

- Markdown body text is available for retrieval.
- Recoverable heading context is preserved where possible.
- Evidence remains traceable back to the source document.
- Text order is preserved well enough to support retrieval and source inspection.
- The system does not invent headings, sections, anchors, or source locations. (?)
- Coarse real provenance is preferred over precise but false provenance.

### M0-4. Retrieval

The system retrieves relevant Markdown evidence from the active query scope.

Acceptance criteria:

- A natural-language question can retrieve relevant evidence from queryable Markdown documents.
- Retrieval is limited to the active scope.
- Retrieved evidence remains connected to its source document.

### M0-5. Grounded Answer Or Abstention

The system either answers from retrieved evidence or abstains.

Supported response states:

```text
answered
insufficient_evidence
```

Acceptance criteria:

- If retrieved evidence is sufficient, the answer is based only on that evidence.
- If evidence is absent, irrelevant, or too weak, the system returns `insufficient_evidence`.
- The system does not present model prior knowledge as corpus-backed.
- Answered responses include source references for the evidence used.
- Unsupported, ambiguous, conflicting, or only partially supported questions fall back to `insufficient_evidence` in this slice.


## 7. Conceptual Product Surface

The exact API routes are not prescribed here. `docs/evergreen/api-contracts.md` owns the stable public HTTP contract.

`mvp-0` only needs a product surface capable of exercising these conceptual operations:

1. Register or upload a Markdown document into a bounded query scope.
2. Ask a question against the bounded query scope.
3. Inspect the answer, response state

## 8. Delivery Design Notes

Implementation-level details for the current delivery slice live in `docs/delivery/design.md`.


## 10. Exit Criteria

we will need it but later
