Yes. At a high level, the case matrix should be a **coverage map for the MVP trust contract**, not a full combinatorial grid. The rubric already gives the right base dimensions: each case has a **support state**, a **question class**, a **minimum provenance expectation**, and then a run-level judgment over support alignment, scope control, provenance quality, abstention behavior, and trust outcome. The recommended first eval set also already names the scenario families that should exist in the matrix: direct lookup in PDF and Markdown, mixed synthesis, source navigation, partial support, unsupported-in-corpus, out-of-scope questions, conflicting-source questions, and malformed or weakly structured documents. 

So I would define the matrix with four practical axes:

1. **Support state**
   `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED_IN_CORPUS`, `UNSUPPORTED_QUESTION_TYPE`, `AMBIGUOUS_OR_CONFLICTING`. 

2. **Question class**
   `factual_lookup`, `localized_explanation`, `multi_source_synthesis`, `source_navigation`, plus the explicit partial/unsupported/ambiguous classes already in the rubric. 

3. **Source condition**
   `pdf`, `markdown`, `mixed`, and a structure-quality slice such as `clean`, `weak_structure`, `scanned_or_ocr_poor`. The rubric already expects slicing by source type and explicitly includes malformed or weakly structured document cases. 

4. **Primary target failure**
   One of your eight first-class failures: `U1`, `U2`, `A1`, `A2`, `P1`, `P2`, `I1`, `S1`. The rubric explicitly says these are the failures that matter most for Version 1, with `U1/U2/A2/P2/S1` treated as priority trust defects.

The main design point is: **do not build the full Cartesian product**. Many cells are low value. Instead, use a curated matrix where each row is a case family designed to expose one or two top-level failures. That matches the rubric’s annotation flow, which starts with support state and provenance expectation, then scores behavior, then assigns a primary failure label.

A clean high-level matrix would look like this:

| Case family                     | Support state               |      Typical source type | Main question class                          | Primary target failures          | Expected correct behavior                                  |
| ------------------------------- | --------------------------- | -----------------------: | -------------------------------------------- | -------------------------------- | ---------------------------------------------------------- |
| Supported direct lookup         | `SUPPORTED`                 |           PDF / Markdown | `factual_lookup`                             | `A1`, `P1`, `P2`                 | Answer directly, cite inspectably                          |
| Supported source navigation     | `SUPPORTED`                 |           PDF / Markdown | `source_navigation`                          | `A1`, `P1`, `P2`                 | Point user to right doc/page/section                       |
| Supported localized explanation | `SUPPORTED`                 |           PDF / Markdown | `localized_explanation`                      | `U1`, `P1`, `P2`                 | Explain only what cited text supports                      |
| Partial-support answer          | `PARTIALLY_SUPPORTED`       |         Mixed often best | `partial_support` / `multi_source_synthesis` | `U2`, `A2`, `P1`                 | Narrow or qualify; do not complete unsupported gaps        |
| Unsupported in corpus           | `UNSUPPORTED_IN_CORPUS`     |                      Any | usually lookup / synthesis                   | `A2`, `U1`                       | Abstain or explicitly state corpus does not support answer |
| Out-of-scope question           | `UNSUPPORTED_QUESTION_TYPE` |              PDF / Mixed | `unsupported_scope`                          | `S1`, `A2`                       | State capability limit; do not answer as grounded          |
| Ambiguous/conflicting evidence  | `AMBIGUOUS_OR_CONFLICTING`  |         Mixed often best | `ambiguous_conflict`                         | `A2`, `U2`, `P1`                 | Surface conflict or qualify by source                      |
| Ingestion / structure stress    | varies                      | weak PDF / weak Markdown | any of the above                             | `I1`, `P1`, `P2`, sometimes `A1` | Preserve enough structure to answer or fail honestly       |

This structure is directly aligned with the rubric’s canonical examples: supported, partially supported, unsupported in corpus, unsupported question type, and ambiguous/conflicting, plus the recommended first evaluation set that adds direct lookup, mixed synthesis, source navigation, and malformed/weakly structured inputs. 

I would also make **provenance expectation** an explicit sub-column in the matrix, because the rubric treats inspectable provenance as part of the product contract and already distinguishes acceptable minimums by source type: PDFs often require page-level provenance, Markdown often requires section-level provenance, and some cases should demand both when recoverable.

So, in practice, the matrix is not really “question type by question type.” It is:

**case family × support state × source condition × target failure**

That gives you a planning view that is small enough to operate, but still faithful to the MVP evaluation logic.

My recommended top-level buckets for the matrix are these eight:

* supported lookup
* supported navigation
* supported localized explanation
* partial-support synthesis
* unsupported-in-corpus
* unsupported-question-type
* ambiguous/conflicting
* ingestion/structure stress 

That is the overview I would use as the backbone. The next step would be to turn each bucket into 3–6 concrete cases and attach source-type coverage and provenance expectations.
