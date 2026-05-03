# Agent Contract

## Canonical sources
- `docs/evergreen/mvp.md` - product scope
- `docs/delivery/architecture.md` - architecture and current repo shape

`docs/evergreen/mvp.md` is the canonical product source. `docs/delivery/architecture.md` is the current architecture source until it is promoted or superseded. `docs/archive/` is history-only.

## Repo Description
DocForge is a document question-answering service under construction. This repo
is organized around `mvp-0`, the Markdown-only walking skeleton: a thin vertical
slice through the future QA service flow before PDFs, richer provenance, and
broader answer behavior are added. Treat this as an end-to-end product spine,
not a horizontal base layer; later evaluation work should reuse this skeleton as
the baseline implementation path.

## Commands
- Use `uv` as the Python command entrypoint for this repo.
- Prefer `uv run poe <task>` for defined developer workflows; otherwise use `uv run <tool>`.
- Do not use `pip`, `python -m pip`, `poetry`, `pipenv`, `npm`, or `npx` for repo workflows.
- Use `make` for local DevEx and infrastructure wrappers such as Docker, Docker Compose, observability stack operations, and docs harness helpers like `make workstream-new type=<work_type> slug=<slug>`, as defined in [`Makefile`](Makefile).
- Common anchors: `uv sync`, `uv run poe verify`, `uv run poe run-api`, `make docker-up-build`, `make workstream-new type=feature slug=my-feature`.
- To inspect the current command surface directly, use `uv run poe --help` and `make help`.

## Validation
- Docs-only change: no mandatory validation; run targeted checks only if docs affect commands or generated artifacts.
- Code change: `uv run poe verify`

## Development Practices
- Save any temporary, exploratory, or developer-experience (devex) scripts into the `scripts/devex/` directory.
