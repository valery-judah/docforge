# Runbooks

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
the image with the LLM dependency group by default so the default runtime has the
sentence-transformers backend installed. Transformer mode uses the application
default sentence-transformers model. If cache paths are not explicitly
configured, the application derives them from `DOC_FORGE_ARTIFACT_ROOT`:
`huggingface` for `DOC_FORGE_HF_HOME` and `torchinductor-cache` for
`DOC_FORGE_TORCHINDUCTOR_CACHE_DIR`. In Compose, those paths resolve under
`/artifacts`, so the first online container run can populate the mounted cache.
Application startup preflight validates these cache paths and exports third-party
library environment names before loading the transformer model. Set
`DOC_FORGE_TRANSFORMERS_OFFLINE=1` and `DOC_FORGE_HF_HUB_OFFLINE=1` only after the
model is available in the mounted Hugging Face cache.

The API container runtime does not include `uv`. Use `python` for container
diagnostics; reserve `uv run ...` for host-side developer workflows. Make passes
the host UID/GID into Compose so bind-mounted artifacts, logs, and downloaded
model cache files remain editable from the host.

`/readyz` is the health endpoint. `/health` is not currently defined.

Remove downloaded model cache during cleanup:

```bash
uv run poe clean --include-model-cache
```
