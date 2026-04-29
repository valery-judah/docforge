#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
repo_root="$(CDPATH='' cd -- "${script_dir}/../../.." && pwd)"

mkdir -p \
  "${repo_root}/docs/evergreen" \
  "${repo_root}/docs/workstreams" \
  "${repo_root}/docs/adrs" \
  "${repo_root}/docs/harness/taxonomy" \
  "${repo_root}/docs/harness/templates" \
  "${repo_root}/docs/harness/conventions" \
  "${repo_root}/docs/harness/playbooks" \
  "${repo_root}/docs/harness/scripts"

touch "${repo_root}/docs/workstreams/.gitkeep"
touch "${repo_root}/docs/adrs/.gitkeep"

printf 'Initialized docs scaffold under %s\n' "${repo_root}/docs"
