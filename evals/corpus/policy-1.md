# Internal Policy: Evidence-Linked Response and Citation Policy

- Policy ID: POL-ERC-004
- Status: Approved
- Policy owner: Knowledge Integrity Council
- Effective date: 2026-01-15
- Review cadence: every 12 months
- Applies to: internal document-grounded assistant workflows, evaluation pipelines, and operator-reviewed response generation
- Does not apply to: fully external web search products, image-only workflows, or OCR-first scanned-document systems

## 1. Purpose

This policy defines the minimum requirements for responses that claim to be grounded in an internal document corpus.

The primary goal of the policy is to ensure that a user can inspect the basis of a response without unreasonable effort. A grounded response is not considered compliant merely because it is plausible or stylistically confident. It must remain within what the referenced corpus supports and must include provenance that is usable for review.

This policy also defines when a system should abstain, when it may answer narrowly with qualification, and when coarse provenance is acceptable.

## 2. Scope

### 2.1 In-scope workflows

This policy applies to workflows where a system answers questions primarily from an uploaded or connected internal corpus and presents the answer as evidence-linked or source-backed.

Examples of in-scope workflows include:

- document-grounded question answering over Markdown and text-extracted PDF sources;
- source-navigation answers that direct the user to a relevant document section;
- evaluation pipelines that score support alignment and provenance quality;
- human-in-the-loop drafting flows where an answer is shown together with source references.

### 2.2 Out-of-scope workflows

This policy does not govern:

- general web search products whose primary evidence source is the public web;
- image-only or chart-only interpretation workflows;
- OCR-heavy scanned-document systems where the text layer is materially incomplete;
- retrieval systems used only for internal ranking experiments and not shown to end users as evidence-backed answers.

### 2.3 Relationship to product-specific guidance

A product or team may add stricter requirements than this policy, but it may not relax the minimum requirements defined here unless an exception is approved under Section 9.

## 3. Core Principles

### 3.1 Support before fluency

A response must not exceed the support available in the cited corpus merely to produce a smoother or more complete answer.

### 3.2 Inspectable provenance

A response must provide provenance that allows a reviewer to find the supporting material with reasonable effort.

### 3.3 Honest uncertainty

When the corpus does not materially support the requested answer, the system must abstain, narrow the answer, or explicitly state the support limitation.

### 3.4 No fabricated provenance

A response must not present a precise-looking citation, anchor, page, or section path unless that locator is actually supported by the system’s recovered source structure.

### 3.5 Narrowness over completion

When only part of a requested answer is supported, the response should prefer a narrower supported answer over an apparently complete unsupported one.

## 4. Definitions

### 4.1 Supported answer

A supported answer is an answer whose material claims are justified by evidence in the cited corpus and whose presentation does not imply stronger support than the evidence warrants.

### 4.2 Partially supported answer

A partially supported answer is an answer where some requested content is supported but the full requested scope is not supported. Under this policy, partial support requires visible qualification or narrowing.

### 4.3 Abstention

Abstention means declining to answer the requested claim fully because the corpus does not provide enough support at the requested scope or because the question falls outside the supported question type.

### 4.4 Provenance

Provenance is the document identity and local locator, such as page or section path, used to let a reviewer inspect the evidence behind an answer.

### 4.5 Coarse provenance

Coarse provenance identifies the correct document or a broad stable parent section but does not identify the most local answer region.

### 4.6 False precision

False precision means presenting a locator that appears more specific than the system can actually justify from the source structure, such as a guessed subsection name or incorrect page number.

## 5. Minimum Response Requirements

### 5.1 Requirement for support alignment

A response presented as document-grounded must stay within what the corpus supports.

If the corpus supports only a narrower answer than the user requested, the response must either:

- answer only the supported portion and state the limitation; or
- abstain from the unsupported portion.

### 5.2 Requirement for provenance

Every document-grounded response shown to a user must include at least one source reference.

For Markdown sources, the preferred provenance format is **document title plus section path**.

For text-extracted PDF sources, the preferred provenance format is **document title plus page number**, and section information should be included when reliably available.

### 5.3 Requirement for local specificity

When the source structure supports a local locator, the response should provide that local locator rather than only the document identity.

Document-only provenance is acceptable only when:

- the document is short enough that local navigation would not materially improve inspectability; or
- the available source structure does not support a more local and trustworthy locator.

### 5.4 Requirement against synthetic anchors

A system must not invent subsection names, page markers, or heading paths based on nearby prose or inferred formatting.

### 5.5 Requirement for readable limitation statements

When the system cannot answer fully, the limitation statement must be explicit enough that a reviewer can tell whether the issue is missing support, unsupported question type, or conflicting evidence.

## 6. Allowed Answer Behaviors

### 6.1 Direct answer

A direct answer is allowed when the requested claim is materially supported by the corpus and the supporting evidence can be cited inspectably.

### 6.2 Narrowed answer

A narrowed answer is allowed when part of the request is supported and the answer explicitly stays within that supported subset.

### 6.3 Qualified answer

A qualified answer is allowed when the corpus supports the answer only under stated conditions, assumptions, or documented exceptions.

