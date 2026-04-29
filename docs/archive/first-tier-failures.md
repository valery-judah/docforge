# MVP Critical Failure Specification for Source-Grounded QA over PDF and Markdown

## 1. Purpose

This document defines the **critical failure model** for the MVP question-answering system.

It exists to answer a narrow engineering question:

> Which failure modes must be measured, reviewed, and reduced first in order for the MVP to satisfy its trust contract?

The intent is not to model every possible RAG defect. The intent is to establish a compact, implementation-relevant failure set that is sufficient to:

1. protect the MVP trust contract,
2. guide evaluation design,
3. prioritize engineering work,
4. standardize reviewer labeling, and
5. define launch-gate behavior for the first version.

This specification is intentionally stricter than a general product-quality checklist. A response can be fluent, helpful-looking, or directionally relevant and still fail this spec if it violates groundedness, provenance, abstention, or scope honesty.

---

## 2. Product contract this failure model protects

The MVP is a bounded document question-answering and evidence-inspection service over **user-uploaded text-based PDFs and Markdown files**. Its core promise is not generic intelligence. Its core promise is that a user can ask a question over an uploaded corpus, receive an answer grounded in that corpus, and inspect the evidence behind the answer.

The failure model in this document protects five non-negotiable properties:

1. **Grounded answering**: answers must remain within what the uploaded corpus supports.
2. **Honest uncertainty**: when support is partial, conflicting, weak, or missing, the system must qualify, narrow, or abstain.
3. **Inspectable provenance**: the user must be able to inspect which document and which coarse source location informed the answer.
4. **No fabricated provenance**: the system must not invent pages, sections, anchors, or source support.
5. **Honest scope boundaries**: questions outside MVP capability must be handled explicitly rather than answered as if they were supported.

These properties are the product contract for MVP and therefore the basis for the primary failure selection in this document.

---

## 3. Why these 8 failures are the MVP minimum

The broader rubric includes additional operational and diagnostic labels. Those remain useful, but they are not all equally suitable as **first-class MVP failures**.

For Version 1, the primary evaluation surface should be limited to the smallest set of failures that directly determine whether the system is trustworthy and usable for its intended task.

The selected failures are:

- `U1` — Unsupported answer
- `U2` — Partially supported answer presented as complete
- `A1` — Wrong abstention
- `A2` — Failed abstention
- `P1` — Provenance missing or too weak to inspect
- `P2` — Incorrect provenance
- `I1` — Ingestion or structure failure visible in answer quality
- `S1` — Scope-boundary failure

Together, these 8 failures cover the entire trust loop:

- whether the answer stayed inside support,
- whether the system chose to answer versus abstain correctly,
- whether the user can inspect the support,
- whether ingestion preserved enough structure to make grounding possible, and
- whether the system stays honest about MVP capability limits.


## 5. Required concepts and definitions

### 5.1 Support states

Every evaluated question should first be classified into one support state:

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `UNSUPPORTED_IN_CORPUS`
- `UNSUPPORTED_QUESTION_TYPE`
- `AMBIGUOUS_OR_CONFLICTING`

These support states are prior to any system output. They define what the corpus actually supports.

### 5.2 Correct response policy by support state

The correct high-level system behavior is:

| Support state | Expected behavior |
|---|---|
| `SUPPORTED` | Answer directly and cite inspectable support |
| `PARTIALLY_SUPPORTED` | Answer narrowly or qualify the unsupported portion |
| `UNSUPPORTED_IN_CORPUS` | Abstain or state lack of support |
| `UNSUPPORTED_QUESTION_TYPE` | State the MVP limitation explicitly |
| `AMBIGUOUS_OR_CONFLICTING` | Surface ambiguity or qualify by source |

### 5.3 Minimum provenance expectation

The minimum provenance required for a question should be one of:

- `document_only`
- `document_and_page`
- `document_and_section`
- `document_page_and_section_if_available`

For MVP:

- **PDFs** commonly require at least document identity plus page.
- **Markdown** commonly requires document identity plus section path.
- **Mixed-format synthesis** often requires one usable provenance record per contributing source.

### 5.4 Trust outcome model

Each run should ultimately resolve to one of:

- `TRUSTWORTHY`
- `BORDERLINE`
- `NOT_TRUSTWORTHY`

