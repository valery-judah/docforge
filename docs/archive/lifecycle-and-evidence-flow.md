# Lifecycle and Evidence Flow

## Purpose

This document defines the conceptual lifecycles that preserve the MVP trust contract from uploaded source files to final answers.

The MVP spec defines what the product promises. This document explains how that promise is protected across the internal evidence flow: how source files become traceable evidence-bearing units, how questions consume those units, and where the system must decide whether to answer, qualify, surface ambiguity, or abstain.

This document owns:

- the evidence-preparation lifecycle;
- the question-answering lifecycle;
- the handoff between those lifecycles;
- the trust-control points that protect grounded answering, inspectable provenance, and honest failure behavior.

This document does not own:

- product scope or user-facing guarantees;
- the canonical retrieval hierarchy;
- parser, chunker, index, or retriever implementation details;
- support-state semantics in detail;
- the full failure taxonomy;
- current service topology or repository structure.

Authority boundaries:

- `docs/evergreen/mvp.md` owns MVP scope, product promise, user-facing guarantees, and explicit deferrals.
- `docs/evergreen/functional-requirements.md` owns the 12 minimal functional requirements and their acceptance criteria.
- `docs/evergreen/retrieval-hierarchy.md` owns the canonical structural model, currently `DOCUMENT -> SECTION -> PASSAGE`.
- `docs/evergreen/architecture.md` owns current implementation truth.
- `docs/delivery/eval-support-semantics.md` owns detailed support-state semantics and answer behavior policy.
- `docs/evergreen/first-tier-failures.md` owns failure definitions, severity, review workflow, and remediation guidance.
- This document owns the conceptual lifecycle and evidence-flow control surface across those documents.

---

## 1. Core Principle

The question path must not invent what the document path failed to preserve.

If document identity, structure, source location, or local text context is lost during evidence preparation, the answering path should not reconstruct those properties by guesswork. It should degrade, qualify, or abstain rather than fabricate unsupported precision.

The lifecycle design exists to preserve this invariant:

```text
Source artifact
  -> traceable evidence unit
  -> retrieved evidence set
  -> support decision
  -> answer or abstention
  -> inspectable provenance
```

Each transition must preserve enough information for the next stage to make a trustworthy decision.

---

## 2. Lifecycle Overview

The MVP has two primary conceptual lifecycles:

1. **Evidence-preparation lifecycle**
2. **Question-answering lifecycle**

The evidence-preparation lifecycle turns uploaded documents into traceable, queryable evidence-bearing units.

The question-answering lifecycle consumes those units, decides what the available evidence supports, and returns an answer, a qualified answer, ambiguity handling, or an abstention with provenance where appropriate.

The handoff between the lifecycles is the active queryable corpus.

```text
Evidence preparation
Acquire -> Normalize -> Recover Structure -> Produce Evidence Units -> Validate Traceability -> Make Queryable

Question answering
Interpret -> Retrieve -> Build Evidence Set -> Decide Support -> Answer or Abstain -> Render Provenance
```

These lifecycles are conceptual. They describe required control responsibilities, not a required module layout or runtime implementation.

### 2.1 Relationship To Minimal Functional Requirements

The lifecycle protects the 12 minimal functional requirements defined in `docs/evergreen/functional-requirements.md`.

It does not duplicate acceptance criteria, implementation design, evaluation policy, or launch-gate failure definitions. Its role is to show where the evidence flow must preserve the MVP trust invariants:

- bounded uploaded corpus;
- traceable evidence;
- corpus-grounded answering;
- inspectable provenance;
- honest uncertainty;
- explicit scope boundaries;
- no fabricated source support.

---

## 3. Evidence-Preparation Lifecycle

The evidence-preparation lifecycle is responsible for converting uploaded files into retrieval-ready units that remain connected to their source.

Its output is not merely indexed text. Its output is evidence that can be retrieved, inspected, and cited without breaking provenance.

### 3.1 Acquire

