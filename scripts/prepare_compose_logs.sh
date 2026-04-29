#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
log_root="${repo_root}/data/logs/compose"
run_id="${DOC_FORGE_LOG_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
run_dir="${log_root}/runs/${run_id}"
latest_dir="${log_root}/latest"

mkdir -p "$run_dir" "$latest_dir"

ln -sfn "../runs/${run_id}/api.jsonl" "${latest_dir}/api.jsonl"
ln -sfn "../runs/${run_id}/worker.jsonl" "${latest_dir}/worker.jsonl"

printf '%s\n' "$run_id"
