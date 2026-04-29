# Research Notes: Trace Stability Under Imperfect Markdown Ingestion

- Status: Working notes
- Author: Retrieval Reliability Group
- Last updated: 2026-02-21
- Intended use: internal technical guide and experiment notes
- Scope: ingestion quality, structure recovery, and provenance behavior for Markdown-heavy corpora
- Non-goals: OCR, chart interpretation, rich table understanding, or exact span anchoring

## 1. Purpose

These notes summarize a set of ingestion experiments focused on a narrow question:

Can the system preserve enough Markdown structure to support answerable retrieval and inspectable provenance when source files are imperfect but still text-native?

The work here is not a full parser benchmark. It is a practical evaluation of how much structural damage the system can tolerate before answer quality or citation quality becomes unreliable.

The central concern is not only whether relevant text is retrievable. It is whether the retrieved text can still be tied back to a stable section path or another honest local locator.

## 2. Study Context

### 2.1 Why the study was run

Earlier test corpora showed a repeated pattern:

- the answer text was often directionally correct,
- but the supporting citation was either too broad or tied to the wrong local section.

In most failed runs, the system did not lose the document identity. It lost local structure. That meant the system could still say "the answer comes from this file" while failing to identify where in the file the support actually lived.

This mattered most for Markdown sources that had been edited repeatedly, imported from notes tools, or partially converted from other formats.

### 2.2 Success condition

For this study, a Markdown file was considered ingestion-stable if all of the following were true:

1. a reviewer could locate the answerable material through the returned section path or other local locator;
2. the system did not invent subsection names that were not actually present in the file;
3. the system could answer narrow lookup questions without unnecessary abstention when the text support was clearly present;
4. list and code formatting did not collapse in a way that changed meaning materially.

### 2.3 Failure condition

A run was considered structurally degraded if one or more of the following happened:

- headings were merged into ordinary text and no longer usable for source navigation;
- repeated subsection names caused the citation to point to the wrong local region;
- list collapse changed the meaning of requirements or exceptions;
- the system refused to answer even though support existed in the file and a human reviewer could still find it.

## 3. Input Profile

### 3.1 File types included

The test set used only Markdown files. Some were originally written as Markdown, while others were lightly normalized exports from note-taking tools.

The files were all text-native. No images, embedded screenshots, or OCR-dependent artifacts were required for the main questions.

### 3.2 Common authoring defects

The most common defects were:

- repeated headings such as `Notes` or `Follow-up`,
- skipped heading levels,
- bold text used as pseudo-headings,
- imported note fragments pasted without full cleanup,
- mixed list styles inside one section,
- short configuration snippets placed directly inside prose without strong visual separation.

### 3.3 What remained recoverable

Even in the weaker files, document identity was almost always stable. Top-level headings were often preserved as well. The main failure zone was lower in the hierarchy: subsection paths, list semantics, and local region boundaries.

## 4. Main Findings

### 4.1 Stable top-level headings help more than perfect fine-grained parsing

When the file had a clean title and stable top-level headings, retrieval usually found the correct topic area even if subsection quality was uneven.

This did not guarantee good provenance. It only meant the system could usually identify the right document and broad section.

### 4.2 Repeated subsection names are a major provenance risk

The single most common source of false precision was repeated subsection names. When a file contained multiple local headings named `Notes`, `Examples`, or `Caveats`, the system sometimes returned a citation that looked specific but actually pointed to the wrong region.

This problem was worse when the file also contained imported note blocks with weak surrounding structure.

### 4.3 Broad citation is safer than invented subsection detail

When subsection recovery was uncertain, coarse provenance was usually safer than fabricated precision.

In reviewer scoring, a broad but materially correct citation was preferred over a precise-looking citation that named the wrong subsection.

### 4.4 List collapse can change meaning

List formatting was not just decorative. In several test files, collapsing bullets into flat prose changed the apparent relationship between rule, exception, and implementation note.

This mattered for answer quality as well as provenance. A system could retrieve the right text span but still answer incorrectly if the structure made an exception look like the default rule.

## 5. Structure Recovery Notes

### 5.1 Heading hierarchy

Markdown files with clean `#`, `##`, and `###` usage were the easiest to preserve. Problems rose quickly when heading levels were skipped or when authors mixed true headings with styled text that only looked like headings.

A common failure pattern was:

- title preserved,
- top-level sections preserved,
- subsection path partially lost,
- answer still retrievable,
- citation returned at the wrong local depth.

### 5.2 Lists and requirements

Requirement-like content was most reliable when each requirement was in its own bullet or short paragraph.

Dense mixed prose created more ambiguity, especially when exceptions were written inline rather than separated clearly.

### 5.3 Code and config fragments

Short code or configuration fragments should remain fenced when they affect meaning. Flattening them into prose often made nearby explanatory text harder to interpret and weakened the local boundary between example and rule.

