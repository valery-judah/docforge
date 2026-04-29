#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
repo_root="$(CDPATH='' cd -- "${script_dir}/../../.." && pwd)"
workstreams_dir="${repo_root}/docs/workstreams"

if [ ! -d "${workstreams_dir}" ]; then
  exit 0
fi

find "${workstreams_dir}" -mindepth 1 -maxdepth 1 -type d -print | sort