The 8 failures in this document are the principal causes of `BORDERLINE` or `NOT_TRUSTWORTHY` outcomes.

---

## 6. Severity model

The selected failures should use the following default severity policy.

| Failure | Default severity | Rationale |
|---|---:|---|
| `U1` | High | Direct trust breach; user may believe unsupported claims |
| `U2` | High / Medium | High when confident, Medium when visibly qualified but still overstated |
| `A1` | Medium | Usefulness failure; less dangerous than unsupported answering |
| `A2` | High | System answered when it should have narrowed or abstained |
| `P1` | Medium | User cannot inspect support reliably |
| `P2` | High | False provenance is a direct trust-contract breach |
| `I1` | Medium / High | Impairs answerability and provenance; High if systematic |
| `S1` | High | Out-of-scope behavior presented as grounded |

Severity may be elevated when the answer is confident, specific, or likely to drive a concrete user decision.

---

## 7. Evaluation priority order

The system should be optimized in this order:

1. prevent unsupported answers and false provenance,
2. ensure correct abstention and scope handling,
3. ensure provenance is inspectable when answers are given,
4. reduce wrong abstentions,
5. improve structure preservation when it materially affects answer quality.

In practice, the defect priority order should be:

1. `U1`, `A2`, `P2`, `S1`
2. `U2`, `P1`
3. `A1`
4. `I1`

This does **not** mean `I1` is unimportant. It means it is usually an enabling defect rather than the first user-visible trust break.

---

## 8. Failure specification template

Every primary failure in this document is defined using the same fields:

- **Definition**: what the failure is.
- **Contract violated**: which MVP guarantee it breaks.
- **Trigger conditions**: when to assign the label.
- **Do not use when**: boundary cases and non-trigger conditions.
- **User-visible symptom**: how it appears in the product.
- **Canonical examples**: representative failure patterns.
- **Likely internal causes**: common upstream explanations.
- **Detection guidance**: how reviewers or automated systems may detect it.
- **Recoverability**: whether retry or architecture changes are needed.
- **Engineering response**: the remediation direction.

---

## 9. Primary failure definitions

## 9.1 `U1` — Unsupported answer

### Definition
The system states one or more **material claims** that are not supported by the uploaded corpus.

### Contract violated
- Grounded answering
- Honest failure behavior

### Why this failure matters
This is the clearest trust failure in a corpus-grounded QA system. The product’s central promise is that answers remain inside the evidence available in the uploaded documents. When the system asserts unsupported content, it is no longer behaving as a corpus QA system. It is behaving as a free-form generator while still implying source-backed authority.

### Trigger conditions
Assign `U1` when any of the following is true:

- the answer invents details not present in the corpus,
- the answer imports model prior knowledge and presents it as corpus-backed,
- the answer overstates what a cited source says,
- the answer attributes claims to a document that does not support them,
- unsupported material changes the substantive meaning of the answer.

### Do not use when
Do **not** use `U1` when:

- some evidence exists but the answer merely extends beyond it; use `U2` if the dominant issue is overstated completeness rather than wholly unsupported content,
- the issue is primarily wrong source references rather than unsupported content; use `P2` if the answer might be right but the provenance is false,
- the system should have abstained because the question is out of scope; use `A2` or `S1` depending on the dominant defect.

### User-visible symptom
The answer looks authoritative but contains claims the user cannot verify from the uploaded documents.

### Canonical examples
- answering a current library recommendation based on model prior instead of the uploaded docs,
- claiming a document specifies an implementation requirement that the text never states,
- merging unsupported facts into an otherwise grounded summary.

### Likely internal causes
- `G1` grounding or synthesis miss,
- `R1` retrieval miss causing the model to fill gaps,
- `X1` context assembly miss,
- insufficient answer prompt constraints,
- lack of support-state awareness at generation time.

### Detection guidance
**Human review:** compare every material claim to cited or retrievable support.  
**Model-judge detection:** possible for answer-vs-context contradiction checks.  
**Auto-detection:** limited, except when the system explicitly says support exists but returns none.

### Recoverability
- `broader_retrieval_may_fix` when relevant evidence exists but was missed,
- `retry_may_fix` only if nondeterminism is known to matter,
- otherwise requires grounding/prompt/policy changes.

