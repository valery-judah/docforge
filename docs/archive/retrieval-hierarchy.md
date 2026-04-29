# Retrieval Hierarchy

**Status:** Draft  
**Scope:** MVP / Version 1  
**Last updated:** 2026-03-23  
**Related docs:** `docs/evergreen/mvp.md`, `docs/evergreen/lifecycle-and-evidence-flow.md`, `docs/evergreen/architecture.md`, `docs/delivery/eval-support-semantics.md`, `docs/delivery/eval-vocabulary.md`, `docs/evergreen/first-tier-failures.md`

## Purpose

This document defines the canonical retrieval hierarchy for the MVP.

Its job is narrow:

- define the structural hierarchy used for retrieval-addressable evidence;
- define the retrieval unit used across ingestion, retrieval, and provenance discussion;
- define the minimum provenance-bearing structure that must survive from ingestion to answer;
- map the conceptual model to the current implementation.

This document does **not** own:

- product scope or trust promise;
- full lifecycle semantics;
- support-state semantics;
- failure taxonomy;
- detailed parser, chunker, or retriever implementation contracts;
- broad repo topology or service-boundary truth.

Authority boundaries are:

- `docs/evergreen/mvp.md` owns product scope, trust promise, and MVP boundaries;
- `docs/evergreen/lifecycle-and-evidence-flow.md` owns the broader document lifecycle, query lifecycle, and evidence-flow framing;
- `docs/evergreen/architecture.md` owns current implementation truth at repo level;
- this document owns the shared structural concepts used across ingestion, retrieval, provenance, and evidence inspection.

---

## 1. Terminology Rules

This document uses the following terminology rules.

### Canonical conceptual terms

Use these terms in architecture, product, and evaluation docs:

- **Document**
- **Section**
- **Passage**

### Implementation terms

Use these terms when discussing current code or runtime objects directly:

- **Chunk**: the current implementation model for a passage
- **RetrievedCandidate**: the query-time ranked representation of a retrieved passage

### Naming guidance

Prefer **Passage** over **Chunk** in conceptual writing.

Use **Chunk** when referring to concrete implementation models, schemas, or runtime objects.

Prefer **section_path** as the canonical conceptual locator term.

The current implementation may use **`heading_path`** for the same role. When discussing code or payloads, call that out explicitly rather than letting the terminology drift silently.

---

## 2. Canonical Hierarchy

The canonical conceptual hierarchy is:

`DOCUMENT -> SECTION -> PASSAGE`

### Document

A **Document** is the stable source object for one uploaded file.

It is the ownership boundary for downstream structure, provenance, and retrieval-addressable units.

### Section

A **Section** is a semantic and structural container recovered within one document.

It carries heading or path structure and provides the main navigation and citation scaffold.

A section is **not** the default ranked retrieval unit in the current MVP design.

### Passage

A **Passage** is the retrieval-addressable text unit derived from one section.

It is the default unit used to discover answerable evidence.

A passage is conceptually smaller than a document and usually smaller than a section, while still preserving enough local context for retrieval, answer assembly, and source inspection.

---

## 3. Retrieval Unit Definition

The current retrieval unit is a **section-aware passage**.

That means:

- each passage belongs to exactly one recovered section;
- passages are the units ranked by retrieval;
- sections remain the semantic containers around those passages;
- later stages preserve document and section linkage rather than treating retrieved text as a free-floating fragment.

The current system should therefore be described as:

**section-aware passage retrieval**

It should **not** be described as:

- section-first retrieval, or
- unstructured chunk retrieval

In current implementation terms:

- a conceptual passage is represented by **`Chunk`**;
- a retrieved ranked passage is represented by **`RetrievedCandidate`**.

---

## 4. Why This Hierarchy Exists

The hierarchy exists to preserve trustworthy evidence flow.

The system is not only trying to retrieve relevant text. It is trying to retrieve text in a form that still carries enough structure to support:

- grounded answering;
- source navigation;
- inspectable provenance;
- answer narrowing or abstention when support is weak;
- non-fabricated citation behavior.

The hierarchy therefore exists to preserve **trust-carrying structure**, not just retrieval convenience.

---

## 5. Minimum Retrieval-Unit Contract

