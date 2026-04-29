# MVP-0: Markdown-Only Base Slice

## 1. Purpose

`mvp-0` is the smallest executable delivery slice for the document question-answering MVP.

It proves one end-to-end product invariant over Markdown files:

```text
uploaded Markdown
  -> traceable evidence unit
  -> embedded and stored evidence
  -> corpus-scoped retrieval
  -> grounded answer or abstention
  -> inspectable Markdown source reference
```

`mvp-0` is not the full MVP. It excludes PDFs, mixed-format corpora, partial-support handling, ambiguity handling, advanced retrieval, production observability, rich UI, and full evaluation infrastructure.

## 2. Relationship To The Full MVP

The full MVP, defined in `docs/evergreen/mvp.md`, is a trust-first question-answering and evidence-inspection service over a bounded uploaded corpus of text-based PDFs and Markdown files.

`mvp-0` is a narrower delivery slice under that product direction. It validates the product spine with Markdown only before adding PDF extraction, page provenance, mixed-format synthesis, and richer support-state behavior.

This document does not broaden MVP scope. If this document conflicts with `docs/evergreen/mvp.md`, `docs/evergreen/functional-requirements.md`, `docs/evergreen/architecture.md`, or `docs/evergreen/api-contracts.md`, the evergreen document wins.

## 3. Scope

### 3.1 In Scope

`mvp-0` includes:

1. Markdown upload or registration into a bounded query scope.
2. Stable document identity.
3. Basic processing status: `processing`, `queryable`, `failed`.
4. Markdown text extraction.
5. Markdown heading-path recovery where available.
6. Evidence unit creation from Markdown text.
7. Embedding generation for evidence units.
8. Persistence of documents, evidence units, provenance metadata, and embeddings.
9. Top-k semantic retrieval filtered to the active query scope.
10. Simple grounded answering from retrieved evidence only.
11. Basic abstention when retrieved evidence is absent or too weak.
12. Source references tied to retrieved Markdown evidence.
13. Minimal query traceability for debugging trust failures.

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
2. System registers each document with stable identity and status `processing`.
3. System extracts Markdown text and recoverable heading paths.
4. System creates traceable evidence units.
5. System embeds and stores the evidence units.
6. System marks successfully processed documents as `queryable`.
7. User asks a natural-language question against the active query scope.
8. System retrieves top-k evidence units from that scope only.
9. System answers from retrieved evidence or returns `insufficient_evidence`.
10. System returns source references for evidence used in the answer.

## 5. Minimal Functional Contract

### M0-1. Markdown Ingestion

Users can provide Markdown files for processing.

Acceptance criteria:

- A valid `.md` file is accepted.
- A non-Markdown file is rejected or clearly marked unsupported.
- The upload or registration creates a stable document identity.
- The document belongs to exactly one active query scope.
- The document starts in `processing` status.

### M0-2. Bounded Query Scope

Queries run only against the selected scope.

Acceptance criteria:

- Each document has a scope identifier, such as `corpus_id` or `workspace_id`.
- Each evidence unit has the same scope identifier and a `document_id`.
- Retrieval is filtered by the active scope identifier.
- Evidence from another scope is never returned.

### M0-3. Processing Status

Each document exposes enough processing state to prevent silent querying of failed content.

Required statuses:

```text
processing
queryable
failed
```

Acceptance criteria:

- A newly registered document starts as `processing`.
- A successfully processed document becomes `queryable`.
- A document that cannot be parsed or embedded becomes `failed`.
- Failed documents are not silently queried.
- Query behavior respects document status.

### M0-4. Markdown Evidence Units

The system extracts Markdown text and creates retrieval-addressable evidence units.

Minimum evidence-unit fields:

```text
evidence_unit_id
scope_id
document_id
source_type = markdown
heading_path
text
chunk_index
```

Acceptance criteria:

- Markdown body text is extracted.
- Heading paths are preserved where recoverable.
- Text order is preserved well enough for retrieval and inspection.
- Code blocks, lists, and table-like Markdown may be preserved as plain text.
- The system does not invent headings, sections, anchors, or source locations.
- Each evidence unit retains document identity, source type, local text, and available heading path.

### M0-5. Embedding And Retrieval

The system embeds evidence units and retrieves them by semantic similarity within the active scope.

Acceptance criteria:

- Each queryable evidence unit has an embedding.
- Embeddings are associated with the correct evidence unit.
- Embedding failures prevent the affected unit or document from being treated as queryable.
- A natural-language question retrieves top-k evidence units from the active scope.
- Retrieved evidence includes text and provenance metadata.
- Retrieved evidence is not detached from document identity.

### M0-6. Grounded Answer Or Abstention

The system generates a concise answer using retrieved evidence only, or abstains.

Supported response states:

```text
answered
insufficient_evidence
```

Acceptance criteria:

- If retrieved evidence is relevant enough, the answer is based only on that evidence.
- If retrieved evidence is empty, irrelevant, or too weak, the system returns `insufficient_evidence`.
- The answer includes source references for evidence used.
- The system does not present model prior knowledge as corpus-backed.
- The answer prompt instructs the model to answer only from provided evidence.