## 6. Imported Debugging Notes

The section below was copied from working notes and only lightly cleaned. It is intentionally left uneven because imported note blocks are a real source of ingestion pressure.

**debug export from notebook - partial cleanup only**

- page markers n/a obviously, markdown only
- top-level path usually survives
- lower path not always
- repeated `Notes` headers after merge were still present in two files
- in one batch the answer was present but citation landed on the wrong Notes subsection
- broad locator was acceptable to reviewers when subsection confidence was low
- invented subsection label was not acceptable
- some list items got flattened and then the default rule looked stronger than it really was
- code fence loss: low frequency, but when it happened config lines blended into explanation text

#### Debug Snapshot

short observations from Feb run

- one document had the answer under a bold pseudo-heading rather than a real heading
- another had two adjacent sections both called `Notes`
- one case answered correctly only when the reviewer ignored the returned subsection and read the whole parent section
- one abstention was judged unnecessary because the support text was present in the imported notes block
- heading path should not be synthesized from neighboring prose
- if only parent section is stable, cite parent section

### Notes

The debug export suggests that citation policy should degrade gracefully. If the subsection boundary is unstable, the system should return the nearest stable parent path instead of guessing a more specific path.

### Notes

A separate review from the same week found that incorrect local citations were more damaging than missing local detail. Reviewers tolerated broad provenance when the answer itself stayed narrow and the document identity was correct.

## 7. Recommendations

### 7.1 Default citation behavior for structurally weak Markdown

When the file has stable top-level structure but unreliable local subsection recovery, return:

- document identity,
- the nearest stable section path,
- and no synthetic subsection label.

Do not invent a locator merely because the answer text appears near a likely boundary.

### 7.2 Answer behavior when support exists in a messy section

If the support text is materially present but lives inside a rough imported-notes region, the system should still answer if the claim is narrow and the evidence is readable.

It may use coarser provenance than normal, but it should not abstain solely because the subsection path is imperfect.

### 7.3 When to abstain

Abstention is appropriate when structure damage makes the relevant text too fragmentary to support the requested claim or when the question depends on a distinction that the flattened structure no longer preserves safely.

Abstention is not appropriate when the answer is still directly stated in readable text and a reviewer can find it with reasonable effort.

## 8. Decision Rules Used in Review

### 8.1 For provenance

Use the most specific stable locator that is actually supported by the file structure.

If there is doubt between a parent section and a guessed subsection, prefer the parent section.

### 8.2 For answerability

If the support is explicit in text and the question is narrow, answer it even when local structure is messy.

If the support depends on distinguishing default rule from exception and the list structure has collapsed, answer cautiously or abstain.

### 8.3 For repeated headings

Repeated local headings such as `Notes` should be treated as a traceability hazard. They do not make the file unusable, but they make subsection-level provenance less reliable.

## 9. Worked Example

### 9.1 Example of safe behavior

Question: "What should the system do when subsection recovery is uncertain?"

Safe answer: return the nearest stable parent path and avoid synthetic subsection labels.

This answer is safe because the recommendation is explicitly stated in the document and does not require inference beyond the local notes.

### 9.2 Example of unsafe behavior

Question: "Which Notes subsection contains the decisive recommendation?"

Unsafe answer: naming the second `Notes` subsection with confidence when the system has not preserved a stable way to distinguish the two local regions.

The file contains both `Notes` subsections, but the ingestion path may not preserve enough local identity to justify precise distinction.

## 10. Local Exceptions and Caveats

### 10.1 Caveat on imported notes

Imported notes were often still usable for narrow lookup questions, but they were worse for precise source navigation.

### 10.2 Caveat on parent-only provenance

Parent-only provenance is acceptable in this study only when the subsection boundary is unstable. It should not become the default behavior for clean Markdown sources.

**ops note - not a heading**
one review batch marked parent-only citation as acceptable for imported sections, but not for clean authored sections; keep that distinction because otherwise provenance gets too broad too often.

## 11. Final Recommendation

For Markdown ingestion under realistic but imperfect authoring conditions:

- preserve document identity and top-level hierarchy first,
- preserve lists and code fences where meaning depends on them,
- avoid synthesizing subsection detail,
- prefer coarse real provenance over precise false provenance,
- and do not abstain from narrow supported questions merely because the local notes section is messy.

## 12. Quick Reference

### 12.1 Highest-risk structure defects

- repeated subsection names
- pseudo-headings created with bold text only
- collapsed bullet lists
- imported notes with weak nesting

### 12.2 Safer fallback behavior

- cite parent section if subsection stability is doubtful
- keep answer scope narrow
- state limitation when exact local path is uncertain
- do not fabricate subsection names

### 12.3 Cases this file is meant to support

This file is suitable for questions about:

- repeated heading risk
- parent-section fallback policy
- when abstention is or is not justified
- why broad provenance can be safer than invented precision
- how structure loss affects answer quality