# Research Notes: Adaptive Context Packing for Long-Form Technical QA

- Status: Working notes
- Author: Retrieval Evaluation Group
- Last updated: 2026-02-26
- Intended use: internal technical guide and experiment notes
- Scope: document-grounded question answering over Markdown-first corpora with PDF-derived text as a secondary source type
- Non-goals: image understanding, chart reading, OCR recovery, and external-web fact completion

## 1. Purpose

These notes summarize the experiment series on adaptive context packing for long-form technical question answering. The central question was whether context assembly should remain a fixed top-k passage selection step or whether the number and shape of passages should vary based on question type, document structure, and passage redundancy.

The work was scoped to text-native sources. Most test documents were Markdown files with stable heading hierarchies, plus a smaller subset of PDF-derived text where page markers were preserved but local structure was less reliable. The study did not attempt to solve figure-dependent answers, screenshot-heavy troubleshooting pages, or scanned PDFs with weak OCR.

The practical motivation was straightforward. Reviewers repeatedly reported answers that were directionally correct but either blended neighboring claims, omitted needed qualifying context, or cited a source bundle that was too broad to inspect. In many of those cases the retrieval stage had found relevant material, but answer quality deteriorated because the assembled context included too many loosely related passages.

## 2. Study Questions

### 2.1 Primary question

Would adaptive context packing improve answer trustworthiness for technical lookup and synthesis prompts without causing unacceptable latency regression?

### 2.2 Secondary questions

The experiment series also tracked the following:

- whether narrower context improved citation usability;
- whether structure-aware packing reduced unsupported completion;
- whether different question classes should use different context budgets;
- whether any gain on technical manuals transferred to runbooks and release notes.

### 2.3 What was not answered here

These notes do not establish a final production policy for all corpora. The experiments focused on manuals, runbooks, and internal implementation notes. Customer tickets, incident timelines, and legal or policy documents were not part of the main evaluation set.

These notes also do not contain the final rollout decision for the serving stack. A deployment recommendation was discussed, but it was not ratified in this document.

## 3. Corpus and Evaluation Setup

### 3.1 Corpus profile

The main evaluation corpus contained three document groups:

- product manuals;
- service runbooks;
- release engineering notes.

Manuals were generally well structured and used stable heading hierarchies. Runbooks varied in quality but still tended to preserve useful subsection boundaries. Release engineering notes were the noisiest group because they mixed procedural guidance, examples, and retrospective notes in the same file.

### 3.2 Question distribution

The annotated set emphasized source-grounded questions over free-form summary prompts. Most of the study set consisted of supported lookups, source-navigation questions, and constrained explanations. A smaller slice of the set covered partial-support and conflicting-evidence prompts because those were recurrent failure modes in earlier QA reviews.

### 3.3 Metrics tracked

The review protocol tracked:

- support alignment;
- citation usability;
- abstention quality;
- answer scope control;
- end-to-end latency.

The notes below use reviewer language such as "clear improvement," "borderline," and "not stable enough" when a result was directionally consistent but the sample size was too small to justify a stronger statistical claim.

## 4. Packing Strategies Compared

### 4.1 Fixed top-k baseline

The baseline packed the top **8 retrieved passages** into generation context. Passages came from the reranked candidate set with no diversity rule beyond score ordering.

This was easy to implement and reasonably robust on direct lookups. Its weakness was that closely related passages from the same section often crowded out disambiguating material from nearby sections. In synthesis-style prompts the baseline sometimes created the appearance of comprehensive support even when one necessary qualification was absent.

### 4.2 Adaptive packing by question class

The adaptive variant used different context budgets based on the predicted question class.

For narrow factual lookups and source navigation, the packer preferred a smaller context and stronger locality. For localized explanations it allowed a slightly broader bundle. For synthesis prompts it attempted to retain source diversity rather than simply taking the highest-scoring passages from one chapter.

The target bundle sizes evaluated were:

- **top 4** for lookup and navigation;
- **top 6** for localized explanation;
- **top 8** for synthesis when multiple sections appeared materially relevant.

### 4.3 Structure-aware anti-redundancy rule

A second variant added a light anti-redundancy rule. When two candidate passages came from the same subsection and one largely subsumed the other, only the stronger passage was kept unless the lower-ranked passage contained a distinct numeric or normative statement.

This rule was introduced after early pilots showed that answer generation often repeated one section's framing and ignored nearby exceptions.

## 5. Main Findings

### 5.1 Supported lookup behavior

On supported lookup questions, smaller context bundles generally improved answer trustworthiness. Reviewers said the **top-4** setting produced the most inspectable answers for manuals and well-structured runbooks because the answer was more likely to stay close to the subsection that actually stated the fact.

The main gain was not recall. The main gain was cleaner support mapping. Reviewers could more easily verify the answer when citations pointed to one subsection instead of a broad bundle from a whole chapter.

### 5.2 Localized explanation behavior

For localized explanation prompts, **top-6** was more reliable than top-4. The smaller setting sometimes dropped a nearby qualifying paragraph that changed the practical interpretation of a configuration recommendation.

This mattered most in runbooks where one subsection described the default behavior and the following subsection described exceptions for degraded mode.

### 5.3 Synthesis behavior

The synthesis results were mixed.

Adaptive packing reduced some obvious cases of repeated evidence and section-local overfitting. However, the improvement was uneven across document groups. Manuals benefited modestly, while release engineering notes still produced unstable answers when the relevant support was scattered across procedural steps and informal commentary.

