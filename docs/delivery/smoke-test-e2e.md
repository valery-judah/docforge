# End-to-End Smoke Test

Use this runbook to execute the live QA smoke path against the seeded demo
corpus with the Ollama-backed answer synthesizer.

This check exercises the full operator path:

- Docker API startup
- demo corpus seeding
- live answer synthesis through Ollama
- the three-question `demo_answer_smoke` scenario

## Success Criteria

The smoke run is successful when:

- question 1 returns `state=answered`
- question 2 returns `state=answered`
- question 3 returns `state=insufficient_evidence`

Expected console output:

```text
Running QA smoke check against http://.../corpora/default
[1/3] PASS answered: What is the interactive target for the full retrieval and answer generation path?
[2/3] PASS answered: What is the maximum length for request_id?
[3/3] PASS insufficient_evidence: What is the CEO approval policy for production incidents?
Smoke check passed: 3/3 questions.
```

## Preconditions

- Docker is available
- Ollama is running on the host
- Ollama has `qwen3.5:9b` available

Verify the model on the host:

```bash
ollama list | rg 'qwen3.5:9b'
```

If needed:

```bash
ollama pull qwen3.5:9b
```

For general Docker runtime and local Ollama setup, see
[runbooks.md](runbooks.md).

## Standard Host Workflow

Use this when the host shell can reach the published API port.

Start the demo stack and seed the demo corpus:

```bash
./scripts/dev.sh up-demo
```

Run the live smoke check:

```bash
uv run poe demo-qa-smoke
```

Stop the stack when finished:

```bash
make docker-down
```

## Fallback Docker-Network Workflow

Use this when the API container is healthy but the host shell cannot reach the
published API port, or when Docker needs an explicit writable config
directory.

Prepare writable Docker paths for this shell:

```bash
mkdir -p .tmp/codex-home .tmp/docker-config
export HOME="$PWD/.tmp/codex-home"
export DOCKER_CONFIG="$PWD/.tmp/docker-config"
```

Start the API container:

```bash
make docker-up-build
```

Seed the demo corpus from inside the Docker network:

```bash
docker run --rm -i --network docforge_default -v "$PWD/evals:/evals:ro" docforge-api:latest python - <<'PY'
import json
import mimetypes
import uuid
import urllib.request
from pathlib import Path

base_url = "http://docforge-api:8000"
corpus_id = "default"
paths = [
    Path("/evals/corpus/research-notes-1.md"),
    Path("/evals/corpus/config-reference-1.md"),
]

for path in paths:
    boundary = f"----docforge{uuid.uuid4().hex}"
    content = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'.encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            content,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    request = urllib.request.Request(
        f"{base_url}/corpora/{corpus_id}/documents",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode())
    document_id = payload["document_id"]
    with urllib.request.urlopen(
        f"{base_url}/corpora/{corpus_id}/documents/{document_id}/inspection",
        timeout=120,
    ) as response:
        response.read()
    print(f"uploaded {path.name} {document_id}")

print("seeded demo corpus")
PY
```

Run the smoke check from inside the same Docker network:

```bash
docker run --rm --network docforge_default docforge-api:latest \
  python -m doc_forge.devtools.demo_answer_smoke \
  --api-base-url http://docforge-api:8000
```

Stop the stack when finished:

```bash
make docker-down
```

## Expected Questions

The smoke test currently asserts these exact questions:

1. `What is the interactive target for the full retrieval and answer generation path?`
2. `What is the maximum length for request_id?`
3. `What is the CEO approval policy for production incidents?`

Expected behavior:

1. question 1 is answered from the demo corpus
2. question 2 is answered from the demo corpus
3. question 3 abstains with `insufficient_evidence`

## Troubleshooting

If `up-demo` or `make docker-up-build` fails with a Docker config permission
error under `/tmp/codex-home/.docker`, use the fallback workflow with explicit
`HOME` and `DOCKER_CONFIG`.

If the smoke check returns `503`, verify the API container is using
`DOC_FORGE_OLLAMA_BASE_URL=http://host.docker.internal:11434` and that
`qwen3.5:9b` is available in the host Ollama runtime.

If the API is healthy in container logs but `curl http://127.0.0.1:8000/readyz`
fails from the host shell, use the fallback Docker-network workflow instead of
the host workflow.

If you want the smoke helper to prepare the runtime before querying, use:

```bash
uv run python -m doc_forge.devtools.demo_answer_smoke --prepare-demo up-demo
```