Every retrieval-addressable passage must preserve enough information to remain inspectable and traceable across retrieval, context assembly, and citation.

### Required conceptual fields

At minimum, a passage should preserve:

- `unit_id`
- `document_id`
- `source_type`
- `section_id` when recoverable
- `section_path` when recoverable
- `text`
- `token_count`
- `ordinal` or equivalent local order
- page or source location when recoverable

### Retrieval-time additions

A retrieved passage candidate should additionally preserve:

- `locator`
- `retrieval_score`
- `retrieval_rank`

### Current implementation mapping

In current code, this contract is approximately realized through:

- `Chunk` for the stored retrieval-addressable unit;
- `RetrievedCandidate` for the ranked query-time form;
- `heading_path` as the current implementation field that fills the role of `section_path`.

### Contract rule

If a field is not reliably recoverable, the system should preserve a coarser real locator rather than fabricate a more precise one.

---

## 6. Segmentation Policy

Passages are created **inside recovered sections**.

The segmentation policy should preserve structural and semantic integrity as much as possible.

### Structural intent

Segmentation should:

- strongly prefer section boundaries over arbitrary fixed windows;
- preserve section ownership for every passage;
- preserve local order within the containing section;
- avoid splitting in ways that destroy inspectability or provenance.

### Practical effect

In practice, this means:

- a small section may remain a single passage;
- a large section may produce multiple passages;
- passage splitting should remain section-bounded by default rather than crossing section boundaries.

### Current implementation truth

Today, the current chunker is passage-oriented inside section structure:

- sections are recovered first;
- chunks are derived inside those sections;
- splitting happens when bounded passage size or structural constraints require it.

This is section-aware passage segmentation, not section-as-default retrieval.

---

## 7. Provenance Floor

The retrieval hierarchy must preserve enough information for users to inspect where answer support came from.

### Canonical conceptual locator

The canonical conceptual source-locator term is:

**`section_path`**

This is the preferred term in docs because it describes the role rather than the implementation history.

### Current implementation locator

The current implementation may store this concept using:

**`heading_path`**

That should be treated as an implementation field name, not the canonical conceptual term.

### Source-type provenance expectations

For MVP, provenance expectations are source-sensitive.

#### Markdown

Markdown should usually preserve:

- document identity;
- section path.

#### PDF

PDF should usually preserve:

- document identity;
- page;
- section-like context when recoverable.

#### Mixed-source synthesis

Mixed-source synthesis should usually preserve:

- one usable provenance record per contributing source.

### Provenance rule

When precision is uncertain, **coarse real provenance is better than false precision**.

This document defines the structural expectations that make provenance possible. It does not define full answer-time support or citation policy.

---

## 8. Concept-to-Implementation Map

| Conceptual role | Canonical term | Current implementation term | Meaning |
|---|---|---|---|
| source object | `Document` | `Document` | stable source identity |
| structural container | `Section` | `Section` | recovered hierarchy and navigation scaffold |
| retrieval unit | `Passage` | `Chunk` | retrieval-addressable text unit inside one section |
| retrieved passage | retrieved passage candidate | `RetrievedCandidate` | ranked query-time retrieval result |
| structural locator | `section_path` | `heading_path` | structural anchor carried from section into downstream use |

This map exists to prevent conceptual and implementation terms from collapsing into each other.

---

## 9. Current Implementation Truth

Current implementation truth for MVP is:

- sections are recovered before chunk production;
- chunks are produced within those recovered sections;
- retrieval ranks chunks rather than whole sections;
- downstream selection, context assembly, and citation preserve document and section linkage.

Small sections may happen to become one chunk, but that does not change the conceptual model. The default design remains passage-oriented retrieval inside section structure.

---

## 10. Runtime Flow

The retrieval hierarchy moves through the runtime in this order:

`ingestion -> section recovery -> passage/chunk production -> retrieval -> selection/context assembly -> answer + citation`

The hierarchy matters because provenance-bearing structure must survive across this flow rather than being reconstructed only at the end.

---

## 11. Handoff To Answer-Time Decisions

This document does not define support-state semantics or answer policy.

However, the retrieval hierarchy exists partly to support later decisions such as:

