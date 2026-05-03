# Old MVP Delivery Loop for the First Trustworthy QA Slice

- **Status:** Superseded historical guidance
- **Scope:** Historical MVP workflow notes
- **Last updated:** 2026-03-23
- **Current docs:** `docs/evergreen/mvp.md`, `docs/delivery/architecture.md`, `docs/delivery/design-notes.md`, `docs/delivery/evals.md`, `docs/delivery/runbooks.md`

**Authority note:** This file is retained as old workflow context only. It does
not define current product scope or current repo truth. Canonical product scope
lives in `docs/evergreen/mvp.md`; current implementation shape lives in
`docs/delivery/architecture.md`.

---

## 1. Purpose and scope

This document captured an earlier delivery workflow for the first trustworthy QA slice of the MVP.

The goal is not to restate the full conceptual model of a document-grounded RAG system. The goal is to describe the smallest practical loop that protects the MVP trust contract and helps the repo earn durable architecture from validated behavior.

The workflow was intentionally narrow:

- it is organized around one design-driving story;
- it treats **supported lookup with inspectable provenance** as the first delivery slice;
- it uses evaluation pressure to decide what to change next;
- it leaves broader architecture and product expansion for later promotion.

This document does not broaden MVP scope. The current product target is defined
in `docs/evergreen/mvp.md`.

Markdown-first implementation or validation is now captured as `mvp-0`, the
Markdown-only walking skeleton in `docs/evergreen/mvp.md`.

---

## 2. Delivery principle

The workflow is model-first, eval-first, and current-state aware.

That means:

- start from the user-visible trust contract, not from desired module boundaries;
- define the minimum invariants that must survive implementation changes;
- use a small eval pack to pressure those invariants early;
- treat implementation as an instrument for learning where the real seams are;
- promote only the behavior and boundaries that survive repeated validation pressure.

The active repo no longer treats Markdown ingestion and evidence preparation as
hypothetical. Retrieval, support assessment, answer generation, and citation
rendering remain target behavior for the walking skeleton until
`docs/delivery/architecture.md` records them as implemented repo truth. The
remaining workflow value is deciding which slice to pressure next, which gaps to
close now, and which internal patterns have earned promotion into evergreen
documentation.

---

## 3. Design-driving story and trust contract

The workflow was anchored in this design-driving story:

> A user asks a focused question over a bounded corpus and receives either a grounded answer with inspectable source references or a clear statement that the corpus or MVP scope does not support the answer.

For workflow purposes, that story implies five non-negotiable trust guarantees:

1. answers stay within corpus support;
2. weak, partial, or conflicting support is handled honestly;
3. provenance is inspectable at useful source granularity;
4. provenance is never fabricated or overstated;
5. MVP scope boundaries are stated explicitly instead of being hidden behind fluent answers.

The first slice is intentionally narrower than the whole story:

- question family: supported lookup;
- answer mode: direct answer only when evidence really supports it;
- provenance target: usable document plus section path for Markdown, and document plus page when PDF support is involved and only coarse provenance is recoverable;
- primary early pressure: trustworthy answer emission and trustworthy provenance.

This slice is narrow on purpose. It is the smallest loop that can validate the trust contract without forcing premature decisions about the rest of the product.

---

## 4. First slice and current-system alignment

The first slice remains the organizing lens, but the repo has since been
re-scoped around a smaller Markdown-only walking skeleton.

Today, current repo truth lives in `docs/evergreen/mvp.md` and
`docs/delivery/architecture.md`. This workflow does not override them.

Those current docs establish that the repo currently has:

- Markdown upload into a bounded corpus;
- stable document identity;
- Markdown parsing into sections and passages;
- passage embedding generation;
- in-memory document and embedding persistence;
- document inspection surfaces;
- Docker and host-side developer commands.

Because of that, the active workflow is not "build a broad QA system from
scratch." The workflow is:

1. choose the next trust-critical slice to pressure;
2. verify how the current implemented seams and target query seams support that slice;
3. change only the minimum implementation needed for the target cases;
4. use eval failures, inspection output, and later trace or citation output to decide whether the model or the implementation needs adjustment;
5. promote only the seams that hold under that pressure.

For now, the preferred slice remains the Markdown-only walking skeleton because
it exercises the core trust contract without dragging in every deferred problem
at once.

---

## 5. Required invariants

This workflow keeps only the invariants that are necessary for the first slice and the next iteration loop.

### 5.1 Stable document identity

Documents need stable identity across ingestion, retrieval, answer generation, review, and evaluation.

### 5.2 Source-type discipline

The system must preserve whether the source is Markdown or PDF. Generic internal terms such as `document` do not widen supported inputs beyond MVP scope.

### 5.3 Recoverable provenance

The system must preserve enough source location information for useful inspection:

- Markdown should preserve document plus section path when recoverable.
- PDF should preserve document plus page, plus section-like context when recoverable.
- If precision is uncertain, coarse real provenance is better than false precision.