### Engineering response
- tighten answering policy around claim-level support,
- require evidence-backed answer planning before synthesis,
- suppress unsupported completions when support is missing,
- log claim-to-source alignment for offline review.

---

## 9.2 `U2` — Partially supported answer presented as complete

### Definition
The corpus supports **part** of the answer, but the system presents a full, clean, or overly definite answer without sufficient qualification.

### Contract violated
- Honest uncertainty
- Grounded answering

### Why this failure matters
`U2` is often the most deceptive early-stage RAG failure because the answer may look mostly correct. The user sees real evidence, a plausible synthesis, and a fluent response, but the system quietly exceeds the support boundary.

### Trigger conditions
Assign `U2` when:

- part of the requested answer is supported, but the system answers as though the entire request were supported,
- the system omits necessary uncertainty or narrowing,
- a multi-document synthesis presents itself as complete even though one or more required components are missing,
- the system collapses incomplete evidence into a definitive response.

### Do not use when
Do **not** use `U2` when:

- the answer is mostly unsupported; use `U1`,
- the main issue is unresolved conflict across documents; use `A2` if the system should have surfaced ambiguity and did not,
- the system abstained too much; use `A1`.

### User-visible symptom
The answer contains real support, but it overpromises the completeness of what the corpus actually establishes.

### Canonical examples
- claiming a full comparison across two sources when one source addresses only half the comparison,
- producing a broad synthesis despite missing evidence for part of the requested scope,
- answering a multipart question fully when only one subpart is supported.

### Likely internal causes
- `G1` grounding or synthesis miss,
- support-state classifier absent or too weak,
- insufficient decomposition of multi-part questions,
- answer prompt optimizing for completeness instead of support fidelity.

### Detection guidance
**Human review:** evaluate whether every requested subclaim was actually supportable.  
**Model-judge detection:** viable if the judge sees question, answer, and source excerpts.  
**Auto-detection:** limited.

### Recoverability
- `broader_retrieval_may_fix` if omitted evidence exists,
- otherwise requires answer policy changes and stronger scope-control behavior.

### Engineering response
- decompose questions into supported and unsupported components,
- generate partial answers explicitly,
- require “support coverage” checks before final answer generation,
- tune for narrowness over rhetorical completeness.

---

## 9.3 `A1` — Wrong abstention

### Definition
The system declines, narrows, or refuses even though the corpus supports a direct or materially sufficient answer.

### Contract violated
- Usefulness expectation
- Correct support-state handling

### Why this failure matters
This is the primary **usefulness** failure among the selected 8. A system that abstains too aggressively will appear weak, brittle, or unable to answer even obvious corpus-backed questions.

### Trigger conditions
Assign `A1` when:

- the question is `SUPPORTED`, but the system says support is missing,
- the system narrows unnecessarily despite enough evidence for a direct answer,
- the answer says “I could not find enough support” even though the relevant evidence is present and inspectable.

### Do not use when
Do **not** use `A1` when:

- the system was correct to abstain because the evidence was genuinely partial or conflicting,
- the answer could not be produced due to an operational outage; use `O1`,
- the problem is actually a retrieval miss with a fallback refusal. `R1` may be the cause, but `A1` is still the primary user-visible failure only if the corpus actually supported the answer.

### User-visible symptom
The product behaves as though it knows less than the uploaded corpus actually contains.

### Canonical examples
- refusing a direct PDF lookup despite the relevant section being present,
- saying evidence is insufficient when the document section and page clearly answer the question.

### Likely internal causes
- `R1` retrieval miss,
- over-conservative answer policy,
- insufficient recall across document boundaries,
- poor query reformulation or chunk selection,
- thresholding tuned to avoid hallucination at the expense of answerability.

### Detection guidance
**Human review:** determine support state independently, then compare with the answer behavior.  
**Model-judge detection:** possible if given gold or retrieved evidence.  
**Auto-detection:** generally not reliable without gold support annotations.

### Recoverability
- `broader_retrieval_may_fix` for recall problems,
- `retry_may_fix` if retrieval is stochastic,
- otherwise requires policy retuning.

### Engineering response
- improve retrieval coverage,
- tune answer/no-answer thresholds on supported examples,
- penalize unnecessary abstention in eval optimization,
- use source-navigation tasks to stress-test answerability.

