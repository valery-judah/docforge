# Design Notes

This file captures delivery-level notes for the `mvp-0` Markdown-only walking
skeleton. Product scope belongs in `docs/evergreen/mvp.md`; current repo shape
belongs in `docs/delivery/architecture.md`.

## Conceptual Processing Pipeline

Markdown processing flow:

```text
Receive Markdown
  -> validate Markdown support
  -> create document identity
  -> extract text and recoverable heading paths
  -> generate and store embeddings
```

Query flow:

```text
Question
  -> embed question
  -> vector search filtered by active scope
  -> retrieve top-k evidence units
  -> assemble evidence payload with text and provenance
  -> decide answered vs insufficient_evidence from retrieved support
  -> generate answer from evidence or abstain
  -> render sources from used evidence
```

The support gate is part of the walking skeleton, but the exact scoring,
thresholding, and prompting strategy can evolve. The product invariant is stable:
answers must be grounded in retrieved Markdown evidence, and weak or absent
support must return `insufficient_evidence` instead of a fluent guess.