### 5.4 Raw-text traceability

Retrieved and cited evidence must remain traceable to the normalized or extracted source text rather than being reconstructed from answer text alone.

### 5.5 Explicit answerability and support gating

The answer path must include an explicit support or answerability decision rather than allowing fluent output to stand in for proof.

Support-state meanings, decision procedure, and allowed answer behavior should be
promoted into active delivery or evergreen docs before they are treated as
current repo policy.

### 5.6 No fabricated provenance or unsupported completion

The workflow must prefer narrower answers, qualification, or abstention over unsupported completion.

Failure labels and scenario classes should be defined in active evaluation docs
before they are treated as current repo policy.

---

## 6. Delivery loop

The operating loop for this workflow is procedural.

### Step 1 - Freeze the eval pack and target failures

Pick a small case pack that matches the slice being pressured. For the first trustworthy QA slice, that means supported-lookup cases with explicit provenance expectations and a small set of target failures.

Keep the pack small and diagnostic. Prefer failure-first cases that can explain
whether the issue is retrieval, support assessment, answer generation,
provenance, or scope leakage.

### Step 2 - Define or confirm provenance and retrieval-unit payloads

Before changing code, confirm the minimum payloads needed to preserve trust in the slice:

- document identity;
- source type;
- section path or page locator when recoverable;
- retrieval-unit linkage back to source text;
- enough citation payload to inspect what supported the answer.

Do not expand the model beyond what the target cases require.

### Step 3 - Verify current seams against the slice

Check how the existing ingestion, evidence preparation, inspection surfaces, and
API support the target loop.

In the current repo, this means verifying behavior against
`docs/delivery/architecture.md` instead of assuming greenfield design space. The
question is not "what architecture should exist?" The question is "what part of
the implemented system already satisfies the slice, what part needs adaptation,
and what part should remain deferred?"

### Step 4 - Implement only the minimum gap

Make the smallest implementation change that improves the target cases without prematurely redesigning unrelated subsystems.

This favors extending existing document, embedding, provenance, and inspection
seams where possible instead of introducing broad new abstractions up front.

### Step 5 - Run eval and inspect traces, citations, and review surfaces

Run the targeted eval or manual review loop for the chosen slice.

Use the repo's existing API responses, document inspection output, and local
review surfaces to inspect:

- whether the right evidence was retrieved;
- whether provenance remained usable;
- whether the answer behavior matched the support state;
- whether the failure is upstream, downstream, or a trust-policy problem.

### Step 6 - Classify failures against canonical semantics

Interpret the result using active evaluation notes rather than ad hoc local
wording.

If the system failed, name the failure in shared terms. If the system passed, confirm that it passed for the right reason rather than because the eval pack was too weak.

### Step 7 - Refine the model or the implementation

Use the failure evidence to decide whether the problem is:

- a weak or incorrect invariant,
- a bad payload or boundary choice,
- an implementation defect inside an already-valid seam,
- or a deferred concern that should stay deferred.

Only then adjust the workflow inputs or the code.

### Step 8 - Promote only validated seams

After repeated pressure, promote stable process rules, interfaces, or architectural seams into evergreen docs when they have clearly earned that status.

Do not treat convenience abstractions from one prototype pass as durable architecture.

---

## 7. Deferred now

This workflow intentionally does not settle the following in the first trustworthy QA slice:

- broad bounded-context expansion beyond what current repo seams have already earned;
- service decomposition or multi-service topology;
- deployment topology decisions beyond the current local runtime and operator workflows;
- advanced versioning or promotion policy for every internal contract;
- PDF hardening beyond the current coarse provenance floor;
- broad synthesis or exhaustive reconciliation guarantees;
- large taxonomy expansion when a smaller failure-first eval pack is enough.

Deferring these is part of the workflow, not a missing section. They should be revisited only when failure pressure or stable usage proves they matter.

---

## 8. Promotion criteria and references

Promote a process rule, seam, or contract into evergreen docs only when it satisfies all of the following:

- it survives multiple eval or review cycles;
- it protects one of the trust-critical invariants;
- it is implemented repo truth rather than a one-off draft preference;
- it reduces ambiguity about product scope, current architecture, or stable interfaces.

Keep this split clear:

- `docs/evergreen/mvp.md` owns durable product scope;
- `docs/delivery/architecture.md` owns current implementation truth;
- `docs/delivery/evals.md` owns active evaluation notes until they are promoted.

This structure is intended to make later evergreen promotion easier. If stable
parts of this old workflow become durable repo policy, they should move into
active evergreen or delivery docs instead of being referenced from this
historical file.

Reference first rather than restating:

- `docs/evergreen/mvp.md` for scope and product promise;
- `docs/delivery/architecture.md` for current implementation truth;
- `docs/delivery/design-notes.md` for current delivery design notes;
- `docs/delivery/evals.md` for active evaluation notes;
- `docs/delivery/runbooks.md` for operating guidance.
