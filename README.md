# docforge

DocForge is a document question-answering service under construction. This
repository is organized around `mvp-0`: the Markdown-only architectural
walking skeleton of DocForge. It is a narrow executable slice that both
connects the main product flow and validates the core architecture before
adding PDFs, richer provenance, and broader answer behavior.

This slice is intentionally small, but it should remain executable,
deployable, and testable end to end. It is the architectural foundation for
future product work and should later become the baseline path used by the
evaluation implementation.

## Command Model

Use `uv` for host environment management and Poe for Python developer tasks:

```bash
uv sync --group llm
uv run poe verify
uv run poe run-api
```

Use `make` for local infrastructure wrappers:

```bash
make help
make docker-up-build
make docker-down
make observability-up-build
make observability-down
```

The task-runner split mirrors the `sem-rag` setup:

- `pyproject.toml`: package metadata, dependency groups, and tool config
- `poe_tasks.toml`: Python task catalog
- `Makefile`: Docker, Compose, and local DevEx wrappers
- `uv.toml`: repo-local uv cache configuration

## Where To Go

- Product scope: [docs/evergreen/mvp.md](docs/evergreen/mvp.md)
- Current architecture: [docs/delivery/architecture.md](docs/delivery/architecture.md)
- macOS install guide: [docs/delivery/install-macos.md](docs/delivery/install-macos.md)
- Runtime and setup runbooks: [docs/delivery/runbooks.md](docs/delivery/runbooks.md)
- End-to-end smoke test runbook: [docs/delivery/smoke-test-e2e.md](docs/delivery/smoke-test-e2e.md)

Use the macOS install guide when you need a contributor workstation setup from
scratch. Use the smoke runbook when you want to start the demo stack, seed the
demo corpus, run the live QA smoke scenario, or troubleshoot answer-path
failures.
