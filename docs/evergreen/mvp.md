# MVP-0: Current Markdown Evaluation Baseline

## 1. Purpose

`mvp-0` is the current evaluation-ready baseline of DocForge: the smallest
executable end-to-end slice that the repository both implements and can
exercise repeatedly today.

It has two goals:

1. Provide a minimal path that users and developers can walk end to end.
2. Provide a stable baseline contract for evaluation work over the current
   Markdown-only system spine.

This document is intentionally narrow. It describes current measured behavior,
not the broader future product target. If this document conflicts with
historical material in `docs/archive/`, this evergreen document wins.

## 2. Relationship To The Broader Product

The broader DocForge direction remains a trust-first question-answering and
evidence-inspection service over a bounded uploaded corpus.

`mvp-0` is the current Markdown-only baseline within that direction. It is the
canonical contract for the evaluation platform until broader capabilities are
implemented and supported by evaluation coverage.

This document does not describe future PDF support, richer support-state
handling, or broader answer guarantees. Those remain deferred.

## 3. Scope

### 3.1 In Scope

`mvp-0` includes:

1. Markdown upload or registration into a bounded query scope.
2. Stable document identity.
3. Markdown body text available for retrieval.
4. Recoverable Markdown heading context where available.
5. Retrieval limited to the active query scope.
6. Answer-or-abstain behavior driven by scoped retrieval and a configured
   support threshold.
7. Source references tied to retrieved Markdown evidence.
8. Evidence inspection over stored Markdown documents and retrieved passages.
9. Evaluation coverage for the current end-to-end Markdown path.

### 3.2 Out Of Scope

`mvp-0` excludes:

1. PDF upload, PDF parsing, and page provenance.
2. OCR, scanned documents, and visual understanding.
3. Mixed PDF/Markdown querying or synthesis.
4. Advanced hybrid retrieval, lexical search, or advanced reranking.
5. Exhaustive multi-document synthesis.
6. Document deletion, reindexing, and versioning semantics.
7. Collaboration, sharing, version history, cloud-drive sync, billing, or
   admin controls.
8. Production observability or production-grade background job semantics.
9. Exact scholarly citation formatting.
10. Frontend polish beyond what is needed to exercise the flow.

### 3.3 Deferred Until Evaluation Coverage Exists

The following behaviors are intentionally excluded from the current functional
contract, even if they remain part of the broader product direction:

1. Strong grounding enforcement beyond passing retrieved evidence into the
   answering path.
2. Explicit classification of unsupported, ambiguous, conflicting, or partially
   supported questions.
3. Richer support-state behavior beyond `answered` and `insufficient_evidence`.
4. Persistent query auditing or run-history traceability.
5. Broader smoke-pack coverage than the currently proven targeted baseline.

## 4. Minimal User Flow

1. User provides one or more Markdown files in a bounded query scope.
2. System makes Markdown text and recoverable heading context available as
   inspectable evidence.
3. User asks a natural-language question against the active query scope.
4. System retrieves relevant evidence from that scope only.
5. System either returns `insufficient_evidence` or returns an answer together
   with the retrieved source passages used for that result.
6. User can inspect the Markdown evidence references behind the result.

## 5. Minimal Functional Contract

### M0-1. Markdown Ingestion

Users can provide Markdown files within a bounded query scope.

Acceptance criteria:

- A valid Markdown file is accepted only after it is queryable in the selected
  scope.
- Unsupported file types are rejected.
- Each accepted document can be referred to consistently after ingestion.
- Each accepted document belongs to one active query scope.
- Ingestion errors return an error and do not create a partial document record.

### M0-2. Bounded Query Scope

Questions are answered only from documents in the selected query scope.

Acceptance criteria:

- A user can ask a question against a specific scope.
- Retrieval and answering are limited to documents in that scope.
- Evidence from outside the selected scope is not returned or cited.
- Cross-scope leakage is covered by the current targeted baseline.

### M0-3. Markdown Evidence

The system turns Markdown content into evidence that can later be retrieved,
inspected, and cited.

Acceptance criteria:

- Markdown body text is available for retrieval.
- Recoverable heading context is preserved where possible.
- Evidence remains traceable back to the source document.
- Text order is preserved well enough to support retrieval and source
  inspection.
- The system does not invent headings, sections, anchors, or source locations.
- Coarse real provenance is preferred over precise but false provenance.

### M0-4. Retrieval

The system retrieves relevant Markdown evidence from the active query scope.

Acceptance criteria:

- A natural-language question can retrieve relevant evidence from queryable
  Markdown documents.
- Retrieval is limited to the active scope.
- Retrieved evidence remains connected to its source document.

### M0-5. Answer Or Abstention

The system either returns an answer from the current answering path or
abstains.

Supported response states:

```text
answered
insufficient_evidence
```

Acceptance criteria:

- Answering uses only passages retrieved from the active query scope as answer
  inputs.
- If no retrieved passage meets the configured support threshold, the system
  returns `insufficient_evidence`.
- Answered responses include source references for the retrieved evidence used.
- This slice does not guarantee explicit unsupported, ambiguous, conflicting,
  or partial-support classification beyond the current abstention behavior.

## 6. Conceptual Product Surface

The exact API routes are not prescribed here. Current implementation routes and
runtime shape live in `docs/delivery/architecture.md` until a stable public
HTTP contract is promoted.

`mvp-0` only needs a product surface capable of exercising these conceptual
operations:

1. Register or upload a Markdown document into a bounded query scope.
2. Ask a question against the bounded query scope.
3. Inspect the answer, response state, and evidence references.

## 7. Evaluation Baseline

This baseline should remain small enough to evaluate repeatedly. Future
evaluation work should continue to reuse this Markdown-only path as the
baseline before adding broader capabilities.

The current baseline is proven through targeted tests and API checks covering:

1. Markdown ingestion and inspection.
2. Scoped retrieval over the active corpus only.
3. Answer responses that return retrieved source passages.
4. `insufficient_evidence` when retrieved support is absent or below threshold.
5. Cross-corpus isolation in targeted retrieval and document-access tests.

The shipped demo smoke harness is narrower than the full targeted baseline and
should be treated as one runtime check within the broader evaluation surface.

## 8. Delivery Design Notes

Implementation-level details for the current delivery slice live in
`docs/delivery/architecture.md`.

## 9. Exit Criteria

Exit criteria are intentionally minimal for this slice:

1. Markdown documents can be accepted into a bounded query scope.
2. Retrieved evidence is limited to the active scope.
3. Answered responses return retrieved Markdown evidence references.
4. Insufficient support produces `insufficient_evidence`.
5. Source references resolve to real Markdown evidence.
6. The current targeted evaluation baseline can exercise the end-to-end path.
