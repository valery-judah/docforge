# Install DocForge On macOS

Use this guide to set up DocForge on macOS for local or Docker-based
development.

## What You Need

DocForge needs:

- `git` for cloning and updating the repo
- `uv` for Python environment and task management
- Docker Desktop for the default containerized runtime
- Ollama for the default answer-synthesis backend
- the `qwen3.5:9b` Ollama model for the live QA path

Assumptions:

- macOS with Apple Silicon or Intel
- enough free disk for Docker images, local artifacts, and Ollama models
- a shell with `curl`

## Install Prerequisites

### 1. Verify `git`

Check first:

```bash
git --version
```

If `git` is missing, install the standard macOS developer tools:

```bash
xcode-select --install
git --version
```

### 2. Install Homebrew

Homebrew is the simplest way to install the remaining tools.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew --version
```

### 3. Install `uv`

DocForge uses `uv` for Python environments and tasks.

Homebrew:

```bash
brew install uv
```

Official standalone installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:

```bash
uv --version
```

### 4. Install Docker Desktop

Docker Desktop is the supported Docker path for this repo.

Homebrew:

```bash
brew install --cask docker
open -a Docker
```

Or install it directly from Docker.

Verify once Docker Desktop has finished starting:

```bash
docker version
docker compose version
```

Notes:

- Docker Desktop requires a supported macOS release and at least 4 GB of RAM.
- On Apple Silicon, Docker recommends Rosetta 2 for the best experience with
  some optional AMD64 tools:

```bash
softwareupdate --install-rosetta
```

### 5. Install Ollama

Ollama is the default answer backend for interactive QA.

Homebrew:

```bash
brew install --cask ollama
open -a Ollama
```

Or install it directly from Ollama.

Verify:

```bash
ollama --version
```

Pull the model used by the default DocForge answer path:

```bash
ollama pull qwen3.5:9b
```

Check that it is available:

```bash
ollama list | grep 'qwen3.5:9b'
```

## Prepare The Repo

Clone the repository and install the locked Python environment:

```bash
git clone <repo-url>
cd docforge
uv sync --group llm
```

Run the read-only verification suite once to confirm the workstation setup:

```bash
uv run poe verify
```

Useful command discovery:

```bash
uv run poe --help
make help
```

## Run DocForge Locally

Use this path when you want the FastAPI app to run directly on the host.

Start the API:

```bash
./scripts/dev.sh local
```

Equivalent command:

```bash
uv run poe run-api
```

Local runtime defaults:

```bash
DOC_FORGE_ANSWER_SYNTHESIZER_BACKEND=ollama
DOC_FORGE_ANSWER_SYNTHESIZER_MODEL=qwen3.5:9b
DOC_FORGE_OLLAMA_BASE_URL=http://127.0.0.1:11434
DOC_FORGE_ANSWER_SYNTHESIS_TIMEOUT_SECONDS=90
```

Verify the app:

```bash
curl http://127.0.0.1:8000/readyz
open http://127.0.0.1:8000/ui
```

## Run The Docker Demo Stack

Use this path when you want the default containerized runtime plus the seeded
demo corpus.

Start the stack, wait for readiness, seed the demo corpus, and print the UI
URL:

```bash
./scripts/dev.sh up-demo
```

Other useful runtime commands:

```bash
./scripts/dev.sh seed-demo
./scripts/dev.sh reset-demo
./scripts/dev.sh down
```

The Docker API container defaults to:

```bash
DOC_FORGE_OLLAMA_BASE_URL=http://host.docker.internal:11434
```

That allows the container to call the Ollama process running on the host Mac.

Verify the stack:

```bash
curl "$(make docker-url)/readyz"
open "$(make docker-url)/ui"
```

For the full live QA assertion flow, including expected questions and fallback
network execution, see [smoke-test-e2e.md](smoke-test-e2e.md).

## Which Script Should You Run?

Use these defaults:

- `./scripts/dev.sh local`: run the API directly on the host
- `./scripts/dev.sh up-demo`: start the Docker stack and seed demo documents
- `./scripts/dev.sh seed-demo`: seed the demo corpus into an already running app
- `./scripts/dev.sh down`: stop the Docker stack
- `uv run poe verify`: validate the local code environment

## Troubleshooting

If `POST /corpora/{corpus_id}/answers/query` returns `503`, Ollama is usually
not reachable from the API runtime. Check:

- host-local app: `DOC_FORGE_OLLAMA_BASE_URL=http://127.0.0.1:11434`
- Docker app: `DOC_FORGE_OLLAMA_BASE_URL=http://host.docker.internal:11434`
- model availability: `ollama list | grep 'qwen3.5:9b'`

If Docker is healthy but `curl http://127.0.0.1:8000/readyz` fails from your
current shell, use the discovered base URL instead:

```bash
make docker-url
```

Some containerized development shells resolve the Docker host differently than
the macOS host shell.

If Docker fails with a config permission error under a temporary home
directory, run with explicit writable paths:

```bash
mkdir -p .tmp/codex-home .tmp/docker-config
export HOME="$PWD/.tmp/codex-home"
export DOCKER_CONFIG="$PWD/.tmp/docker-config"
make docker-up-build
```

For deeper runtime operations, see [runbooks.md](runbooks.md). For the live QA
smoke path, see [smoke-test-e2e.md](smoke-test-e2e.md).

## Sources

- `uv` installation: <https://docs.astral.sh/uv/getting-started/installation/>
- Docker Desktop for Mac: <https://docs.docker.com/desktop/setup/install/mac-install/>
- Ollama on macOS: <https://docs.ollama.com/macos>
