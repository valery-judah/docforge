#!/usr/bin/env bash
set -euo pipefail

readonly script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"

checks=(
  "${script_dir}/validate-frontmatter.sh"
)

for check in "${checks[@]}"; do
  "${check}"
done

printf 'Docs lint checks passed\n'
