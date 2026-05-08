# Evaluation Notes

`mvp-0` is the baseline implementation path for current evaluation work. The
baseline should stay deliberately small and exercise the Markdown-only system
spine that the repository can prove today.

## Current Proven Baseline

The current baseline is established by targeted tests and API checks, not only
by the demo smoke harness.

Covered behaviors:

| Behavior                      | Current proof surface                                                     |
| ----------------------------- | ------------------------------------------------------------------------- |
| Markdown ingestion            | Upload, validation, stable identity, and no partial ingestion on failure. |
| Evidence inspection           | Document structure, heading context, passage order, and provenance spans. |
| Scoped retrieval              | Retrieval returns passages from the active corpus only.                   |
| Answer or abstention          | Answer responses include source passages; weak support returns abstention. |
| Cross-corpus isolation        | Document access and retrieval are limited to the requested corpus.        |

Minimum pass conditions for the current baseline:

- Markdown documents become queryable only after successful ingestion.
- Retrieved evidence remains connected to real Markdown documents and passage
  provenance.
- Answered responses return retrieved source passages.
- `insufficient_evidence` is returned when retrieved support is absent or below
  threshold.
- Cross-scope evidence leakage does not occur in targeted tests.

## Demo Smoke Harness

The shipped demo smoke harness is narrower than the full targeted baseline. It
currently serves as a lightweight live-runtime check for:

- supported answered cases over the seeded demo corpus
- an `insufficient_evidence` case
- basic response-shape and evidence-presence validation

It should not be treated as the sole definition of evaluation coverage.

## Future Expansion

The broader future eval pack can extend this baseline once the implementation
and measurements exist. Expected future additions include:

- richer unsupported, ambiguous, conflicting, and partial-support cases
- broader source-navigation and provenance grading
- cross-scope checks in the shipped smoke harness itself
- evaluation for future PDF and mixed-format capabilities
