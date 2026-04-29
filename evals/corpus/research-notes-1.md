# Research Notes: Heading-Aware Passage Segmentation for Technical Document QA

- Status: Working notes
- Author: Retrieval Evaluation Group
- Last updated: 2026-02-18
- Intended use: internal technical guide and experiment summary
- Scope: document-grounded question answering over Markdown and exported PDF text
- Non-goals: table extraction, figure interpretation, OCR-heavy scanned documents

## 1. Purpose

These notes summarize the current findings from the segmentation and retrieval study used to support technical document question answering. The study was designed to answer a narrow engineering question: does preserving document structure during passage segmentation improve answer quality and citation quality for lookup-style questions?

The work here is not a complete retrieval architecture review. It focuses on the practical behavior of a document QA stack under realistic constraints: mixed source formats, inconsistent authoring quality, and the requirement that returned answers remain tied to inspectable source locations.

The main recommendation is to use heading-aware segmentation as the default indexing strategy for technical corpora with meaningful section structure. Fixed-size windows remain useful as a fallback for weakly structured documents, but they should not be the primary segmentation mode when heading paths are available.

## 2. Study Context

### 2.1 Why the study was run

The previous indexing pipeline treated all technical documents as flat text. That approach was serviceable for broad semantic retrieval, but it produced two recurring problems in question answering.

First, answerable lookup questions were sometimes grounded in the wrong local context because adjacent sections were merged into the same passage window. Second, citations were frequently too coarse to be useful because the system could identify the file but not the specific section where the answer was stated.

The study was run after repeated reviewer feedback that many answers were directionally correct but difficult to inspect. The problem was not only retrieval relevance. It was also passage shape. If the indexed unit ignores section boundaries, the returned evidence often contains the right topic but the wrong support span.

### 2.2 What counts as success

For this study, success was defined in three ways.

The first measure was lookup answerability: whether a reviewer could verify that a narrow factual question had been answered from the corpus without unsupported additions.

The second measure was citation usability: whether a reviewer could navigate from the answer to the correct document section without scanning large portions of the file.

The third measure was latency discipline: any retrieval improvement that raised median end-to-end latency above the interactive target was treated as operationally weak even if answer quality improved.

The interactive target used in this study was **under 2.5 seconds median end-to-end latency** for the full retrieval and answer generation path.

## 3. Corpus Profile

### 3.1 Included document types

The study corpus included engineering runbooks, API notes, design summaries, onboarding guides, and internal research notes. Documents were primarily Markdown, with a smaller number of PDFs that had already been converted to text with page markers preserved.

The corpus intentionally excluded image-first content, scanned PDFs with poor OCR, and documents where critical facts were only present in charts or diagrams.

### 3.2 Corpus size

The indexed corpus contained **1,840 documents** at the time of the final experiment run. Of those, **1,510 were Markdown** and **330 were PDF-derived text files**.

The median Markdown document length was approximately **1,200 words**. The median PDF-derived document length was approximately **2,100 words** after extraction and cleanup.

### 3.3 Authoring quality observations

Markdown documents with stable heading hierarchies produced the cleanest retrieval units. Weakly authored notes with heading jumps, repeated heading names, or large unstructured sections generated the most citation problems.

In the PDF-derived subset, the biggest issue was not lexical noise. It was broken alignment between extracted text blocks and original page boundaries. When page markers drifted, provenance degraded even when retrieval still found the right topic area.

## 4. Segmentation Strategies Evaluated

### 4.1 Fixed-window baseline

The baseline strategy used flat windows of **280 tokens** with **40-token overlap**. This approach was chosen because it is simple to implement and relatively robust when structure is unreliable.

The weakness of the baseline was locality. A passage could begin in one subsection and end in another, which made it harder to attach a clean section path to the retrieved evidence. Reviewers described these passages as relevant but messy.

### 4.2 Heading-aware segmentation

The heading-aware strategy treated section boundaries as primary passage boundaries. Subsections were preserved when they remained under the passage size ceiling. Long subsections were split internally, but the split segments retained the same heading path metadata.

The maximum target segment size for heading-aware passages was **320 tokens**, with a soft preference for keeping each segment closer to **220 to 280 tokens** when possible. Small subsections were allowed to remain intact even if they were shorter than the nominal target range.

### 4.3 Hybrid fallback mode

A fallback mode was added for poorly structured files. In fallback mode, the segmenter first attempted heading-aware segmentation. If the file had fewer than two meaningful headings or if a single section contained more than 70 percent of the document text, the pipeline fell back to fixed windows.

This fallback prevented degenerate cases where a nominally structured document produced one massive section that was unusable for local citation.

## 5. Retrieval Stack Configuration

### 5.1 First-stage retrieval

The production-like experiment used a hybrid first stage with lexical and dense retrieval. Lexical retrieval remained important for identifier-heavy questions, especially those involving parameter names, environment flags, or exact component terms.

Dense retrieval improved recall for paraphrased questions but was less reliable when section titles contained specialized terminology that the query repeated exactly.

The first-stage retriever returned **30 candidates** before reranking.

### 5.2 Reranking

A cross-encoder reranker was applied to the first-stage candidate set. The reranker selected the top **12 passages** for downstream answer assembly.

