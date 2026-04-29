# MVP Spec: Question-Answering Service over PDF Books and Markdown Files

## 1. Overview

The MVP is a document question-answering and evidence-inspection service for engineers working with a bounded collection of user-uploaded text-based PDFs and Markdown files. It helps users ask focused natural-language questions across technical books, manuals, specs, notes, and internal documents without manually searching, skimming, and reconciling source material.

The service is trust-first: answers must be grounded in retrieved corpus evidence, include inspectable source references for material claims, and honestly narrow, qualify, surface ambiguity, state limitations, or abstain when the corpus does not provide enough support. The MVP proves a constrained mixed-format corpus can become a trustworthy queryable knowledge source; it is not a general research agent, full document-intelligence platform, OCR system, rich PDF understanding system, or external web retrieval tool.

### 1.1 Document Authority

This document is the governing source for MVP product scope, supported inputs, product promise, user-facing trust guarantees, non-goals, and explicit deferrals.

Authority boundaries:

- `docs/evergreen/mvp.md` owns MVP scope, supported inputs, trust guarantees, non-goals, and explicit deferrals.
- `docs/evergreen/functional-requirements.md` owns the 12 minimal functional requirements and acceptance criteria.
- `docs/evergreen/lifecycle-and-evidence-flow.md` owns conceptual lifecycle controls that protect the MVP trust contract.
- `docs/evergreen/architecture.md` owns current implementation truth and earned internal seams.
- Delivery, workflow, workstream, and architecture documents may generalize internal concepts for modeling or implementation, but they do not broaden MVP product scope.

If another document implies broader MVP behavior than this document allows, this document wins for product scope. Broader concepts remain implementation detail, future work, or non-MVP unless explicitly promoted here.

Acceptance criteria, lifecycle controls, architecture seams, and evaluation language must be interpreted through this boundary. They must not add OCR, rich PDF layout reconstruction, image, figure, chart, or table-centric understanding, collaboration, version history, external web retrieval, production observability, or other deferred capabilities to MVP scope.

## 2. Problem Statement

Engineers often rely on long-form technical materials such as books, manuals, specifications, design notes, and internal Markdown documents. These materials are useful, but they are difficult to query as a single knowledge source.

Manual search and skimming are slow. Relevant information may be spread across multiple files, chapters, or sections, creating repeated search loops, reading overhead, and decision risk when users cannot quickly determine what the corpus says or where it says it.

LLM-based document QA systems, usually implemented with retrieval-augmented generation, can reduce some of this friction by retrieving relevant passages and generating natural-language answers.

However, basic RAG-style implementations often still do not reliably provide:

- grounded answers based only on the uploaded corpus;
- synthesis across related documents;
- source references that users can inspect;
- enough evidence detail for users to verify why an answer was produced;
- clear behavior when the corpus does not support an answer.

The MVP addresses this problem by turning a focused collection of text-based PDFs and Markdown files into a question-answerable corpus with inspectable evidence.

## 3. Jobs To Be Done
### Primary Job

When an engineer needs to answer a focused technical question from a bounded set of uploaded PDFs and Markdown documents, they hire the product to produce a corpus-grounded answer with inspectable evidence, so they can make a confident technical decision without manually searching, skimming, and reconciling source material.
### Supporting Jobs

To complete the primary job, the product must help the user:

- **Find** relevant support even when it is spread across multiple files, chapters, sections, or notes.
- **Synthesize** a concise answer from the available corpus evidence.
- **Verify** the answer by exposing inspectable source evidence behind it.
- **Navigate** from the answer back to the relevant source locations.
- **Qualify** the answer by distinguishing between fully supported, partially supported, ambiguous, conflicting, and unsupported evidence.

### Product implication

The JTBD implies that the MVP should not optimize only for answer fluency. It should optimize for **trustable answer workflow**.

## 4. MVP Product Promise

The MVP promises a trustable question-answering workflow over a bounded uploaded corpus.

For every user question, the product must follow this response contract:

1. If corpus evidence is sufficient, answer from that evidence and provide inspectable source references for material claims.
2. If evidence is partial, weak, ambiguous, or conflicting, answer narrowly, qualify the response, and surface the uncertainty.
3. If the corpus does not support the question or the request is outside MVP scope, abstain or state the limitation explicitly.