---

## 9.4 `A2` — Failed abstention

### Definition
The system should have abstained, narrowed, or surfaced ambiguity, but instead answered too strongly.

### Contract violated
- Honest uncertainty
- Honest failure behavior
- Scope control

### Why this failure matters
`A2` is the abstention-side counterpart to `U1`. It means the system made the wrong decision about whether the available support justified a direct answer. In a trust-first MVP, this is a major defect.

### Trigger conditions
Assign `A2` when:

- the question is `UNSUPPORTED_IN_CORPUS`, but the system answers directly,
- the question is `PARTIALLY_SUPPORTED`, but the system gives a complete answer instead of narrowing,
- the question is `AMBIGUOUS_OR_CONFLICTING`, but the system chooses one answer without qualification,
- the evidence is too weak for the confidence level used.

### Do not use when
Do **not** use `A2` when:

- the main defect is that the question is outside MVP capability; use `S1` if the dominant error is scope-boundary dishonesty,
- the answer is unsupported regardless of abstention logic; use `U1` if unsupported claims dominate,
- the answer mostly reflects partial support but with overstated completeness; use `U2`.

### User-visible symptom
The system answers when it should instead say: not enough support, limited answer only, or sources conflict.

### Canonical examples
- answering an unsupported-in-corpus question from prior knowledge,
- collapsing conflicting policy values into a single confident answer,
- treating weak evidence as sufficient for a specific recommendation.

### Likely internal causes
- missing support-state reasoning,
- answer prompt biased toward completion,
- no explicit ambiguity pathway,
- insufficient contradiction detection,
- no distinction between “related evidence exists” and “answer is supportable.”

### Detection guidance
**Human review:** label support state first, then determine if the answer decision matched it.  
**Model-judge detection:** feasible with support-state definitions.  
**Auto-detection:** limited.

### Recoverability
- `broader_retrieval_may_fix` only when missing evidence would have changed the support state,
- otherwise requires abstention and ambiguity-handling changes.

### Engineering response
- encode explicit behavior by support state,
- separate answerability classification from answer generation,
- require conflict surfacing for materially divergent sources,
- train/prompt for “narrow answer” as the preferred fallback before abstention.

---

## 9.5 `P1` — Provenance missing or too weak to inspect

### Definition
The answer may be directionally reasonable, but the returned source references are too weak, coarse, or incomplete for reliable user inspection.

### Contract violated
- Inspectable provenance

### Why this failure matters
The MVP does not promise answer text alone. It promises answer text plus inspectable support. `P1` means the system may have answered reasonably, but the user cannot actually validate why the answer should be trusted.

### Trigger conditions
Assign `P1` when:

- document identity is present but page or section is missing where it should be recoverable,
- source references are too coarse to verify material claims,
- cited passages are nearby and directionally useful but not precise enough for inspection,
- evidence cards identify a document but not a usable location.

### Do not use when
Do **not** use `P1` when:

- the returned provenance is outright false; use `P2`,
- exact paragraph anchors are missing for PDFs but page-level provenance is acceptable under MVP,
- the answer itself is unsupported; `U1` or `U2` may be primary, with `P1` as a secondary observation only if needed.

### User-visible symptom
The user sees something like “from Book A” but still cannot navigate to the supporting material with reasonable effort.

### Canonical examples
- correct document returned without page when page is recoverable,
- vague section path like “Chapter 3” for a narrow claim that required a more specific location,
- multi-source synthesis with only one generic source card.

### Likely internal causes
- `T1` traceability reconstruction miss,
- incomplete metadata propagation from retrieval unit to UI payload,
- insufficient citation assembly logic,
- document normalization that preserved content but lost usable anchors.

### Detection guidance
**Human review:** ask whether a user could verify the answer from the returned provenance alone.  
**Model-judge detection:** moderately feasible with provenance expectations attached to each question.  
**Auto-detection:** possible for missing required fields such as page or section.

### Recoverability
- `retry_may_fix` rarely,
- often requires provenance payload or UI-layer improvement,
- may require ingestion changes if anchor data was never preserved.

### Engineering response
- define minimum provenance by source type,
- enforce provenance completeness checks before final response emission,
- propagate section/page metadata throughout retrieval and answering,
- prefer coarse real provenance over false precision.