In practice, the reranker improved passage ordering for paraphrased lookup questions, but it also introduced a latency cost. The added latency was acceptable in the final configuration, but only after candidate count was capped at 30.

### 5.3 Answer context assembly

The answer generator did not receive all 12 reranked passages. Instead, the assembly step passed only the top **6 passages** to generation. This limit reduced context redundancy and made citation review easier.

Passing more than 6 passages increased the frequency of blended answers that mixed nearby but non-equivalent statements. That was especially common in policy-style documents where neighboring sections contained exceptions and general rules.

## 6. Main Findings

### 6.1 Effect on supported lookup questions

Heading-aware segmentation produced the clearest improvement on supported lookup questions. Reviewer-marked answerability improved because the returned evidence was more likely to match the exact subsection where the answer was stated.

The largest gain was in citation usability rather than raw retrieval recall. Even when both strategies retrieved a relevant passage, heading-aware segments were more likely to support an answer with a precise section path.

Across the annotated lookup set, heading-aware segmentation improved citation usability by **11 percentage points** over the fixed-window baseline.

### 6.2 Effect on source navigation questions

Source navigation also improved, though less dramatically than direct lookup. The main benefit was that the system could name a specific subsection rather than only the document.

Reviewers were more likely to mark a navigation answer as useful when the returned provenance included both the document identity and the subsection path. Document-only answers were usually considered incomplete even when the document itself was correct.

### 6.3 Effect on synthesis-style prompts

The improvement on synthesis prompts was smaller. When an answer required combining multiple sections, passage boundaries mattered less than retrieval diversity and answer control.

For synthesis, heading-aware segmentation still helped by reducing local contamination, but it did not eliminate unsupported completion. The main failure mode remained the model presenting a partially supported answer as complete.

## 7. Failure Patterns Observed

### 7.1 Wrong abstention on locally supported facts

Some clearly answerable lookup questions still triggered abstention. This usually happened when the exact answer appeared in a short subsection with a generic heading, while neighboring larger sections ranked more strongly.

This failure was not caused by missing evidence. It was usually caused by poor passage ranking combined with conservative answer behavior.

### 7.2 Weak provenance despite correct answer text

A recurring issue was answers that were textually correct but cited only the document title. Reviewers consistently marked these as weak because the document could be long and the answer location was not obvious.

This pattern was more common in the fixed-window baseline because the retrieved segment often lacked stable section metadata.

### 7.3 False precision in citation

In a smaller number of cases, the system returned a precise-looking subsection path that did not actually contain the answer. This was more damaging than coarse provenance because it created the appearance of inspectability while misdirecting the reviewer.

False precision usually came from stale heading metadata after intermediate segment merges.

## 8. Implementation Guidance

### 8.1 Default segmentation policy

Use heading-aware segmentation as the default when the source document has a meaningful section hierarchy.

A document should be considered heading-structured if it has at least **three semantically distinct headings** and no single section contains more than **70 percent** of the total document text.

### 8.2 Fallback policy

Use fixed windows when the source fails the structure test, when extracted headings are obviously decorative, or when subsection boundaries are too unstable to support local citation.

The fallback window size should remain **280 tokens with 40-token overlap** unless downstream latency or recall measurements justify a change.

### 8.3 Citation policy for Markdown sources

For Markdown documents, the preferred provenance format is **document title plus section path**. Subsection-level provenance should be returned when the answer is local to one subsection.

Document-only provenance should be reserved for short documents or for cases where no finer stable structure exists.

## 9. Known Limitations

### 9.1 Cases not addressed by this guide

These notes do not solve table lookup, figure interpretation, or screenshot-heavy technical documentation. They also do not address scanned PDFs where page text is incomplete or noisy.

The guidance here assumes that the answerable content exists in text form and that section structure is either present or recoverable.

### 9.2 Remaining open questions

The study did not fully resolve how to segment appendices that contain dense parameter lists. In those cases, fixed windows sometimes outperformed heading-aware segments because repeated labels created excessive passage similarity.

Another open question is whether answer assembly should diversify sections before passing context to generation. Current behavior can over-concentrate on one chapter even when the top reranked list contains multiple useful sections.

## 10. Final Recommendation

For technical document QA over mostly text-native sources, adopt heading-aware segmentation as the default indexing policy.

Retain fixed-window segmentation as a fallback for weakly structured files, but do not use it as the primary mode for Markdown documents with stable headings.

If the product promise includes inspectable provenance, do not treat segmentation as a purely retrieval concern. Passage boundaries determine not only what is found, but whether the returned answer can be reviewed efficiently.

## 11. Quick Reference

### 11.1 Recommended defaults

Use these defaults unless the corpus profile gives a strong reason to deviate:

- default segmentation mode: heading-aware
- fallback segmentation mode: fixed window
- fixed-window size: 280 tokens
- fixed-window overlap: 40 tokens
- heading-aware target ceiling: 320 tokens
- first-stage candidates: 30 passages
- reranked set: 12 passages
- generator context: top 6 passages
- latency target: under 2.5 seconds median

### 11.2 Use heading-aware segmentation when

Use heading-aware segmentation when the file has stable headings, the goal includes inspectable citations, and lookup or navigation questions are common.

### 11.3 Use fallback segmentation when

Use fallback segmentation when the file has weak structure, decorative headings, or one oversized section that dominates the document.
