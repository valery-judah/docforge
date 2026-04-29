#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "container-log-wrapper.sh requires a command to execute" >&2
  exit 64
fi

if [ -z "${DOC_FORGE_JSON_LOG_PATH:-}" ]; then
  exec "$@"
fi

log_dir="$(dirname "$DOC_FORGE_JSON_LOG_PATH")"
mkdir -p "$log_dir"

set +e
"$@" 2>&1 | tee >(
  python -c '
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
with path.open("a", encoding="utf-8") as handle:
    for line in sys.stdin:
        candidate = line.rstrip("\n")
        try:
            json.loads(candidate)
        except Exception:
            continue
        handle.write(candidate + "\n")
' "$DOC_FORGE_JSON_LOG_PATH"
)
command_status="${PIPESTATUS[0]}"
tee_status="${PIPESTATUS[1]:-0}"
set -e

if [ "$tee_status" -ne 0 ]; then
  exit "$tee_status"
fi
exit "$command_status"