---

## 9.6 `P2` — Incorrect provenance

### Definition
The system returns source references that do not actually support the answer.

### Contract violated
- Inspectable provenance
- No fabricated provenance

### Why this failure matters
`P2` is one of the most severe defects in the system. It creates the appearance of evidence-backed reliability while silently undermining it. False provenance is often worse than missing provenance because it misleads users into trusting nonexistent support.

### Trigger conditions
Assign `P2` when:

- the page is wrong,
- the section path is wrong or nonexistent,
- the cited document does not support the cited claim,
- the source anchor is fabricated,
- the answer claims support but the cited location does not contain it.

### Do not use when
Do **not** use `P2` when:

- the source is directionally useful but too coarse; use `P1`,
- the answer is unsupported even without considering provenance; `U1` may be the primary label if unsupported content dominates and provenance is only a side effect.

### User-visible symptom
The system appears inspectable, but the evidence trail is false.

### Canonical examples
- citing the wrong page in a PDF,
- returning a section that does not exist,
- citing a nearby passage that does not support the answer’s key claim.

### Likely internal causes
- `T1` traceability reconstruction miss,
- citation assembly bug,
- offset or page-mapping errors in PDF ingestion,
- source-unit mixing during synthesis,
- stale or lossy anchor metadata.

### Detection guidance
**Human review:** verify each citation directly against the underlying source location.  
**Model-judge detection:** possible in some cases if the cited passage is available.  
**Auto-detection:** partial, for impossible anchors or invalid section references.

### Recoverability
- commonly `needs_ingestion_fix` or citation assembly fix,
- rarely recoverable by retry alone.

### Engineering response
- add invariant checks on citation payloads,
- preserve stable unit-to-source mappings through every pipeline stage,
- test page mapping and section reconstruction independently of answer quality,
- fail closed when citation confidence is low rather than fabricate exactness.

---

## 9.7 `I1` — Ingestion or structure failure visible in answer quality

### Definition
The answer or provenance degrades because ingestion or normalization failed to preserve usable structure, boundaries, or traceability.

### Contract violated
- Structural integrity
- Traceability

### Why this failure matters
The MVP’s feasibility depends on preserving enough structure from PDFs and Markdown to support retrieval and inspectable answering. `I1` is the failure class that tests whether the ingestion pipeline is good enough for the product to work at all on common inputs.

### Trigger conditions
Assign `I1` when:

- PDF page mapping is broken,
- headings are lost, merged, or corrupted,
- Markdown structure collapses so section-level retrieval becomes unreliable,
- formatting loss changes meaning materially,
- code blocks are flattened in a way that harms interpretation,
- the answer failure is visibly downstream of normalization damage rather than ordinary answer-generation behavior.

### Do not use when
Do **not** use `I1` when:

- the issue is simply poor semantic retrieval despite intact structure; use `R1` as the likely cause under some other primary failure,
- the question is outside MVP scope and the system handled it honestly,
- the answer is unsupported for reasons unrelated to ingestion quality.

### User-visible symptom
The system misses obvious sections, cites impossible locations, or retrieves malformed fragments that no longer reflect the source document’s intended structure.

### Canonical examples
- wrong page numbers because page offsets drifted during PDF normalization,
- Markdown headings collapsed so provenance can no longer reference section paths,
- lists or code blocks flattened into prose and then misinterpreted.

### Likely internal causes
- `N1` normalization or structure recovery miss,
- `T1` traceability reconstruction miss,
- lossy parser behavior,
- brittle heading inference in PDF text extraction,
- insufficient preservation of document boundaries.

### Detection guidance
**Human review:** compare normalized output or cited fragments to the original input structure.  
**Model-judge detection:** weak unless raw and normalized content are both available.  
**Auto-detection:** possible for malformed hierarchies, broken page mappings, or missing anchors.

### Recoverability
- usually `needs_ingestion_fix`,
- sometimes `broader_retrieval_may_fix` if the damage is partial rather than structural.

### Engineering response
- validate structure recovery independently from QA,
- add ingestion-quality assertions for page mapping and hierarchy formation,
- preserve code blocks and list semantics where they affect meaning,
- measure answer quality sliced by source type and document quality.

---

## 9.8 `S1` — Scope-boundary failure