### M0-7. Evidence Rendering

The response includes inspectable Markdown evidence references.

Minimum response shape:

```json
{
  "answer": "...",
  "support_state": "answered | insufficient_evidence",
  "sources": [
    {
      "document_id": "...",
      "source_type": "markdown",
      "heading_path": ["...", "..."],
      "evidence_unit_id": "...",
      "excerpt": "..."
    }
  ]
}
```

Acceptance criteria:

- Every source reference resolves to a real uploaded Markdown document.
- Every source reference corresponds to retrieved evidence actually used.
- The system does not fabricate documents, headings, sections, anchors, or source support.
- If provenance is missing, the system does not present the claim as fully supported.
- Coarse real provenance is preferred over precise false provenance.

### M0-8. Minimal Traceability

The system records enough query information to debug obvious trust failures.

At minimum, record:

```text
query text
scope identifier
retrieved evidence_unit_ids
retrieval scores or ranks
selected evidence_unit_ids used for answering
answer text
answered versus insufficient_evidence decision
returned provenance payload
source_type slice = markdown
```

Acceptance criteria:

- A developer can inspect what evidence was retrieved.
- A developer can inspect what evidence was used in the answer.
- A developer can compare returned provenance with retrieved evidence.
- A developer can identify obvious unsupported-answer or false-provenance failures during smoke testing.

## 6. Minimal Query Policy

`mvp-0` deliberately avoids mature support-state reasoning.

Use a conservative binary policy:

```text
If no evidence is retrieved:
  return insufficient_evidence.

If retrieved evidence is below the relevance threshold:
  return insufficient_evidence.

If retrieved evidence is relevant:
  answer only from that evidence and cite it.

If the model cannot answer from the provided evidence:
  return insufficient_evidence.
```

Partial support, ambiguity, conflict, and unsupported question-type handling belong in later slices. In `mvp-0`, those cases should not produce confident unsupported answers; they should fall back to `insufficient_evidence` when the binary policy cannot support a grounded answer.

## 7. Conceptual Product Surface

The exact API routes are not prescribed here. `docs/evergreen/api-contracts.md` owns the stable public HTTP contract.

`mvp-0` only needs a product surface capable of exercising these conceptual operations:

1. Register or upload a Markdown document into a bounded query scope.
2. Read document processing status.
3. Ask a question against the bounded query scope.
4. Inspect the answer, response state, source references, and minimal trace.

Implementations should use the current stable service routes where possible and update `docs/evergreen/api-contracts.md` before introducing incompatible public API changes.

## 8. Conceptual Processing Pipeline

```text
Receive Markdown
  -> validate Markdown support
  -> create document identity
  -> set status = processing
  -> extract text and heading paths
  -> create evidence units with provenance
  -> generate and store embeddings
  -> mark document queryable or failed
```

```text
Question
  -> embed question
  -> vector search filtered by active scope
  -> retrieve top-k evidence units
  -> assemble evidence payload with text and provenance
  -> decide answered vs insufficient_evidence
  -> generate answer from evidence or abstain
  -> render sources from used evidence
  -> record minimal trace
```

## 9. Minimal Smoke Evaluation

The first smoke eval should be deliberately small: 4 to 6 questions over 2 to 3 Markdown files.

Required cases:

| Case | Purpose |
|---|---|
| Supported factual lookup | Proves retrieval, answering, and citation for a direct fact. |
| Localized explanation | Proves a short explanation can stay grounded in local Markdown evidence. |
| Unsupported in corpus | Proves the system returns `insufficient_evidence` instead of guessing. |
| Source navigation or provenance check | Proves returned references resolve to real retrieved evidence. |
| Cross-scope leakage check | Proves retrieval does not return evidence from another scope. |

Minimum pass conditions:

- Supported questions return relevant Markdown evidence.
- Unsupported questions do not produce confident unsupported answers.
- Source references resolve to actual Markdown documents and heading paths where available.
- No answer cites a source that was not retrieved and used.
- Cross-scope evidence leakage does not occur.

## 10. Exit Criteria

`mvp-0` is complete when:

1. A Markdown file can be registered or uploaded into a bounded query scope.
2. The system exposes `processing`, `queryable`, and `failed` states.
3. Markdown text and recoverable heading paths become traceable evidence units.
4. Evidence units are embedded and stored.
5. A user can ask a natural-language question against the bounded scope.
6. Retrieval returns evidence only from that scope.
7. The system returns either `answered` or `insufficient_evidence`.
8. Answered responses are based on retrieved evidence only.
9. Returned sources point to retrieved Markdown evidence actually used.
10. Minimal query/evidence/answer trace data is inspectable.
11. The minimal smoke eval can be run repeatedly during development.

## 11. Summary

`mvp-0` is the absolute minimal base for the MVP direction:

```text
Markdown upload
  -> parse
  -> chunk
  -> embed
  -> retrieve
  -> answer or abstain
  -> cite Markdown evidence
```

The success criterion is not polished answer quality. It is that document identity, evidence text, embeddings, retrieval results, answer generation, and source rendering remain connected end to end.
