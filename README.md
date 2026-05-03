# docforge

DocForge is a document question-answering service under construction. This
repository is organized around `mvp-0`: the Markdown-only walking skeleton of
DocForge, a narrow end-to-end slice that connects the main product flow before
adding PDFs, richer provenance, and broader answer behavior.

The walking skeleton is intentionally small, but it should remain executable,
deployable, and testable end to end. It is the foundation for future product
work and should later become the baseline path used by the evaluation
implementation.

## Command Model

Use Docker Compose for the default application runtime:

```bash
make docker-up-build
curl "$(make docker-url)/readyz"
make docker-down
```

Use the playground script to start the app and load a couple of Markdown
documents for UI exploration:

```bash
./scripts/dev.sh up-demo
```

Use `uv` for host environment management and Poe for Python developer tasks:

```bash
uv sync --group llm
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
curl "$(make docker-url)/readyz"
make docker-down
```

The Docker image uses `uv` only while building the locked virtual environment.
The final runtime container does not include or invoke `uv`; use `python` for
any in-container diagnostics.

Use `PORT` to change the host port while the container continues to listen on
port `8000`:

```bash
PORT=8080 make docker-up-build
curl http://127.0.0.1:8080/readyz
```

Runtime artifacts are mounted at `./data` on the host and `/artifacts` in the
container. Compose JSON logs are archived under `./data/logs/compose`. Make
passes the host UID/GID into Compose so files created in these bind mounts stay
editable by the local user.

Local clients should avoid assuming that `localhost` means the Docker host.
Use the discovery helper when a command may run from either the host shell or a
containerized development shell:

```bash
uv run python -m doc_forge.devtools.api_discovery
scripts/devex/resolve_api_base_url.py
```

The resolver checks `DOC_FORGE_API_BASE_URL` first. Without an explicit value,
it probes `127.0.0.1`, `host.docker.internal`, and `172.17.0.1` using the
configured `PORT`. Compose also exposes the API as `api:8000` and
`docforge-api:8000` for container-to-container calls.

Compose builds the default image with the LLM dependency group because
sentence-transformer-backed embeddings are the default runtime mode. To force the
deterministic development model:

```bash
DOC_FORGE_UV_SYNC_GROUPS="" \
DOC_FORGE_EMBEDDING_MODEL=deterministic \
make docker-up-build
```

## UI Playground

Start the Docker app and seed demo Markdown documents:

```bash
./scripts/dev.sh up-demo
```

The script uploads `evals/corpus/research-notes-1.md` and
`evals/corpus/config-reference-1.md` into the `default` corpus, then verifies
each upload through the document inspection endpoint. Open the printed `/ui`
URL to inspect the processed document structure and embedding metadata.

Seed an already-running app:

```bash
./scripts/dev.sh seed-demo
```

Reset the Docker runtime and reseed demo documents:

```bash
./scripts/dev.sh reset-demo
```

The current runtime stores documents in memory, so demo data is attached to the
running API process. Reseed after restarting the app. Override
`DOC_FORGE_DEMO_CORPUS_ID`, `DOC_FORGE_DEMO_DOCS`, or
`DOC_FORGE_API_BASE_URL` when you need a different corpus, document set, or API
target.