### Definition
The system treats an out-of-scope question as if it were supported rather than explicitly stating the MVP limitation.

### Contract violated
- Honest scope boundaries
- Honest failure behavior

### Why this failure matters
The MVP explicitly excludes OCR-dependent PDFs, rich table and figure understanding, and external-world answering beyond the uploaded corpus. `S1` ensures that the system remains honest about those limits.

### Trigger conditions
Assign `S1` when:

- the answer depends mainly on chart, table, figure, image, or diagram interpretation and the system answers as though grounded,
- the answer depends on OCR-poor or scanned content and the system behaves as if it read it reliably,
- the question requires external-world facts not present in the uploaded documents and the system answers as if corpus-backed.

### Do not use when
Do **not** use `S1` when:

- the system correctly says the question appears out of scope,
- the answer is unsupported in corpus but still of a type the MVP should answer; then `A2` or `U1` may be more appropriate,
- the issue is merely missing evidence rather than out-of-scope capability.

### User-visible symptom
The system gives a seemingly grounded answer in an area where the MVP never claimed reliable capability.

### Canonical examples
- inventing values from a benchmark chart,
- answering from a scanned PDF without acknowledging OCR limitations,
- answering “current recommended version” when the corpus does not contain that external-world fact.

### Likely internal causes
- absent scope classifier,
- prompt optimized for answering rather than capability honesty,
- over-trust in extracted surrounding prose,
- failure to distinguish “question mentions corpus object” from “question is answerable by corpus text.”

### Detection guidance
**Human review:** determine whether the question fundamentally depends on excluded capabilities.  
**Model-judge detection:** often feasible from the question alone.  
**Auto-detection:** partially feasible for known unsupported modalities.

### Recoverability
- `not_recoverable_in_mvp` when the question truly depends on excluded capabilities,
- otherwise requires routing, product messaging, or scope-detection improvements.

### Engineering response
- classify unsupported question types early,
- return explicit scope-limitation language,
- prevent the answer model from speculating over tables, figures, or OCR-weak content,
- separate “can retrieve surrounding text” from “can answer the actual question.”

---

## 10. Failure interaction rules

Primary failures must remain mutually disciplined. The following rules avoid inconsistent labeling.

### 10.1 `U1` vs `U2`

- Use `U1` when the answer contains **material unsupported claims** that are not meaningfully backed by corpus evidence.
- Use `U2` when the answer has **real support**, but overstates how complete or definite that support is.

### 10.2 `A2` vs `S1`

- Use `S1` when the question is fundamentally outside MVP scope and the system answered as though grounded.
- Use `A2` when the question is in-scope but the system should have narrowed or abstained due to lack of support, partial support, or conflict.

### 10.3 `P1` vs `P2`

- Use `P1` for weak, coarse, incomplete, or only approximately helpful provenance.
- Use `P2` for false, fabricated, or claim-mismatched provenance.

### 10.4 `I1` vs other failures

- `I1` should be primary only when ingestion/normalization damage is visibly the dominant reason the run failed.
- If ingestion damage caused an unsupported answer, the run may still be primarily `U1` or `P2`, with `N1` or `T1` captured as secondary causes.

### 10.5 Dominant-failure rule

Every failed or borderline run should receive **one primary failure label**. If multiple problems are present, choose the label that best explains the user-visible trust break.

A useful order for choosing a primary label is:

1. Was the question fundamentally outside MVP scope but answered as supported? → `S1`
2. Did the answer materially exceed support? → `U1` or `U2`
3. Did the system make the wrong answer/abstain decision? → `A1` or `A2`
4. Was provenance non-inspectable or false? → `P1` or `P2`
5. Was the failure fundamentally caused by visible structure damage? → `I1`

Check `S1` early when the question depends on a capability the MVP explicitly excludes, such as OCR-only content, rich table/figure/chart/image understanding, external-world retrieval, or other deferred scope. If the question is in scope but the corpus lacks support, prefer `A2`, `U1`, or `U2` according to the answer behavior.

---

## 11. Secondary cause mapping

Primary failures describe the user-visible defect. Secondary cause labels explain probable internal origin.