### 6.4 Abstention

Abstention is required when:

- the corpus does not materially support the requested answer;
- the question depends on unsupported content types such as image-only or chart-only interpretation;
- the available evidence is too conflicting to justify a single answer without qualification.

## 7. Provenance Rules

### 7.1 Markdown provenance

For Markdown documents, use the most specific stable heading path supported by the file structure.

If subsection recovery is unreliable, the response may cite the nearest stable parent section rather than guessing a more specific path.

### 7.2 PDF provenance

For PDF-derived text, use the most reliable page-level locator available. If section metadata is reliably preserved, it may be included in addition to the page reference.

### 7.3 Repeated headings

When a document contains repeated local headings such as `Notes`, `Exceptions`, or `Examples`, the system must avoid claiming subsection-level precision unless the local region can be distinguished reliably.

### 7.4 Broad but honest provenance

Broad provenance is acceptable when local structure is unstable, provided that:

- the cited document or parent section is correct;
- the answer remains narrow;
- and the response does not imply subsection certainty that the system does not actually have.

### 7.5 Invalid provenance patterns

The following are not compliant:

- citing the wrong document;
- citing the wrong page or section for a material claim;
- inventing a locator that does not exist in the source;
- citing a nearby section that discusses the topic but does not support the claim actually made.

## 8. Exceptions and Special Cases

### 8.1 Short documents

For documents under approximately **600 words**, document-only provenance may be acceptable if the entire document can be reviewed quickly and local headings do not materially improve inspectability.

### 8.2 Imported notes and weakly structured Markdown

For lightly normalized notes, imported notebook exports, or weakly structured Markdown, parent-section provenance may be acceptable when subsection boundaries are unstable.

This exception does not permit fabricated subsection labels.

### 8.3 Multi-document answers

A response may cite multiple documents when the answer genuinely depends on more than one source.

A multi-document answer must not present a synthesized conclusion as fully supported if one of the required source contributions is missing or only partial.

### 8.4 Conflicting evidence

When two authoritative in-scope documents materially conflict, the response must surface the conflict or qualify by source rather than collapsing the conflict into one apparently definitive answer.

## 9. Policy Exceptions and Approval

### 9.1 Approval requirement

Any exception that reduces user-visible provenance quality or allows weaker support behavior than this policy requires must be approved by the Knowledge Integrity Council.

### 9.2 Temporary exceptions

Temporary exceptions may be granted for pilots or controlled internal tests if all of the following are true:

- the exception is time-bounded;
- the affected workflow is clearly identified;
- reviewers are informed that the workflow is operating under reduced provenance or support guarantees.

### 9.3 Prohibited exception types

The following exceptions are not approvable under this policy:

- allowing fabricated provenance;
- allowing unsupported answers to be presented as supported;
- suppressing a known support limitation in user-visible output.

## 10. Review and Enforcement

### 10.1 Required review dimensions

Workflows governed by this policy must be reviewable along at least these dimensions:

- support alignment;
- provenance quality;
- abstention behavior;
- scope handling.

### 10.2 Severity guidance

The following are considered high-severity compliance failures:

- unsupported answers presented as supported;
- incorrect provenance for a material claim;
- fabricated or synthetic local locators.

The following are usually medium-severity failures:

- provenance that is real but too broad to inspect efficiently;
- unnecessary abstention on a clearly supported lookup question.

### 10.3 Remediation expectation

Teams that observe repeated provenance or support failures must either:

- tighten answer behavior;
- improve structure recovery;
- or narrow the workflow’s claimed capability.

## 11. Examples

### 11.1 Example of compliant narrowed answer

User question: “What is the default retention period and all exceptions?”

If the corpus states the default retention period clearly but does not enumerate all exceptions, a compliant response would state the default and explicitly note that the available corpus does not fully specify all exceptions.

### 11.2 Example of non-compliant completion

If the corpus gives one example exception but not a complete exception set, it is not compliant to present that example as though it were the full set of exceptions.

### 11.3 Example of compliant coarse provenance

If a Markdown file has unstable subsection structure after import cleanup, citing the parent section is compliant if the parent section is correct and no false subsection label is implied.

### 11.4 Example of non-compliant false precision

If the source file contains two different subsections called `Notes`, it is not compliant to cite “Notes > Final Recommendation” unless that exact path is actually present and reliably distinguished in the recovered structure.

## 12. Non-Goals and Silences

### 12.1 Matters not specified here

This policy does not specify:

- the ranking algorithm to be used by retrieval systems;
- the model family to be used for answer generation;
- the exact confidence scoring methodology;
- whether page-level evidence should be exposed in the user interface as links, pills, or inline references.

### 12.2 Why these matters are omitted

These choices may affect implementation quality, but they are not minimum policy requirements for support fidelity and provenance honesty.

## 13. Final Rule Summary

A document-grounded response is compliant only if it is:

- support-aligned,
- inspectably sourced,
- honest about limitations,
- and free of fabricated provenance.

When there is tension between a polished complete answer and an honestly limited answer, this policy requires the honestly limited answer.