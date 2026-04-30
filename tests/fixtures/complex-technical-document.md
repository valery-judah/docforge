# DocForge Operator Guide

This guide explains how operators prepare DocForge for local ingestion. It intentionally includes inline **formatting**, `commands`, and a [reference link](https://example.test/docs) so the parser preserves the original Markdown passage text.

## Environment Setup

Create the local environment before starting services.

1. Run `uv sync`.
2. Copy `.env.example` to `.env`.
3. Confirm PostgreSQL is reachable.

> Keep local credentials out of committed documentation.
> Rotate shared secrets after demos.

```markdown
# This heading is inside a fenced code block and must not create a section
## Neither should this one
```

### Configuration Matrix

| Setting | Default | Purpose |
|---|---|---|
| DOCFORGE_ENV | local | Selects local runtime defaults. |
| DOCFORGE_LOG_LEVEL | info | Controls structured log verbosity. |

Use the matrix when reviewing pull requests that alter runtime behavior.

## Ingestion Workflow

Upload Markdown documents through the API.

- Confirm the corpus exists.
- Submit the document record.
- Confirm parsing and embedding finished before the upload response returned.

### Failure Modes

A failed parse should leave the original document available for inspection.

```text
parse failed: unsupported document type
```

## Environment Setup

This repeated heading represents a troubleshooting section with the same title as an earlier section.

### Verification

Run `uv run poe verify` before handoff.

Check the generated structure JSON and confirm every passage remains under the expected section path.
