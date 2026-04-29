#!/usr/bin/env bash
set -euo pipefail

readonly script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
readonly repo_root="$(CDPATH='' cd -- "${script_dir}/../../.." && pwd)"
readonly docs_dir="${repo_root}/docs"
readonly workstreams_dir="${docs_dir}/workstreams"

required_workstream_keys=(
  artifact_kind
  id
  title
  work_type
  status
  owner
  created
  updated
)

status=0

report_error() {
  printf '%s\n' "$1" >&2
  status=1
}

markdown_files() {
  find "${docs_dir}" -type f -name '*.md' | sort
}

has_frontmatter() {
  local file="$1"
  [ "$(sed -n '1p' "${file}")" = "---" ]
}

frontmatter_closing_line() {
  local file="$1"
  awk 'NR > 1 && $0 == "---" { print NR; exit }' "${file}"
}

frontmatter_block() {
  local file="$1"
  local closing_line="$2"
  sed -n "2,$((closing_line - 1))p" "${file}"
}

has_frontmatter_key() {
  local frontmatter="$1"
  local key="$2"
  printf '%s\n' "${frontmatter}" | grep -Eq "^${key}:"
}

frontmatter_value() {
  local frontmatter="$1"
  local key="$2"
  printf '%s\n' "${frontmatter}" | sed -nE "s/^${key}:[[:space:]]*(.*)$/\\1/p" | head -n 1
}

is_workstream_file() {
  local file="$1"
  case "${file}" in
    "${workstreams_dir}"/*/workstream.md) return 0 ;;
    *) return 1 ;;
  esac
}

validate_generic_frontmatter() {
  local file="$1"
  local closing_line="$2"

  if [ -z "${closing_line}" ]; then
    report_error "Malformed frontmatter: missing closing delimiter in ${file}"
    return 1
  fi

  if [ "${closing_line}" -eq 2 ]; then
    report_error "Malformed frontmatter: empty frontmatter block in ${file}"
    return 1
  fi

  return 0
}

validate_workstream_frontmatter() {
  local file="$1"
  local frontmatter="$2"
  local artifact_kind
  local workstream_id
  local work_type
  local work_status
  local created
  local updated
  local key

  for key in "${required_workstream_keys[@]}"; do
    if ! has_frontmatter_key "${frontmatter}" "${key}"; then
      report_error "Missing required frontmatter key ${key} in ${file}"
    fi
  done

  artifact_kind="$(frontmatter_value "${frontmatter}" "artifact_kind")"
  if [ "${artifact_kind}" != "workstream" ]; then
    report_error "Invalid artifact_kind in ${file}: expected workstream"
  fi

  workstream_id="$(frontmatter_value "${frontmatter}" "id")"
  if ! printf '%s\n' "${workstream_id}" | grep -Eq '^WS-[0-9][0-9][0-9]+$'; then
    report_error "Invalid id in ${file}: expected WS-###"
  fi

  work_type="$(frontmatter_value "${frontmatter}" "work_type")"
  case "${work_type}" in
    feature|defect|refactor|spike|operations-infrastructure) ;;
    *)
      report_error "Invalid work_type in ${file}: ${work_type}"
      ;;
  esac

  work_status="$(frontmatter_value "${frontmatter}" "status")"
  case "${work_status}" in
    backlog|active|blocked|done|archived) ;;
    *)
      report_error "Invalid status in ${file}: ${work_status}"
      ;;
  esac

  created="$(frontmatter_value "${frontmatter}" "created")"
  if [ -z "${created}" ]; then
    report_error "Invalid created in ${file}: expected non-empty value"
  fi

  updated="$(frontmatter_value "${frontmatter}" "updated")"
  if [ -z "${updated}" ]; then
    report_error "Invalid updated in ${file}: expected non-empty value"
  fi
}

while IFS= read -r file; do
  local_closing_line=""
  local_frontmatter=""

  if ! has_frontmatter "${file}"; then
    if is_workstream_file "${file}"; then
      report_error "Missing frontmatter block in ${file}"
    fi
    continue
  fi

  local_closing_line="$(frontmatter_closing_line "${file}")"
  if ! validate_generic_frontmatter "${file}" "${local_closing_line}"; then
    continue
  fi

  if is_workstream_file "${file}"; then
    local_frontmatter="$(frontmatter_block "${file}" "${local_closing_line}")"
    validate_workstream_frontmatter "${file}" "${local_frontmatter}"
  fi
done < <(markdown_files)

exit "${status}"