- whether a direct answer is justified;
- whether an answer should be narrowed or qualified;
- whether the system should abstain;
- whether ambiguity or conflict should be surfaced;
- whether the returned provenance is inspectable enough for the question and source type.

The hierarchy is therefore not only a storage model. It is part of the control surface for trustworthy answer behavior.

---

## 12. Trust-Critical Invariants

The hierarchy must preserve the following invariants:

- every passage belongs to exactly one document;
- every passage belongs to exactly one recovered section;
- local order is preserved within the document or containing section;
- section or page anchors survive into retrieval and citation when recoverable;
- retrieval and citation must not fabricate anchors or stronger provenance than the source supports;
- retrieved text must remain inspectable as source-backed evidence;
- related evidence must not automatically be treated as sufficient evidence.

These are trust invariants, not merely implementation preferences.

---

## 13. Verification And Observability Hooks

This document does not define a full testing strategy, but the hierarchy should have direct engineering consequences.

At minimum, the system should make it possible to verify or log:

- passage-to-document linkage;
- passage-to-section linkage;
- locator payload completeness;
- retrieved units and scores;
- provenance payload returned to the user;
- fallback behavior when structure is missing or only coarsely recoverable.

If these checks are absent, several retrieval, provenance, and structure failures become difficult to diagnose reliably.

---

## 14. Non-Goals And Deferred Redesigns

This document does **not** commit the project to:

- section-as-default embedded retrieval;
- paragraph-perfect universal anchors;
- advanced hybrid retrieval or reranking architecture;
- a broader retrieval redesign beyond MVP trust needs;
- a future publication, mutation, supersession, or withdrawal policy;
- non-MVP guarantees for OCR-heavy, figure-heavy, or layout-heavy documents.

Those may matter later, but they are deferred until the current section-aware passage model is shown to be insufficient under evaluation pressure.

---

## 15. Worked Examples

### Example A: Markdown source

A Markdown document may be represented conceptually as:

`Document -> Section -> Passage`

Example:

- `Document`: `distributed-systems-notes.md`
- `Section`: `["Chapter 3", "Two-Phase Commit"]`
- `Passage`: a bounded text unit containing a few paragraphs about coordinator failure handling

At retrieval time, the runtime may return a `RetrievedCandidate` that preserves:

- document identity;
- section path;
- passage text;
- retrieval score;
- locator metadata.

The user-facing provenance surface may then show:

- document title;
- section path;
- a supporting snippet.

### Example B: PDF source

A PDF document may be represented conceptually as:

`Document -> Section -> Passage`

Example:

- `Document`: `database-internals.pdf`
- `Section`: a recovered section-like container for a chapter or subsection
- `Passage`: a bounded text unit derived from that section

At retrieval time, the runtime may return a `RetrievedCandidate` that preserves:

- document identity;
- recovered section linkage when available;
- page-level locator;
- passage text;
- retrieval score.

The user-facing provenance surface may then show:

- document title;
- page;
- section-like context when recoverable;
- a supporting snippet.

These examples are illustrative. They are here to show the hierarchy and provenance surface, not to define a public API.

---

## 16. Summary

For MVP, the canonical retrieval hierarchy is:

`DOCUMENT -> SECTION -> PASSAGE`

In the current implementation:

- a passage is represented by `Chunk`;
- retrieval returns ranked `RetrievedCandidate` objects;
- sections remain the semantic and provenance scaffold around passage retrieval.

The project should therefore describe the current model as **section-aware passage retrieval**.

That description is precise enough to guide architecture, evaluation, provenance expectations, and implementation discussion without overcommitting the MVP to a larger retrieval redesign.

---

## 17. References

- `docs/evergreen/mvp.md`: product scope, trust promise, and provenance expectations
- `docs/evergreen/lifecycle-and-evidence-flow.md`: conceptual document/query lifecycles and broader evidence flow
- `docs/evergreen/architecture.md`: current repo shape and implemented seams
- `docs/delivery/eval-vocabulary.md`: terminology normalization for evaluation
- `docs/delivery/eval-support-semantics.md`: support-state meaning and minimum provenance floor
- `docs/evergreen/first-tier-failures.md`: trust-critical failures around support, provenance, abstention, and scope