## 5. Primary Use Cases

The MVP supports a small set of question patterns over a bounded corpus of supported PDFs and Markdown files. These use cases describe the primary ways users interact with the corpus; the shared response contract is defined in the MVP Product Promise above.

Unless otherwise stated, every use case follows that promise rather than restating the grounding, provenance, and abstention rules locally.

### 5.1 Factual lookup

The user asks for a specific fact, definition, requirement, or statement expected to appear in the uploaded corpus.

Examples:

- “What is X?”
- “How does this book define Y?”
- “What are the requirements for Z?”

The expected interaction is a concise answer that helps the user avoid manually finding and reading the relevant passage.

### 5.2 Localized explanation

The user asks for an explanation of a concept, process, or section-level topic discussed in one part of the corpus.

Examples:

- “Explain the retry strategy described in these notes.”
- “Summarize the chapter’s explanation of backpropagation.”

The expected interaction is a focused explanation that preserves the local context instead of turning into a general-purpose tutorial.

### 5.3 Basic synthesis

The user asks what one or more uploaded documents say about a topic that may be discussed across multiple sources.

Examples:

- “What do these documents say about vector databases?”
- “Synthesize the guidance on caching from Book A and my notes.”

The expected interaction is a compact synthesis across relevant retrieved material. The MVP does not promise exhaustive compare-and-contrast behavior across every possible viewpoint in the corpus.

### 5.4 Source navigation

The user asks where a topic is discussed or which source locations are relevant.

Examples:

- “Where is tokenization discussed?”
- “Which book or section covers distributed transactions?”
- “Show the passages relevant to this question.”

The expected interaction is a navigational response that helps the user jump to relevant documents, pages, sections, or passages.

### 5.5 Unsupported, partial, or ambiguous questions

The user asks a question that the active corpus does not fully answer, answers only in part, or answers differently across sources.

Examples:

- “What is the recommended production configuration?”
- “Do these documents agree on the retry policy?”
- “What does the corpus say about pricing?”

The expected interaction is a response that helps the user understand the support state of the corpus, not just the apparent answer.

## 6. Core User Flow

The MVP user-facing flow is the simplest path by which a user turns a bounded document collection into corpus-grounded answers with inspectable evidence.

1. **Create a bounded corpus**

   The user uploads a focused set of supported documents: text-based PDFs and Markdown files.

2. **Wait until the corpus is queryable**

   The system processes the uploaded documents and makes them available as a searchable, question-answerable corpus.

3. **Ask a corpus-scoped question**

   The user asks a natural-language question about the uploaded corpus.

4. **Receive a grounded response**

   The system answers from corpus evidence when support is sufficient. When support is partial, conflicting, weak, missing, or outside MVP scope, the system narrows, qualifies, surfaces ambiguity, abstains, or states the limitation.

5. **Inspect the evidence**

   The user can inspect the source documents and source locations behind the response.

6. **Decide whether to trust or investigate further**

   Based on the answer, qualification, abstention, limitation, and evidence, the user decides whether the corpus sufficiently answers the question or whether further source inspection is needed.

The flow preserves the MVP invariants: bounded corpus, corpus-grounded answering, inspectable provenance, honest uncertainty, no fabricated source support, and explicit scope boundaries.
## 7. Out of Scope / Explicit Deferrals

The MVP is intentionally limited to a trustable question-answering workflow over a focused, user-uploaded corpus of text-based PDFs and Markdown files.

This section defines what the MVP does **not** promise. Functional requirements define the minimum required system behaviors, and lifecycle/evidence-flow documents define how the trust contract is preserved internally. The exclusions below prevent adjacent capabilities from being interpreted as part of MVP scope.

### 7.1 Input and parsing exclusions

The MVP does not support:

- scanned PDFs or documents that require OCR;
- image-heavy PDFs where the answer depends on visual content;
- rich PDF layout reconstruction;
- table-centric parsing or table-centric question answering;
- figure, diagram, image, or chart understanding;
- complex footnote, sidebar, margin annotation, or scholarly apparatus handling;
- exact scholarly citation formatting.

