# Runbooks

## Docker Transformer Embedding Model

Use this when the API container should run with sentence-transformer-backed
embeddings instead of the deterministic development model.

Start the Docker stack in transformer mode:

```bash
DOC_FORGE_UV_SYNC_GROUPS="--group llm" \
DOC_FORGE_EMBEDDING_MODEL=transformer \
make docker-up-build
```

Verify the API is reachable and the container has the expected embedding
configuration:

```bash
curl "$(make docker-url)/readyz"
docker compose exec -T api env | sort | rg 'DOC_FORGE_EMBEDDING_MODEL|TRANSFORMERS_OFFLINE|HF_HUB_OFFLINE|HF_HOME'
```

`DOC_FORGE_EMBEDDING_MODEL` selects the embedding regime and accepts
`deterministic` or `transformer`. Transformer mode uses the application default
sentence-transformers model. `HF_HOME` defaults to `/artifacts/huggingface`, so
the first online container run can populate the mounted cache. Set
`TRANSFORMERS_OFFLINE=1` and `HF_HUB_OFFLINE=1` only after the model is
available in that cache.

`/readyz` is the health endpoint. `/health` is not currently defined.

Remove downloaded model cache during cleanup:

```bash
uv run poe clean --include-model-cache
```