| Primary failure | Common secondary causes |
|---|---|
| `U1` | `G1`, `R1`, `X1` |
| `U2` | `G1`, `R1`, `X1` |
| `A1` | `R1`, over-conservative policy |
| `A2` | `G1`, missing support-state policy |
| `P1` | `T1`, `N1`, incomplete payload assembly |
| `P2` | `T1`, `N1`, citation assembly bugs |
| `I1` | `N1`, `T1` |
| `S1` | missing scope router, `G1` |

Secondary causes should be assigned only when there is evidence. They should not be guessed from answer text alone if traces are absent.

---

## 12. Required evaluator workflow

Evaluators should follow this sequence:

1. **Classify support state** without looking at the answer first.
2. **Define minimum provenance expectation** for that question.
3. **Read the answer** and identify all material claims.
4. **Inspect the returned sources** and test whether they support those claims.
5. **Judge scope control and abstention behavior**.
6. **Assign overall trust outcome**.
7. **Assign one primary failure label if needed**.
8. **Assign secondary cause labels only when evidence exists**.

Most labeling disagreement is actually disagreement about support state. Resolve support state before debating failure labels.

---

## 13. Reviewer decision rules

When uncertainty exists during annotation, use these rules.

### Rule 1: Support fidelity beats answer completeness
A narrower but support-faithful answer is better than a broad unsupported answer.

### Rule 2: Coarse real provenance beats precise false provenance
If page or section precision is uncertain, the system should cite coarsely rather than fabricate specificity.

### Rule 3: Unsupported detail still counts
A mostly correct answer still fails if it includes material invented detail.

### Rule 4: Correct abstention on unsupported question types is success
Out-of-scope honesty is a pass, not a failure.

### Rule 5: Partial support requires visible qualification
If the corpus only partially supports the answer, qualification is part of correctness.

### Rule 6: Conflicting evidence requires visible tension handling
A confident single answer is wrong if the corpus materially conflicts and the system hides that conflict.

---

## 14. Implementation requirements implied by this failure set

The MVP does not need a perfect architecture, but it does need enough control points to make these failures measurable and reducible.

### 14.1 Required pipeline invariants

The pipeline should preserve, for each retrieval unit:

- stable document identifier,
- source type (`pdf` or `markdown`),
- section path when recoverable,
- page or source location when recoverable,
- enough raw-text context to verify what was actually retrieved.

### 14.2 Required answer-time decisions

Before final answer emission, the system should make or approximate these decisions:

1. Is the question in scope for MVP?
2. What is the likely support state of the retrieved evidence?
3. Is a direct answer justified, or should the system narrow, qualify, surface ambiguity, or abstain?
4. Does the returned provenance meet minimum inspectability for the question and source type?

### 14.3 Minimum instrumentation

At minimum, log:

- query text,
- corpus and document identifiers involved in the query,
- retrieved units and scores,
- evidence selected for the support decision,
- answer text,
- returned provenance payload,
- answer/abstain decision,
- source type slice (`pdf`, `markdown`, `mixed`),
- ingestion, structure, or provenance degradation flags relevant to the response,
- whether the question likely hit a known unsupported scope boundary.

Without these logs, several of the selected failures can only be diagnosed superficially.

---

## 15. Evaluation dataset requirements

A usable MVP eval set should deliberately include cases that trigger all 8 selected failures.

### 15.1 Required question classes

Include at least:

- direct PDF factual lookup,
- direct Markdown factual lookup,
- localized explanation,
- mixed-format synthesis,
- source navigation,
- partial-support questions,
- unsupported-in-corpus questions,
- ambiguous/conflicting-source questions,
- out-of-scope figure/table/image questions,
- malformed or weakly structured input cases.

### 15.2 Recommended first dataset size

A practical initial target is **50 to 100 annotated questions**. This is enough to expose failure distribution without overbuilding evaluation infrastructure.

### 15.3 Required slicing dimensions

Slice results by:

- source type: `pdf`, `markdown`, `mixed`,
- question class,
- support state,
- provenance expectation,
- primary failure label,
- confidence behavior,
- document quality bucket if available.

---

## 16. Operational metrics derived from this failure model

The following rates should be visible in early dashboards:

- trustworthy rate,
- borderline rate,
- not trustworthy rate,
- supported-question success rate,
- correct abstention rate,
- wrong abstention rate,
- failed abstention rate,
- provenance pass rate,
- unsupported-answer rate,
- failure distribution by primary failure label,
- failure distribution by question class,
- failure distribution by source type.