The MVP may preserve table-like text, code blocks, headings, or other recoverable structure when available, but preserving such text does not mean specialized table, layout, image, or citation understanding is in scope.

### 7.2 Retrieval and indexing deferrals

The MVP does not require:

- lexical search as a first-class retrieval layer;
- advanced hybrid retrieval tuning;
- sophisticated reranking pipelines beyond basic MVP needs;
- guaranteed exhaustive retrieval across very large corpora;
- very large corpus optimization.

The MVP requires retrieval that is good enough to support the defined question-answering workflow over a bounded corpus, with evidence that remains traceable and inspectable.

### 7.3 Derived knowledge deferrals

The MVP does not create or maintain derived knowledge products such as:

- stored summaries as first-class artifacts;
- synthetic questions;
- entity extraction or entity resolution systems;
- graph or entity-relation extraction;
- automatic knowledge graph generation;
- precomputed derived knowledge views beyond retrieval-ready evidence units.

The MVP answers from retrieved corpus evidence at query time rather than promising a separate derived knowledge layer.

### 7.4 Product and platform deferrals

The MVP does not include:

- arbitrary enterprise search;
- live web retrieval or external-world research;
- cloud-drive connectors or incremental background sync;
- collaboration, sharing, or team workspace workflows;
- collaborative editing;
- fine-tuning;
- workflow automation;
- billing, quotas, or advanced admin controls;
- complex access control, multi-tenant permissions, or ACL enforcement beyond simple user/workspace ownership boundaries;
- production-grade observability, operational dashboards, audit systems, or full production hardening.

These may be future platform capabilities, but they are not required to validate the MVP promise.

### 7.5 Question classes outside MVP

The MVP does not promise reliable answers for:

- questions requiring external-world knowledge not present in the uploaded corpus;
- questions whose answer depends mainly on tables, figures, diagrams, charts, or images;
- questions requiring exhaustive compare-and-contrast across all possible relevant sources;
- questions requiring deliberate source diversification beyond basic synthesis;
- questions requiring guaranteed exhaustive retrieval over very large corpora;
- requests for exact scholarly citation formatting.

For these cases, the expected MVP behavior is to state the limitation, narrow the answer to what the corpus supports, surface uncertainty, or abstain.

### 7.6 Boundary statement

Architecture, lifecycle, retrieval, and workflow documents may define internal models or implementation approaches, but they do not broaden MVP scope on their own.

The MVP remains bounded by:

- supported inputs: text-based PDFs and Markdown files;
- supported corpus model: a focused uploaded corpus scoped to a user or workspace;
- supported answer behavior: corpus-grounded answers, qualified answers, ambiguity handling, explicit limitations, or abstention;
- supported evidence behavior: inspectable provenance based on recoverable document identity, source type, page, section, heading, or source-location metadata.

## 8. Functional Requirements

The canonical MVP functional requirements are the 12 minimal functional requirements in `docs/evergreen/functional-requirements.md`. That document owns the acceptance criteria for supported uploads, bounded corpus creation, stable source identity, processing status, text extraction, minimum provenance, traceable evidence units, corpus retrieval, evidence handoff, grounded answering, support-aware response behavior, and evidence rendering.

This section does not duplicate those criteria or broaden MVP scope.

## 9. Non-Functional Requirements / Trust Requirements

The MVP is trust-first. A fluent answer is not sufficient if it violates the evidence contract.

These non-functional requirements define the minimum quality attributes required for a trustworthy MVP. They do not define implementation architecture, full production observability, enterprise security, collaboration, version history, or production hardening.

### NFR1. Groundedness

Answers must remain within what the active uploaded corpus supports. The system must not import model prior knowledge and present it as corpus-backed.

### NFR2. Evidence-strength calibration

Response strength must match evidence strength.

When evidence is sufficient, the system may answer directly.
When evidence is partial, weak, ambiguous, conflicting, missing, or outside MVP scope, the system must narrow, qualify, surface ambiguity, abstain, or state the relevant limitation.

### NFR3. Provenance inspectability

Material answer claims must be inspectable through source references.

Minimum MVP provenance expectations are:

| Source type | Minimum MVP provenance expectation |
|---|---|
| PDF | Document identity plus page where recoverable |
| Markdown | Document identity plus section or heading path where recoverable |
| Mixed-format synthesis | Usable provenance for each materially contributing source |

### NFR4. Provenance integrity

The system must not fabricate documents, pages, sections, headings, anchors, source locations, or source support.

Coarse real provenance is better than precise false provenance.

### NFR5. Scope honesty

The system must not treat unsupported capabilities as supported.

For questions involving unsupported input types, unsupported question types, or external knowledge outside the active corpus, the system must state the limitation rather than answer speculatively.

### NFR6. Degraded-state safety

The system must handle degraded evidence states honestly.

Examples:

- weak structure must reduce section-level precision;
- weak PDF page mapping must reduce page-level precision;
- insufficient evidence must trigger narrowing, qualification, or abstention;
- conflicting evidence must be surfaced rather than collapsed into a single unsupported answer;
- unavailable provenance must prevent a claim from being presented as corpus-supported.

### NFR7. Minimum diagnostic traceability

The MVP must make it possible to inspect or log enough information to evaluate trust failures.

At minimum, this includes:

- query text;
- corpus and document identifiers involved in the query;
- retrieved evidence units and scores;
- evidence selected for answer/support decision;
- answer text;
- answer versus abstain decision;
- support-state estimate or decision where available;
- returned provenance payload;
- source type slice: `pdf`, `markdown`, or `mixed`;
- whether the request crossed a known unsupported scope boundary;
- ingestion, structure, or provenance degradation flags relevant to the response.

This is not a full production observability commitment. It is the minimum diagnostic surface needed to evaluate whether the MVP preserved the evidence contract.

## 10. MVP Failure Model and Evaluation

The MVP should be evaluated against a compact set of first-tier failures that directly protect the product promise.

### 10.1 Support states

Each evaluated question should first be classified by what the corpus actually supports:

| Support state | Expected behavior |
|---|---|
| `SUPPORTED` | Answer directly and cite inspectable support |
| `PARTIALLY_SUPPORTED` | Answer narrowly or qualify unsupported portions |
| `UNSUPPORTED_IN_CORPUS` | Abstain or state lack of support |
| `UNSUPPORTED_QUESTION_TYPE` | State the MVP limitation explicitly |
| `AMBIGUOUS_OR_CONFLICTING` | Surface ambiguity, conflict, or source-specific differences |

### 10.2 First-tier MVP failures

The MVP should track these primary failure labels:

| Label | Failure                                                  | Why it matters                                                           |
| ----- | -------------------------------------------------------- | ------------------------------------------------------------------------ |
| `U1`  | Unsupported answer                                       | The system states material claims not supported by the corpus.           |
| `U2`  | Partially supported answer presented as complete         | The system overstates what the evidence supports.                        |
| `A1`  | Wrong abstention                                         | The system refuses or narrows despite sufficient support.                |
| `A2`  | Failed abstention                                        | The system answers when it should abstain, narrow, or surface ambiguity. |
| `P1`  | Provenance missing or too weak to inspect                | The user cannot verify the answer with reasonable effort.                |
| `P2`  | Incorrect provenance                                     | The system cites sources or locations that do not support the answer.    |
| `I1`  | Ingestion or structure failure visible in answer quality | Normalization damage harms retrieval, answering, or provenance.          |
| `S1`  | Scope-boundary failure                                   | The system answers an out-of-scope question as if it were supported.     |

Detailed definitions, severity, reviewer workflow, and remediation guidance belong in the first-tier failure specification rather than this MVP spec.

### 10.3 Evaluation dataset requirements

A practical MVP evaluation set should include:

- direct PDF factual lookup;
- direct Markdown factual lookup;
- localized explanation;
- mixed-format synthesis;
- source navigation;
- partial-support questions;
- unsupported-in-corpus questions;
- ambiguous or conflicting-source questions;
- out-of-scope table, figure, chart, image, or external-world questions;
- malformed or weakly structured input cases.

A practical initial evaluation target is **50 to 100 annotated questions**, with results sliced by source type, question class, support state, provenance expectation, and primary failure label.