The system accepts supported user-uploaded files and registers them as part of a bounded corpus.

Minimal requirements protected:

- MFR1: supported uploads;
- MFR2: bounded corpus creation;
- MFR3: stable source identity;
- MFR4: processing status.

At this stage, the system establishes:

- corpus membership;
- stable document identity;
- source type, such as `pdf` or `markdown`;
- ownership boundary;
- basic file-level status.

Control invariant:

> No later stage should treat text as corpus evidence unless it can be traced back to a registered source document.

Failure protected against:

- orphaned evidence units;
- cross-corpus contamination;
- source references that cannot resolve to a real uploaded document.

### 3.2 Normalize

The system extracts or normalizes source text into a workable internal representation.

For MVP, normalization is lightweight. It should preserve recoverable structure and provenance, not attempt exact document reconstruction or rich visual understanding.

Minimal requirements protected:

- MFR5: text extraction;
- MFR6: minimum source structure and provenance, where source-location signals are recoverable during normalization.

At this stage, the system should preserve where available:

- document boundaries;
- page or source-location signals;
- heading or section signals;
- text order;
- enough local context for later inspection.

Control invariant:

> Normalization may be coarse, but it must not erase the minimum source context needed for retrieval and evidence inspection.

Failure protected against:

- answerable text becoming uninspectable;
- page, section, or heading references becoming fabricated later;
- retrieval units losing their source boundaries.

### 3.3 Recover Structure

The system recovers document hierarchy where structure is present or reasonably inferable.

For Markdown, this usually means heading-based structure. For text-based PDFs, this may mean page-aware and/or inferred section structure, depending on what can be recovered reliably.

Structure recovery should aim to produce meaningful retrieval context, not perfect document layout.

Minimal requirements protected:

- MFR6: minimum source structure and provenance.

Control invariant:

> Recovered structure should be valid enough that retrieval units can be understood inside their document context.

Failure protected against:

- passages detached from their section meaning;
- misleading heading paths;
- malformed hierarchy that harms retrieval or source inspection.

### 3.4 Produce Evidence Units

The system derives retrieval-addressable evidence units from the normalized and structured representation.

In the current conceptual model, these are passage-level units linked to document and section context. This document does not redefine the canonical hierarchy; it assumes the hierarchy owned by `docs/evergreen/retrieval-hierarchy.md`.

Minimal requirements protected:

- MFR7: traceable evidence units.

Each evidence unit should carry, where recoverable:

- document identity;
- source type;
- section or heading path;
- page or source location;
- local text content;
- enough neighboring context to support inspection;
- any status flags that affect trust, such as weak structure or partial provenance.

Control invariant:

> Evidence units are only useful for this MVP if they can be retrieved and then inspected as source-grounded evidence.

Failure protected against:

- relevant retrieval without usable provenance;
- provenance rendered from metadata unrelated to the retrieved text;
- answers supported by text that users cannot reasonably inspect.

### 3.5 Validate Traceability

Before evidence units become part of the active queryable corpus, the system should validate that they remain traceable enough for MVP use.

This is a conceptual readiness gate, not merely an indexing detail.

A document or unit may be:

- **queryable** when text and provenance are sufficient for normal use;
- **queryable with limitations** when text is usable but structure or provenance is degraded;
- **failed** when the system cannot preserve enough text or traceability to support trustworthy retrieval and answering.

Minimal requirements protected:

- MFR3: stable source identity;
- MFR4: processing status;
- MFR7: traceable evidence units;
- MFR12: evidence rendering.

Control invariant:

> A unit that cannot point back to a real source document and coarse source location should not be treated as fully ready evidence.

Failure protected against:

- ungrounded answers caused by ingestion damage;
- incorrect provenance;
- silent degradation that later appears as a trust failure.

### 3.6 Make Queryable

Once evidence units are usable and traceable, they become part of the active queryable corpus.

This stage is the handoff point to the question-answering lifecycle.

Minimal requirements protected:

- MFR8: corpus retrieval, by ensuring only traceable evidence enters the active corpus.

Making a corpus queryable does not imply:

- publication workflow;
- version history;
- full mutation management;
- exhaustive retrieval guarantees;
- production-grade operational hardening.

Control invariant:

> The active queryable corpus should contain only evidence units whose source identity and inspectability status are known.

Failure protected against:

- retrieving stale or untraceable material;
- treating partially failed ingestion as fully reliable;
- mixing implementation readiness with trust readiness.

---

## 4. Question-Answering Lifecycle

The question-answering lifecycle is responsible for consuming the active queryable corpus without breaking the evidence contract.

Its output is not merely a generated answer. Its output is a support-aware response: answer, qualification, ambiguity handling, abstention, or explicit limitation, with provenance where an answer is given.

### 4.1 Interpret

The system interprets the user question relative to the active corpus and MVP capability boundaries.

Minimal requirements protected:

- MFR11: support-aware response behavior;
- scope honesty for explicit MVP boundaries.

This includes identifying whether the question appears to be:

- a corpus-grounded question;
- a partial or ambiguous request;
- a source-navigation request;
- a synthesis request;
- an unsupported question type;
- dependent on external knowledge not present in the corpus.

Control invariant:

> The system should treat the uploaded corpus as the answer boundary unless the response explicitly states a limitation or lack of support.

Failure protected against:

- answering external-world questions as if corpus-supported;
- missing scope boundaries;
- treating ambiguous questions as fully specified.

### 4.2 Retrieve

The system retrieves candidate evidence units from the active queryable corpus.

Retrieval should carry provenance metadata forward with the retrieved content. It should not return text detached from document identity or source-location context.

Minimal requirements protected:

- MFR8: corpus retrieval;
- MFR9: evidence handoff.

Control invariant:

> Retrieved content must remain connected to the provenance needed for answer generation and evidence rendering.

Failure protected against:

- relevant text without inspectable source support;
- answer generation using evidence that cannot be cited;
- provenance being reconstructed after the fact.

### 4.3 Build Evidence Set

The system selects and organizes the evidence it will actually consider for answering.

This may involve grouping, local context expansion, deduplication, source balancing, or pruning. The conceptual purpose is to define the support bundle used for the answer decision.

Minimal requirements protected:

- MFR9: evidence handoff;
- MFR10: grounded answering.

The evidence set should distinguish between:

- evidence used directly;
- related but insufficient evidence;
- conflicting evidence;
- missing evidence;
- evidence excluded because of weak provenance or scope mismatch.

Control invariant:

> The system should decide from an explicit evidence set, not from an opaque mix of retrieved text, model prior knowledge, and inferred context.

Failure protected against:

- related evidence being overstated as sufficient evidence;
- unsupported synthesis;
- inability to diagnose why an answer was produced.

### 4.4 Decide Support

Before final answer emission, the system decides what the evidence supports.

Minimal requirements protected:

- MFR10: grounded answering;
- MFR11: support-aware response behavior.

At minimum, the system should determine or approximate:

1. whether the question is in MVP scope;
2. whether the corpus contains enough evidence to answer;
3. whether the evidence is complete, partial, ambiguous, conflicting, or missing;
4. whether provenance is inspectable enough for the response;
5. whether the correct behavior is answer, narrow, qualify, surface ambiguity, abstain, or state a limitation.

This is the central trust-control point in the question-answering lifecycle.

Control invariant:

> The existence of related evidence is not sufficient justification for a direct answer.

Failure protected against:

- unsupported answers;
- partially supported answers presented as complete;
- failed abstentions;
- ambiguity being hidden behind a fluent response.

### 4.5 Answer or Abstain

The system emits the response selected by the support decision.

Minimal requirements protected:

- MFR10: grounded answering;
- MFR11: support-aware response behavior.

The response may be:

- a direct answer when support is sufficient;
- a narrowed answer when only part of the question is supported;
- a qualified answer when support is partial or weak;
- an ambiguity-aware answer when sources are unclear or conflicting;
- an abstention when the corpus does not support a reliable answer;
- an explicit limitation when the request is outside MVP capability.

Control invariant:

> Response strength must match evidence strength.

Failure protected against:

- overconfident unsupported answers;
- speculative answers disguised as corpus findings;
- unnecessary refusal when sufficient evidence exists.

### 4.6 Render Provenance

If the system answers, it renders provenance derived from the evidence actually used.

Returned provenance should be no more precise than the pipeline can support. Coarse real provenance is better than precise false provenance.

Minimal requirements protected:

- MFR12: evidence rendering.

For MVP, provenance rendering should preserve the minimum expected source trail by source type:

- PDF: document identity plus page where recoverable;
- Markdown: document identity plus section or heading path where recoverable;
- mixed-format synthesis: usable provenance for each materially contributing source.

Control invariant:

> Provenance should explain why the answer is inspectable, not merely decorate the answer with source-looking references.

Failure protected against:

- fabricated pages, sections, anchors, or documents;
- citations that do not support the material claim;
- provenance too weak for user verification.

---

## 5. Evidence Handoff Contract

The evidence-preparation lifecycle hands the question-answering lifecycle an active queryable corpus of evidence units.

That handoff must preserve, at minimum:

| Property | Why it matters |
|---|---|
| Corpus membership | Prevents cross-corpus contamination. |
| Stable document identity | Allows evidence to resolve back to a source artifact. |
| Source type | Enables source-specific provenance and scope behavior. |
| Text content | Provides the material available for retrieval and answering. |
| Section or heading path, where recoverable | Preserves local meaning and source navigation for structured documents. |
| Page or source location, where recoverable | Enables inspectable PDF and source-location provenance. |
| Local context | Lets users and evaluators inspect what was actually retrieved. |
| Traceability status | Allows degraded evidence to be handled honestly. |

If these properties are missing or degraded, the query path should not silently compensate by guessing. It should reduce answer strength, expose limitations, or abstain.

---

## 6. Evidence Flow Invariant

The same evidence path should support retrieval, answer decision, and provenance rendering.

```text
Retrieved evidence
  -> evidence set used for support decision
  -> answer content
  -> rendered provenance
```

The system should avoid a split where one set of text is used to answer and a different or reconstructed set of references is used for provenance.

This protects the core evidence invariant:

> Material claims should be traceable to the evidence that actually supported them.

When the system cannot maintain that invariant, it should qualify, narrow, abstain, or state a limitation.

---

## 7. Trust-Control Points

The lifecycle contains five trust-control points.

### 7.1 Structure Preservation

The system preserves enough document hierarchy and boundaries for retrieved units to remain meaningful and inspectable.

Primary failure prevented:

- ingestion or structure failure visible in answer quality.

### 7.2 Traceability

The system preserves stable mappings from evidence units back to source documents and coarse source locations.

Primary failures prevented:

- missing provenance;
- incorrect provenance;
- fabricated source support.

### 7.3 Scope Honesty

The system identifies when a question depends on unsupported inputs, unsupported question types, or external knowledge outside the corpus.

Primary failure prevented:

- answering out-of-scope questions as though they were corpus-supported.

### 7.4 Support Decision

The system decides whether the evidence justifies a direct answer, qualified answer, ambiguity handling, or abstention.

Primary failures prevented:

- unsupported answer;
- failed abstention;
- partially supported answer presented as complete.

### 7.5 Provenance Sufficiency

The system checks whether the provenance it can return is sufficient for the answer type and source type.

Primary failures prevented:

- provenance too weak to inspect;
- precise but false source references;
- answer claims that users cannot verify.

---

## 8. Degraded States

The lifecycle should make degraded states visible enough that downstream behavior can remain honest and acceptance-testable.

Required degraded-state behavior:

