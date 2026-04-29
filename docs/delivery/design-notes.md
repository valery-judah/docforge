

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
  -> decide answered vs insufficient_evidence (how?)
  -> generate answer from evidence or abstain (what are the criteria, could we even do this?)
  -> render sources from used evidence
```

