# Evaluation Notes

`mvp-0` should become the baseline implementation path for evaluation work. The
first evaluation pack should stay deliberately small and exercise the
Markdown-only walking skeleton end to end before adding PDF, mixed-format, or
richer support-state cases.

## Minimal Smoke Evaluation

The first smoke eval should be deliberately small: 4 to 6 questions over 2 to 3 Markdown files.

Required cases:

| Case                                  | Purpose                                                                  |
| ------------------------------------- | ------------------------------------------------------------------------ |
| Supported factual lookup              | Proves retrieval, answering, and citation for a direct fact.             |
| Localized explanation                 | Proves a short explanation can stay grounded in local Markdown evidence. |
| Unsupported in corpus                 | Proves the system returns `insufficient_evidence` instead of guessing.   |
| Source navigation or provenance check | Proves returned references resolve to real retrieved evidence.           |
| Cross-scope leakage check             | Proves retrieval does not return evidence from another scope.            |

Minimum pass conditions:

- Supported questions return relevant Markdown evidence.
- Unsupported questions do not produce confident unsupported answers.
- Source references resolve to actual Markdown documents and heading paths where available.
- No answer cites a source that was not retrieved and used.
- Cross-scope evidence leakage does not occur.
