# Eval Case Storage

Phase zero uses a folder-per-slice layout.

## Shared files

Keep shared schema files at the top of `evals/cases/`:

* `cases.schema.json`
* `answer_keys.schema.json`

These define the record shapes used by authored case sets.

The shared schemas are a matrix-ready superset aligned with the case families in
[`30_building_case_matrix.md`](docs/workstreams/WS-003-seed-corpus/30_building_case_matrix.md).
Individual authored sets may use only a narrow subset of the allowed enums and fields.

## Authored sets

Store each authored slice under `evals/cases/sets/<set_id>/`.

Each set folder should contain:

* `cases.jsonl`
* `answer_keys.jsonl`

Example:

* `evals/cases/sets/supported_lookup_research_1/cases.jsonl`
* `evals/cases/sets/supported_lookup_research_1/answer_keys.jsonl`
* `evals/cases/sets/supported_source_navigation/cases.jsonl`
* `evals/cases/sets/supported_source_navigation/answer_keys.jsonl`

## Naming guidance

Choose set names that make the slice obvious from the path:

* scenario family first
* source bundle second

Example:

* `supported_lookup_research_1`

## Current rule

Until the dataset packaging scheme is refactored, do not add top-level authored payload files such as `evals/cases/cases.jsonl` or `evals/cases/answer_keys.jsonl`.

## Shared vs set-specific rules

Use the shared schemas for:

* allowed case families
* allowed question classes
* allowed support states
* allowed provenance modes
* allowed expected behaviors

Use set-specific validation for narrower local conventions, such as:

* one gold source only
* Markdown-only slices
* fixed support state for a given set
* exact section grounding against a specific source document