These are sufficient for the first iteration cycle. More detailed diagnostics can remain in internal traces.

---

## 17. Launch-gate interpretation

The MVP should not be considered ready for beta trust validation if any of the following are common in normal usage slices:

- `U1` unsupported answers,
- `A2` failed abstentions,
- `P2` incorrect provenance,
- `S1` scope-boundary failures.

These represent direct contract breaches.

The product may still be usable for controlled beta work with some residual `A1`, `P1`, or `I1` failures, provided they are visible, bounded, and trending downward. Those are still important defects, but they generally degrade usefulness and inspectability before they fully destroy trust.

---

## 18. Acceptance criteria by failure

This document does not set numeric targets, but it does define qualitative expectations.

### 18.1 `U1`
Should be rare enough that unsupported answering is treated as an exception, not a normal response mode.

### 18.2 `U2`
Should be uncommon on partial-support and synthesis questions. The normal fallback should be narrowing or qualification.

### 18.3 `A1`
May appear during early retrieval tuning, but should decline quickly as retrieval coverage improves.

### 18.4 `A2`
Should be rare. The system should prefer narrow answering or explicit abstention over confident overreach.

### 18.5 `P1`
Should be tolerated only where provenance is genuinely coarse due to MVP constraints, especially in PDFs.

### 18.6 `P2`
Should be treated as a release-blocking defect when systematic.

### 18.7 `I1`
Should be investigated by document-quality slice to determine whether the MVP’s lightweight normalization is clearing the usefulness threshold.

### 18.8 `S1`
Should be rare. Out-of-scope questions should generally receive explicit limitation language.

---

## 19. Example annotation record

```json
{
  "query_id": "q_018",
  "question": "What values are shown in the benchmark chart?",
  "question_class": "unsupported_scope",
  "support_state": "UNSUPPORTED_QUESTION_TYPE",
  "minimum_provenance": "document_and_page",
  "run_id": "run_2026_03_10_018",
  "answer_text": "The chart shows Redis at 2 ms and Postgres at 15 ms.",
  "returned_sources": [
    {
      "doc_id": "perf_notes_pdf",
      "display_name": "Performance Notes",
      "page_start": 44,
      "page_end": 44,
      "section_path": []
    }
  ],
  "support_alignment": "FAIL",
  "scope_control": "BAD",
  "provenance_quality": "WEAK",
  "abstention_behavior": "UNDER_CONSERVATIVE",
  "overall_trust_outcome": "NOT_TRUSTWORTHY",
  "primary_failure_label": "S1",
  "secondary_cause_labels": ["G1"],
  "severity": "high",
  "detectability": "human_only",
  "recoverability": "not_recoverable_in_mvp",
  "confidence_behavior": "high_confidence_wrong",
  "reviewer_notes": "Question depends on chart interpretation, which is outside MVP scope. System should have stated limitation rather than answering as grounded."
}
```

---

## 20. Recommended engineering workflow

Use the 8 selected failures as the top layer of the evaluation stack.

### 20.1 Weekly triage

For each evaluation batch:

1. review counts by primary failure label,
2. review `U1`, `A2`, `P2`, and `S1` first,
3. then inspect `U2` and `P1`,
4. review `A1` for usefulness regression,
5. review `I1` by source type and document quality.

### 20.2 Fix sequencing

Use this order:

1. eliminate false support and false provenance,
2. enforce correct abstention and scope handling,
3. improve provenance completeness,
4. improve retrieval recall to reduce wrong abstention,
5. harden ingestion for structurally weak documents.

### 20.3 Regression policy

Any change that improves answer rate by increasing `U1`, `A2`, `P2`, or `S1` should be treated as a regression, even if raw answer coverage increases.

---

## 21. Summary

The MVP does not need a large taxonomy to be evaluable. It needs the **right** taxonomy.

The 8 failures in this document are sufficient because they directly encode the Version 1 trust contract:

- stay inside corpus support,
- decide correctly when to answer versus abstain,
- return inspectable and truthful provenance,
- preserve enough structure for the system to work,
- remain honest about capability limits.

If these 8 failures are measured consistently and driven down in the recommended priority order, the team will have a practical and trustworthy foundation for further MVP building.
