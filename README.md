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

## Docker

Build and run the API container through Compose:

```bash
make docker-up-build
curl http://127.0.0.1:8000/readyz
make docker-down
```

Use `PORT` to change the host port while the container continues to listen on
port `8000`:

```bash
PORT=8080 make docker-up-build
curl http://127.0.0.1:8080/readyz
```

Runtime artifacts are mounted at `./data` on the host and `/artifacts` in the
container. Compose JSON logs are archived under `./data/logs/compose`.
