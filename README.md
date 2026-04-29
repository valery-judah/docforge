# docforge

DocForge Python service scaffold.

## Command Model

Use `uv` for environment management and Poe for Python developer tasks:

```bash
uv sync
uv run poe fmt
uv run poe lint
uv run poe type
uv run poe test
uv run poe verify
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