| Degraded state | Expected behavior |
|---|---|
| Text extracted, but structure weak | Weak structure must reduce section-level precision. |
| PDF text available, but page mapping weak | Weak page mapping must reduce page-level precision. |
| Evidence relevant, but insufficient | Insufficient evidence must trigger narrowing, qualification, or abstention. |
| Evidence conflicting | Conflicting evidence must be surfaced rather than collapsed into one unsupported answer. |
| Question requires unsupported MVP capability | Unsupported MVP capability must produce explicit limitation language. |
| Provenance unavailable for a claim | Unavailable provenance must prevent the claim from being presented as corpus-supported. |

Degraded does not always mean unusable. It means the response must respect the weaker evidence or weaker provenance state.

---

## 9. Relationship To Adjacent Documents

This lifecycle document is intentionally narrower than the MVP spec and broader than implementation docs.

It should be read as the bridge between:

- product-level trust promises;
- retrieval hierarchy design;
- support-state behavior;
- implementation architecture;
- evaluation and failure analysis.

It should not duplicate detailed product scope from the MVP spec or detailed algorithm choices from implementation documents.

When documents disagree:

- MVP scope and guarantees are resolved in `docs/evergreen/mvp.md`.
- Structural hierarchy is resolved in `docs/evergreen/retrieval-hierarchy.md`.
- Current runtime truth is resolved in `docs/evergreen/architecture.md`.
- Support-state behavior is resolved in `docs/delivery/eval-support-semantics.md`.
- Failure definitions and review workflow are resolved in `docs/evergreen/first-tier-failures.md`.

---

## 10. Minimum Readiness And Diagnostic Trace Surface

This document does not define a full observability plan or production observability commitment. Lifecycle traceability is a readiness and control concept: the system must preserve enough inspectable state to determine whether the MVP trust contract held.

At minimum, the system should make it possible to inspect, evaluate, or diagnose:

- corpus and document identifiers involved in a query;
- query text;
- retrieved evidence units and scores;
- evidence units selected for the support decision;
- source type slice: `pdf`, `markdown`, or `mixed`;
- answer text;
- answer versus abstain decision;
- support-state estimate or decision, where available;
- returned provenance payload;
- whether the request crossed a known unsupported scope boundary;
- ingestion or provenance degradation flags relevant to the response.

This trace surface is not a production observability commitment. It is the minimum diagnostic surface needed to evaluate whether the lifecycle preserved the MVP trust contract.

---

## 11. Deferred Lifecycle Concerns

The MVP lifecycle does not require a full publication, mutation, audit, or version-history system.

A later hardening pass may define lifecycle behavior such as:

```text
Admit -> Re-ingest / Supersede -> Rebuild Queryable State -> Withdraw from Active Retrieval
```

That lifecycle is deferred.

This deferral means the current lifecycle should not be read as promising:

- durable version history;
- document supersession semantics;
- active withdrawal guarantees;
- audit-grade publication controls;
- collaborative corpus management.

The deferred direction is recorded only because future mutation behavior must preserve the same evidence invariant: the query path should only retrieve evidence whose active status, source identity, and provenance are known.

---

## 12. Summary

This document defines the conceptual evidence flow behind the MVP’s trust contract.

The evidence-preparation lifecycle turns uploaded source documents into traceable, queryable evidence units.

The question-answering lifecycle retrieves those units, forms an evidence set, decides what the evidence supports, and then answers, qualifies, surfaces ambiguity, abstains, or states a limitation.

The central invariant is:

> The question path must not invent what the document path failed to preserve.

When structure, traceability, support, or provenance is weak, the system should degrade honestly rather than answer with unsupported confidence or fabricated precision.

---

## 13. References

- `docs/evergreen/mvp.md`
- `docs/evergreen/functional-requirements.md`
- `docs/evergreen/retrieval-hierarchy.md`
- `docs/evergreen/architecture.md`
- `docs/delivery/eval-support-semantics.md`
- `docs/evergreen/first-tier-failures.md`
