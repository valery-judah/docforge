# MVP Functional Acceptance Criteria

Functional requirements define the minimum system behaviors needed to deliver the MVP product promise: a trustable question-answering workflow over a bounded corpus of uploaded text-based PDFs and Markdown files.

Acceptance criteria define observable pass/fail behavior for those requirements. They do not broaden MVP scope, prescribe implementation architecture, or replace evaluation and launch-gate failure definitions.

## MFR1. Supported uploads

Users can upload text-based PDF and Markdown files. Unsupported files are rejected or clearly flagged.

Acceptance criteria:

- Given a user uploads a text-based PDF, the system accepts it for processing.
- Given a user uploads a Markdown file, the system accepts it for processing.
- Given a user uploads an unsupported file type, scanned/OCR-only PDF, image-heavy document, or otherwise unsupported input, the system rejects it or clearly flags it as outside MVP scope.
- The system does not claim support for OCR, rich layout reconstruction, figures, charts, images, or table-centric QA.

## MFR2. Bounded corpus creation

Supported uploads are registered into a bounded user/workspace-scoped corpus.

Acceptance criteria:

- Uploaded supported documents are registered into a specific corpus.
- Queries run only against the active selected corpus.
- Evidence from one corpus must not appear in answers for another corpus.
- Corpus ownership is scoped to a user or workspace boundary.

## MFR3. Stable source identity

Every document and evidence unit preserves stable document identity and source type across ingestion, retrieval, answering, and provenance.

Acceptance criteria:

- Each source document receives a stable identity after upload.
- Evidence units retain document identity.
- Retrieval results retain document identity.
- Answer provenance resolves to real uploaded documents.
- Source type is preserved at minimum as `pdf` or `markdown`.

## MFR4. Processing status

The system exposes whether each document/corpus is processing, queryable, failed, or queryable with limitations.

Acceptance criteria:

- The system exposes document or corpus state as processing, queryable, failed, or queryable with limitations.
- A failed document is not silently treated as queryable.
- A document with degraded provenance or structure is not represented as fully queryable.
- Query behavior respects processing status.

## MFR5. Text extraction

The system extracts usable text from supported files without claiming support for OCR, rich layout, figures, charts, or tables.

Acceptance criteria:

- Text is extracted from supported text-based PDFs.
- Text is extracted from Markdown files.
- Document boundaries and text order are preserved well enough for retrieval and inspection.
- Unsupported extraction cases are surfaced rather than hidden.
- The system does not fabricate text from unsupported visual or scanned content.

## MFR6. Minimum source structure and provenance

The system preserves recoverable page, heading, section, or source-location metadata at the coarsest reliable level.

Acceptance criteria:

- For Markdown, heading or section paths are preserved where recoverable.
- For PDFs, page information is preserved where recoverable.
- If section or page precision is weak, the system uses coarser provenance or exposes the limitation.
- The system does not invent page numbers, headings, anchors, or sections.
- Coarse real provenance is preferred over precise false provenance.

## MFR7. Traceable evidence units

The system creates retrieval-addressable evidence units that retain document identity, source type, local text context, and available provenance.

Acceptance criteria:

- Normalized text is split or organized into retrieval-addressable evidence units.
- Each evidence unit retains document identity, source type, local text context, and available source-location metadata.
- Evidence units are inspectable enough for a user or evaluator to verify why they were retrieved.
- Evidence units without sufficient traceability are not treated as fully ready evidence.

## MFR8. Corpus retrieval

The system retrieves candidate evidence units from the active corpus for supported question types across PDF-only, Markdown-only, and mixed corpora.

Acceptance criteria:

- A user question retrieves candidate evidence units from the active corpus.
- Retrieval works for PDF-only corpora.
- Retrieval works for Markdown-only corpora.
- Retrieval works for mixed PDF and Markdown corpora.
- Retrieval supports the MVP question classes: factual lookup, localized explanation, basic synthesis, and source navigation.
- Retrieval does not use documents outside the active corpus.

## MFR9. Evidence handoff

Retrieved evidence passed to answering includes the text and provenance needed to decide support and render sources.

Acceptance criteria:

- Retrieved evidence passed to answer generation includes source text and provenance metadata.
- Answer generation does not receive detached text without document identity.
- Evidence used for support decisions is the same evidence available for provenance rendering.
- The system does not reconstruct provenance after answering from unrelated metadata.

## MFR10. Grounded answering

Answers are generated only from retrieved corpus evidence and must not make unsupported material claims.

Acceptance criteria:

- Supported questions receive answers based on retrieved corpus evidence.
- Material claims in the answer are supported by retrieved evidence.
- The system does not import model prior knowledge and present it as corpus-backed.
- If retrieved evidence is insufficient, the answer does not present unsupported claims as facts.
- Unsupported confident answers are treated as failures.

## MFR11. Support-aware response behavior

The system answers, narrows, qualifies, surfaces ambiguity, states lack of support, or states an MVP limitation according to evidence support.

Acceptance criteria:

- If evidence is sufficient, the system answers directly.
- If evidence is partial, the system narrows or qualifies the answer.
- If evidence is missing, the system states that the corpus does not support an answer.
- If evidence is ambiguous or conflicting, the system surfaces the ambiguity or source-specific differences.
- If the question requires an unsupported MVP capability, the system states the limitation.
- Response strength matches evidence strength.

## MFR12. Evidence rendering

Answers return source references that correspond to evidence actually used, and the system must not fabricate documents, pages, sections, anchors, or source support.

Acceptance criteria:

- Answers include source references for material claims.
- Returned source references correspond to evidence actually used.
- PDF provenance includes document identity plus page where recoverable.
- Markdown provenance includes document identity plus section or heading path where recoverable.
- Mixed-format synthesis includes usable provenance for each materially contributing source.
- The system does not fabricate documents, pages, sections, anchors, or source support.
- Claims without inspectable provenance are not presented as corpus-supported.

## Legacy FR Traceability

The previous 26 functional requirements are legacy detail for traceability only. The MVP requirements layer is the 12-MFR model above.

| Legacy FRs | Minimal MVP requirement |
|---|---|
| FR1, FR2, FR3 | MFR1 |
| FR4, FR5 | MFR2 |
| FR6, FR7, FR10 | MFR3 |
| FR8, FR15 | MFR4 |
| FR9 | MFR5 |
| FR11, FR12 | MFR6 |
| FR13, FR14 | MFR7 |
| FR16, FR17, FR19 | MFR8 |
| FR18 | MFR9 |
| FR20, FR21 | MFR10 |
| FR22, FR26 | MFR11 |
| FR23, FR24, FR25 | MFR12 |
