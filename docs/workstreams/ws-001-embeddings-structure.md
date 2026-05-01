# Embeddings Structure

## Summary

The embedding subsystem follows a lightweight port/adapter structure. Application code depends on
the `EmbeddingModel` contract, while concrete embedding implementations adapt either deterministic
local logic or an external model backend to that contract.

The boundary is:

```text
DocumentService -> EmbeddingModel port -> embedding adapter -> model backend
```

## Contract

`EmbeddingModel` is the application-facing contract for calculating embeddings:

```python
def embed_texts(texts: list[str]) -> list[list[float]]:
    ...
```

The service layer only needs this behavior. It does not know whether vectors come from a deterministic
hash implementation, sentence-transformers, or a future backend.

The contract currently returns plain Python lists. That keeps persistence and service code simple and
does not introduce a NumPy-native vector contract yet.

## Adapters

`DeterministicEmbeddingModel` is the deterministic adapter. It is used for stable development and test
behavior. It calculates normalized hash-based vectors without loading external model packages.

`SentenceTransformerEmbeddingModel` is the model-backed adapter. Its responsibility is to call a
sentence-transformers backend, request normalized embeddings, and coerce returned vector rows into the
application contract shape.

Sentence-transformers import and model construction live behind the sentence-transformer backend loader.
That keeps the adapter focused on embedding behavior and keeps optional dependency handling close to the
backend integration.

## Runtime Wiring

Application startup is the composition root. It reads `DOC_FORGE_EMBEDDING_MODEL` and injects one
singleton embedding model into `DocumentService`:

- `deterministic` selects `DeterministicEmbeddingModel`.
- `transformer` selects `SentenceTransformerEmbeddingModel`.

Runtime preflight checks stay in the application layer. For transformer mode, startup validates the
Docker-provided Hugging Face and Torch cache directories before constructing the model-backed adapter.

## Current Responsibilities

- `DocumentService` owns document ingestion workflow and asks the embedding contract for passage vectors.
- `EmbeddingModel` defines the application-level embedding calculation contract.
- Embedding adapters translate concrete implementations into that contract.
- Backend loaders own optional library imports and backend model construction.
- App startup owns configuration, runtime preflight, singleton creation, and dependency injection.
