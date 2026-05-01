#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd)

PORT="${PORT:-8000}"
API_URL="${DOC_FORGE_API_BASE_URL:-http://127.0.0.1:$PORT}"
API_URL="${API_URL%/}"
DEMO_CORPUS_ID="${DOC_FORGE_DEMO_CORPUS_ID:-default}"
DEMO_DOCS="${DOC_FORGE_DEMO_DOCS:-evals/corpus/research-notes-1.md evals/corpus/config-reference-1.md}"
READY_TIMEOUT_SECONDS="${DOC_FORGE_READY_TIMEOUT_SECONDS:-60}"

cd "$REPO_ROOT"

usage() {
  cat <<'EOF'
Usage: scripts/dev.sh {up-demo|docker|local|seed-demo|playground|reset-demo|down|logs}

Commands:
  up-demo      Build and start Docker, upload demo docs, then print the UI URL.
  docker       Build and start the Docker Compose API, then print the UI URL.
  local        Run the API locally with uv and Poe.
  seed-demo    Upload demo Markdown docs and verify processing through inspection.
  playground  Alias for up-demo.
  reset-demo   Remove Compose volumes, start Docker, seed demo docs, then print the UI URL.
  down         Stop the Docker Compose API.
  logs         Follow Docker Compose API logs.

Environment:
  PORT                         Host port for the API. Default: 8000
  DOC_FORGE_API_BASE_URL       API base URL. Default: http://127.0.0.1:$PORT
  DOC_FORGE_DEMO_CORPUS_ID     Corpus seeded for UI exploration. Default: default
  DOC_FORGE_DEMO_DOCS          Space-separated Markdown files to upload.
  DOC_FORGE_READY_TIMEOUT_SECONDS
                               Seconds to wait for /readyz. Default: 60
EOF
}

ui_url() {
  printf '%s/ui\n' "$API_URL"
}

wait_ready() {
  elapsed=0
  while [ "$elapsed" -lt "$READY_TIMEOUT_SECONDS" ]; do
    if curl -fsS "$API_URL/readyz" >/dev/null; then
      return 0
    fi

    elapsed=$((elapsed + 1))
    sleep 1
  done

  echo "API did not become ready at $API_URL within ${READY_TIMEOUT_SECONDS}s." >&2
  return 1
}

document_id_from_response() {
  uv run python -c 'import json, sys; print(json.load(sys.stdin)["document_id"])'
}

seed_demo() {
  wait_ready

  for document_path in $DEMO_DOCS; do
    if [ ! -f "$document_path" ]; then
      echo "Demo document not found: $document_path" >&2
      return 1
    fi

    echo "Uploading $document_path to corpus $DEMO_CORPUS_ID"
    upload_response=$(
      curl -fsS \
        -F "file=@${document_path}" \
        "$API_URL/corpora/$DEMO_CORPUS_ID/documents"
    )
    document_id=$(printf '%s' "$upload_response" | document_id_from_response)

    echo "Verifying processed inspection for $document_id"
    curl -fsS \
      "$API_URL/corpora/$DEMO_CORPUS_ID/documents/$document_id/inspection" \
      >/dev/null
  done

  echo "Seeded demo corpus: $DEMO_CORPUS_ID"
}

up_demo() {
  make docker-up-build
  seed_demo
  echo "UI: $(ui_url)"
}

case "${1:-}" in
  up-demo)
    up_demo
    ;;
  docker)
    make docker-up-build
    wait_ready
    echo "UI: $(ui_url)"
    ;;
  local)
    exec uv run poe run-api
    ;;
  seed-demo)
    seed_demo
    ;;
  playground)
    up_demo
    ;;
  reset-demo)
    make docker-clean
    make docker-up-build
    seed_demo
    echo "UI: $(ui_url)"
    ;;
  down)
    make docker-down
    ;;
  logs)
    docker compose logs -f api
    ;;
  -h | --help | help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