The current notes support a narrow conclusion: adaptive packing helps synthesis when the contributing evidence is spread across a small number of clearly structured sections. These notes do **not** support the stronger claim that adaptive packing solves synthesis reliability in general.

## 6. Recommendation Status

### 6.1 Current recommendation for manuals

For product manuals, these notes recommend **adaptive packing with top-4 default for supported lookup and source navigation**. The reasoning is that manuals usually have stable heading structure, local answer regions, and fewer section-level contradictions.

### 6.2 Current recommendation for runbooks

For runbooks, the recommendation is more cautious. Adaptive packing appears beneficial for lookup questions and many localized explanations, but the exact default bundle size should remain configurable because runbooks vary more in structure and often place operational caveats in nearby sections.

### 6.3 Recommendation boundary

These notes do not establish one default packing policy for every corpus type. They justify a default for manuals and a conditional recommendation for runbooks. They do not provide enough evidence to choose a final default for release notes or mixed-note corpora.

## 7. Conflicting Signals

### 7.1 Offline benchmark signal

In the offline benchmark, **top-8** sometimes produced the highest answer completeness score on synthesis-style prompts. This was especially visible in release engineering notes where the relevant support was distributed across procedural context, rollout caveats, and a final recommendation block.

### 7.2 Reviewer trust signal

In human review, **top-6** often produced better trust outcomes than top-8 because answers were less likely to blend weakly related passages into a complete-looking narrative. Reviewers were more tolerant of a narrower answer than of a fully stated answer that quietly crossed the support boundary.

### 7.3 Why this was not fully resolved

The conflict between offline completeness and reviewer trust was not resolved in this round. The study tracked both signals, but the offline set favored answer breadth while human review favored support fidelity and inspectable provenance.

For that reason, a single statement such as "top-8 is best" would overstate what the notes support.

## 8. Release Notes Subset

### 8.1 Why release notes were difficult

Release engineering notes were difficult because they often mixed status updates, procedural guidance, and follow-up comments in the same file. A single section might contain a rollout instruction, an exception discovered later, and a retrospective note written after the original change.

### 8.2 What the study actually found

The notes support only a limited claim for this subset: adaptive packing reduced some redundant evidence bundles but did not make release-note synthesis reliably support-preserving.

A stronger recommendation would require a cleaner source format or stricter section filtering before retrieval.

### 8.3 What is still unknown

These notes do not report a final production-safe bundle size for release notes. They also do not provide a complete error decomposition for this subset.

## 9. Dashboard References Not Included in Text Export

### 9.1 Latency heatmap

The latency heatmap referenced during the review meeting is **not reproduced in this Markdown export**. It was shown from a dashboard screenshot during discussion and archived separately in the experiment folder.

The screenshot was used to compare tail-latency behavior across context budgets. The specific cell values from that heatmap are not transcribed here.

### 9.2 Citation-review scatter plot

The citation-review scatter plot is also omitted from this text export. Reviewers used it to discuss the relationship between citation usability and perceived answer trust, but the plotted points and exact axes are not written out in these notes.

Questions that depend on the visual values from these artifacts cannot be answered from this file alone.

## 10. Open Decisions

### 10.1 Serving default

A final serving default for all corpus types was deferred. The working direction favored adaptive packing, but the team did not ratify one universal default in this document.

### 10.2 Cost model

The comparative cost model for top-4, top-6, and top-8 generation was still under review when these notes were compiled. A separate budgeting sheet existed, but its results are not copied here.

### 10.3 Model-specific tuning

These notes do not specify whether the same packing policy should be used for every generator model. The experiments were run on the default evaluation stack only.

## 11. Imported Debugging Notes

### 11.1 Notes from Jan 12 import

The following notes were copied from a rough debugging pad and were not fully normalized before being appended here.

- reranker looked OK on manuals
- on runbooks maybe top-6 > top-4 if exception section adjacent but not always
- watch duplicate section pulls / same heading repeated from mirrored docs
- release notes are weird because recommendation block may be tiny and earlier commentary dominates ranking
- one reviewer said “smaller bundle = less lying by completion” which is directionally right but not a formal metric
- keep this in mind:
  - if support is only partial don't let answer fill in global policy
  - if answer cites only document title review score drops fast
  - if heading path is unstable, coarse cite is safer than fake precision

### 11.2 Additional import

This subsection intentionally preserves the rougher formatting of the source notes.

1. pilot with anti-redundancy helped
2. but only when subsection labels were real labels
3. if headings are decorative, structure-aware packing inherits bad structure
4. page-derived text from PDF exports sometimes had better local blocks than sloppy Markdown
5. no final answer yet on release-note default

operational note - a few manual files had this shape:
feature notes
patch behavior
exceptions
follow-up
which means local navigation was poor even though file extension was markdown

more rough notes: same heading name reused in two different places made provenance look more precise than it was; this showed up in two annotated failures. keep an eye on section-path uniqueness when generating display citations.

## 12. Summary

These notes support adopting adaptive context packing as the default direction for structured technical manuals and many runbooks, with a strong benefit for supported lookup and citation usability.

They do not support a universal claim that one context budget is best across all corpora. They also do not support answering questions that depend on omitted charts, screenshots, or budgeting artifacts that were discussed separately from this text export.

Where evidence is mixed, the safe reading is narrower: adaptive packing improves some trust-related behaviors, but the release-notes subset and the global default decision remain unresolved.
