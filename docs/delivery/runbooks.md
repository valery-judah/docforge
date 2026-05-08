# Runbooks

## Docker Runtime Basics

Use Docker Compose for the default application runtime:

```bash
make docker-up-build
curl "$(make docker-url)/readyz"
make docker-down
```

The Docker image uses `uv` only while building the locked virtual environment.
The final runtime container does not include or invoke `uv`; use `python` for
in-container diagnostics.

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

`/readyz` is the health endpoint. `/health` is not currently defined.

## Demo Playground

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

For the full live QA assertion workflow, see
[smoke-test-e2e.md](smoke-test-e2e.md).

## Local Answer Synthesis

The default answer backend is Ollama with `qwen3.5:9b`:

```bash
ollama pull qwen3.5:9b
uv run poe run-api
```

Host-local app runs default to:

```bash
DOC_FORGE_ANSWER_SYNTHESIZER_BACKEND=ollama
DOC_FORGE_ANSWER_SYNTHESIZER_MODEL=qwen3.5:9b
DOC_FORGE_OLLAMA_BASE_URL=http://127.0.0.1:11434
DOC_FORGE_ANSWER_SYNTHESIS_TIMEOUT_SECONDS=90
```

The checked-in `.env.example` intentionally does not enable
`DOC_FORGE_OLLAMA_BASE_URL` by default. Set it explicitly when you want the
Ollama backend, based on how the API is running:

- host-local API process: `http://127.0.0.1:11434`
- Docker Compose API container: `http://host.docker.internal:11434`

Docker Compose already defaults to `http://host.docker.internal:11434` for
Ollama so the container can call a host-local Ollama runtime. Do not override
that with `127.0.0.1` unless Ollama is running inside the same container. If
Ollama is not reachable, the API still starts and document ingestion still
works, but `POST /corpora/{corpus_id}/answers/query` returns `503`.

For tests or explicitly offline work, switch answering back to the
deterministic adapter:

```bash
DOC_FORGE_ANSWER_SYNTHESIZER_BACKEND=deterministic uv run poe verify
DOC_FORGE_EMBEDDING_MODEL=deterministic DOC_FORGE_ANSWER_SYNTHESIZER_BACKEND=deterministic make docker-up-build
```

## Docker Transformer Embedding Model

Use this when the API container should run with the default
sentence-transformer-backed embeddings.

Start the Docker stack in transformer mode:

```bash
make docker-up-build
```

Verify the API is reachable and the container has the expected embedding
configuration:

```bash
curl "$(make docker-url)/readyz"
docker compose exec -T api env | sort | rg 'DOC_FORGE_EMBEDDING_MODEL|DOC_FORGE_TRANSFORMERS_OFFLINE|DOC_FORGE_HF_HUB_OFFLINE|DOC_FORGE_HF_HOME|DOC_FORGE_TORCHINDUCTOR_CACHE_DIR'
docker compose exec -T api python -c 'import doc_forge; print("python runtime ok")'
```

`DOC_FORGE_EMBEDDING_MODEL` selects the embedding regime and accepts
`deterministic` or `transformer`; `transformer` is the default. Compose builds
the image with the LLM dependency group by default so the default runtime has
the sentence-transformers backend installed. Transformer mode uses the
application default sentence-transformers model. If cache paths are not
explicitly configured, the application derives them from
`DOC_FORGE_ARTIFACT_ROOT`: `huggingface` for `DOC_FORGE_HF_HOME` and
`torchinductor-cache` for `DOC_FORGE_TORCHINDUCTOR_CACHE_DIR`. In Compose,
those paths resolve under `/artifacts`, so the first online container run can
populate the mounted cache. Application startup preflight validates these cache
paths and exports third-party library environment names before loading the
transformer model. Set `DOC_FORGE_TRANSFORMERS_OFFLINE=1` and
`DOC_FORGE_HF_HUB_OFFLINE=1` only after the model is available in the mounted
Hugging Face cache.

The API container runtime does not include `uv`. Use `python` for container
diagnostics; reserve `uv run ...` for host-side developer workflows. Make passes
the host UID/GID into Compose so bind-mounted artifacts, logs, and downloaded
model cache files remain editable from the host.

Remove downloaded model cache during cleanup:

```bash
uv run poe clean --include-model-cache
```
