#!/usr/bin/env bash
set -euo pipefail

readonly allowed_work_types='feature refactor spike operations-infrastructure defect'

usage() {
  printf 'Usage: %s <work_type> <slug>\n' "$(basename "$0")" >&2
  printf 'Allowed work_type values: %s\n' "${allowed_work_types}" >&2
}

if [ "$#" -ne 2 ]; then
  usage
  exit 1
fi

work_type="$1"
slug="$2"

case " ${allowed_work_types} " in
  *" ${work_type} "*) ;;
  *)
    printf 'Expected work_type to be one of: %s\n' "${allowed_work_types}" >&2
    exit 1
    ;;
esac

case "${slug}" in
  *[!a-z0-9-]*|'')
    printf 'Expected lowercase slug with letters, numbers, or hyphens\n' >&2
    exit 1
    ;;
esac

script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
repo_root="$(CDPATH='' cd -- "${script_dir}/../../.." && pwd)"
workstreams_dir="${repo_root}/docs/workstreams"
templates_dir="${script_dir}/../templates"
today="$(date +%F)"

mkdir -p "${workstreams_dir}"

last_id="$(
  find "${workstreams_dir}" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; |
    sed -nE 's/^WS-([0-9]+)-.*$/\1/p' |
    sort -n |
    tail -n 1
)"

if [ -n "${last_id}" ]; then
  next_num=$((10#${last_id} + 1))
else
  next_num=1
fi

ws_id="$(printf 'WS-%03d' "${next_num}")"
workstream_dir="${workstreams_dir}/${ws_id}-${slug}"

if [ -e "${workstream_dir}" ]; then
  printf 'Workstream already exists: %s\n' "${workstream_dir}" >&2
  exit 1
fi

title="$(
  printf '%s\n' "${slug}" |
    awk -F- '{
      OFS = " "
      for (i = 1; i <= NF; i++) {
        if (length($i) > 0) {
          $i = toupper(substr($i, 1, 1)) substr($i, 2)
        }
      }
      print $0
    }'
)"

mkdir -p "${workstream_dir}"

WS_ID="${ws_id}" TITLE="${title}" TODAY="${today}" WORK_TYPE="${work_type}" STATUS="active" \
  envsubst '${WS_ID}${TITLE}${TODAY}${WORK_TYPE}${STATUS}' \
  < "${templates_dir}/workstream.md" \
  > "${workstream_dir}/${ws_id}-workstream.md"

cp "${templates_dir}/framing.md" "${workstream_dir}/${ws_id}-framing.md"

printf 'Created %s\n' "${workstream_dir}"
