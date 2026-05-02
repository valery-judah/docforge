  Current State
  The app already has a Pydantic settings boundary, but it is very narrow: src/doc_forge/app/settings.py:14 only owns DOC_FORGE_EMBEDDING_MODEL.

  The main mismatch with docs/workstreams/ws-002-config.md is that runtime config is split across places:

  - Settings reads only embedding_model.
  - src/doc_forge/app/runtime_checks.py:19 reads HF_HOME and TORCHINDUCTOR_CACHE_DIR directly from os.environ.
  - docker-compose.yml:9 defines app-like config that the app does not model: DOC_FORGE_ARTIFACT_ROOT, DOC_FORGE_SERVICE_NAME, DOC_FORGE_JSON_LOG_PATH, offline flags, cache paths.
  - .env.example:3 appears stale for the current app: it documents answer-generator/Ollama config, but the current architecture only wires embeddings.
  - src/doc_forge/app/dependencies.py:46 eagerly creates the service singleton at module import time, so settings validation and model construction happen on import rather than an explicit
    startup/container boundary.

  Recommended Refactor
  I would do this incrementally, not as a broad rewrite.

  1. Expand Settings into the single application config boundary.

  Useful first fields:

  environment: str = "dev"
  artifact_root: Path = Path("./data")
  service_name: str = "doc_forge-api"
  json_log_path: Path | None = None
  embedding_model: EmbeddingModelRegime = EmbeddingModelRegime.DETERMINISTIC
  hf_home: Path | None = None
  torchinductor_cache_dir: Path | None = None
  hf_hub_offline: bool = False
  transformers_offline: bool = False

  For HF_HOME and TORCHINDUCTOR_CACHE_DIR, I’d probably support legacy third-party env names via aliases while introducing namespaced app vars such as DOC_FORGE_HF_HOME /
  DOC_FORGE_TORCHINDUCTOR_CACHE_DIR.

  2. Move transformer cache validation to use Settings, not os.environ.

  runtime_checks.validate_runtime(settings) should check settings.hf_home and settings.torchinductor_cache_dir. It can still create directories there; keep side effects out of Pydantic
  validators.

  3. Add SettingsConfigDict(secrets_dir="/run/secrets").

  There are no real app secrets yet, but adding the source now matches ws-002-config.md and avoids changing the pattern later.

  4. Add a safe settings summary.

  Something like settings.safe_summary() returning non-secret values:

  {
      "environment": "dev",
      "embedding_model": "deterministic",
      "artifact_root": "...",
      "transformer_cache_configured": true,
  }

  Do not log full DSNs, tokens, secrets, or future credentials.

  5. Clean up deployment config docs/examples.

  Update .env.example so it reflects the current app, especially DOC_FORGE_EMBEDDING_MODEL, artifact root, environment, and transformer cache/offline knobs. Move answer-generator/Ollama values
  out unless that feature still exists in a pending branch.

  6. Consider replacing eager module-level composition.

  Instead of _document_service = _create_document_service() at import time, introduce an app container/factory boundary. That gives tests and future deployment modes a cleaner way to inject
  settings and keeps startup failure explicit.

  Likely First PR
  A tight first PR could change only:

  - src/doc_forge/app/settings.py:14
  - src/doc_forge/app/runtime_checks.py:12
  - tests/test_app_settings.py:9
  - tests/test_runtime_checks.py:9
  - .env.example:1
  - maybe docker-compose.yml:9

  That would align the app with the workstream’s main rule: one typed config interface, env vars as the runtime source, and startup validation before serving traffic.

