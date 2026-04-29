# Context Assembly Service API and Configuration Reference

- Document ID: CAS-REF-002
- Status: Active
- Owner: Retrieval Platform Team
- Last updated: 2026-02-27
- Intended audience: platform engineers, evaluation engineers, service operators
- Applies to: internal Context Assembly Service deployments used for document-grounded QA
- Does not apply to: OCR-first ingestion pipelines, image-only retrieval systems, public web search workflows

## 1. Overview

The Context Assembly Service (CAS) is an internal service that prepares evidence context for document-grounded answer generation. It accepts a normalized query request, retrieves candidate passages from an indexed corpus, applies ranking and filtering rules, assembles a bounded answer context, and returns both context payloads and provenance metadata.

This reference covers:

- request and response fields for the primary API;
- service-level configuration values;
- provenance and citation behavior;
- fallback behavior when source structure is incomplete;
- operational limits relevant to interactive workloads.

This reference does not define model prompting, user-interface rendering, or offline evaluation scoring policy except where those behaviors affect service outputs directly.

## 2. Service Purpose

The service exists to solve a narrow problem: produce a compact, inspectable evidence set for a user question over an internal corpus.

The service is not responsible for final answer wording. It is responsible for:

- retrieving relevant candidate passages;
- preserving source identity and local locators when available;
- filtering or downscoping context when evidence quality is weak;
- returning enough metadata for downstream answer generation and review.

The service is expected to prefer trustworthy traceability over maximal evidence volume. When there is tension between large context windows and clean provenance, the service defaults to provenance-preserving behavior.

## 3. Base Endpoint and Versioning

### 3.1 Base path

The current base path for the primary API is:

`/v1/context/assemble`

### 3.2 Versioning policy

The API uses path-based major versioning.

Minor backward-compatible changes may include:

- new optional response fields;
- new enum values where clients are expected to ignore unknown values safely;
- new optional request hints.

Backward-incompatible changes require a new major version path.

### 3.3 Supported content type

Requests must use:

`application/json`

Responses are returned as JSON.

## 4. Primary Operation

### 4.1 Summary

The primary operation accepts a question and retrieval configuration, then returns an evidence package for downstream answer generation.

### 4.2 Request method

`POST /v1/context/assemble`

### 4.3 Required request fields

The following request fields are required:

- `request_id`
- `query_text`
- `corpus_id`

#### 4.3.1 `request_id`

Type: string

Requirements:

- must be unique within the caller's request stream for tracing purposes;
- maximum length: 128 characters.

The service does not require a UUID format, but callers should avoid reusing IDs across retries when they need distinct tracing.

#### 4.3.2 `query_text`

Type: string

Requirements:

- must not be empty after trimming whitespace;
- maximum length: 8,000 characters.

Very long queries are accepted for compatibility, but retrieval quality is tuned for short to medium natural-language questions rather than full document submissions.

#### 4.3.3 `corpus_id`

Type: string

This identifies the indexed corpus against which retrieval is performed.

The service returns `404` if the corpus is unknown and `403` if the caller is not permitted to access the named corpus.

### 4.4 Optional request fields

Optional fields include:

- `query_type`
- `top_k_candidates`
- `top_k_context`
- `rerank_enabled`
- `provenance_mode`
- `allow_parent_fallback`
- `max_context_tokens`
- `filters`
- `debug`
- `timeout_ms`

#### 4.4.1 `query_type`

Type: string enum

Supported values:

- `lookup`
- `navigation`
- `localized_explanation`
- `synthesis`
- `unknown`

Default: `unknown`

This field is advisory. It does not hard-route retrieval logic, but it influences ranking weights and context diversity thresholds.

#### 4.4.2 `top_k_candidates`

Type: integer

Default: `30`

Allowed range: `5` to `100`

This sets the size of the candidate pool before reranking. Larger values may improve recall but can increase median latency and may introduce more low-quality evidence into downstream assembly.

#### 4.4.3 `top_k_context`

Type: integer

Default: `6`

Allowed range: `1` to `20`

This sets the maximum number of passages returned in the final assembled context. The service may return fewer than the requested number if evidence quality filters remove candidates.

#### 4.4.4 `rerank_enabled`

Type: boolean

Default: `true`

When `true`, the service applies the configured reranker to the first-stage candidate set before context selection.

#### 4.4.5 `provenance_mode`

Type: string enum

Supported values:

- `document_only`
- `document_and_local`
- `strict_local`

Default: `document_and_local`

Behavior:

- `document_only` returns document identity without requiring a local locator;
- `document_and_local` returns document identity and the most reliable local locator available;
- `strict_local` suppresses candidates that cannot provide a sufficiently reliable local locator.

`strict_local` is intended for provenance-sensitive workflows and may reduce recall on weakly structured corpora.

#### 4.4.6 `allow_parent_fallback`

Type: boolean

Default: `true`

When enabled, the service may return a stable parent section when subsection recovery is unreliable. This setting applies primarily to Markdown heading paths and PDF section metadata.

If `allow_parent_fallback` is `false`, the service will not degrade a local locator to a broader parent path. In weakly structured corpora, disabling parent fallback can reduce the number of returned passages materially.

#### 4.4.7 `max_context_tokens`

Type: integer

Default: `2200`

Allowed range: `256` to `8192`

This sets a hard ceiling for the total token budget of the assembled context payload returned by CAS.

#### 4.4.8 `filters`

Type: object

The `filters` object may contain:

- `doc_ids`
- `doc_types`
- `section_prefixes`
- `tags`
- `updated_after`
- `updated_before`

All filters are optional.

##### `doc_ids`

Type: array of strings

If present, retrieval is restricted to the listed documents.

##### `doc_types`

Type: array of strings

Supported values include:

- `markdown`
- `pdf_text`
- `policy`
- `runbook`
- `api_reference`
- `notes`

The exact values available depend on corpus indexing configuration.

##### `section_prefixes`

Type: array of strings

For structured corpora, this restricts retrieval to passages whose heading path begins with one of the given prefixes.

##### `tags`

Type: array of strings

Tag filtering behavior is corpus-specific.

##### `updated_after`

Type: string, RFC 3339 timestamp

##### `updated_before`

Type: string, RFC 3339 timestamp

Date filters are best-effort and only apply when document metadata includes normalized update timestamps.

#### 4.4.9 `debug`

Type: boolean

Default: `false`

When `true`, the response may include internal scoring and filtering metadata. Debug responses are larger and should not be exposed directly to end users.

#### 4.4.10 `timeout_ms`

Type: integer

Default: inherited from server setting

If provided, the request timeout may be lowered from the server default but may not exceed the server maximum.

The default server-side request timeout is **4000 ms**.

## 5. Response Schema

### 5.1 Top-level response fields

The response may include:

- `request_id`
- `corpus_id`
- `status`
- `assembled_context`
- `returned_passages`
- `provenance_summary`
- `warnings`
- `timing_ms`
- `debug_info`

### 5.2 `status`

Type: string enum

Possible values:

- `ok`
- `partial`
- `no_context`
- `error`

Interpretation:

- `ok` means usable context was assembled;
- `partial` means some retrieval or provenance constraints reduced the output;
- `no_context` means no acceptable evidence package was returned;
- `error` means the request failed.

### 5.3 `assembled_context`

Type: string

This field contains the concatenated context payload intended for downstream answer generation.

Passages are concatenated in service-selected order, with local provenance headers inserted between passage blocks unless disabled by deployment configuration.

### 5.4 `returned_passages`

Type: array of objects

Each returned passage may contain:

- `passage_id`
- `doc_id`
- `doc_title`
- `content`
- `rank`
- `score`
- `provenance`
- `structure_quality`
- `selection_reason`

#### 5.4.1 `provenance`

Type: object

Possible provenance fields include:

- `doc_title`
- `doc_path`
- `page`
- `page_start`
- `page_end`
- `section_path`
- `section_start`
- `section_end`
- `locator_confidence`

The service does not guarantee that all provenance fields are present for every passage.

#### 5.4.2 `locator_confidence`

Type: string enum

Supported values:

- `high`
- `medium`
- `low`

Interpretation:

- `high` means the local locator is directly supported by recovered source structure;
- `medium` means the local locator is believed stable but derived through normalization;
- `low` means only broad or fallback provenance is reliable.

### 5.5 `provenance_summary`

Type: object

This field summarizes provenance characteristics across the returned set.

Possible fields include:

- `mode_used`
- `parent_fallback_used`
- `strict_local_dropped_count`
- `documents_returned`
- `all_locators_stable`

### 5.6 `warnings`

Type: array of strings

Warnings are human-readable notes describing notable conditions, for example:

- local section recovery incomplete;
- parent section fallback applied;
- candidate set reduced by strict provenance constraints.

Warnings are advisory and not a substitute for structured status handling.

## 6. Provenance Behavior

### 6.1 General rule

CAS returns the most specific stable provenance it can justify from the indexed source structure.

The service must not synthesize subsection labels or page numbers that are not supported by recovered document metadata.

### 6.2 Markdown provenance behavior

For Markdown sources, the preferred local locator is `section_path`.

When subsection structure is reliable, the service returns the full heading path.

When subsection structure is unstable but the parent section is stable, and `allow_parent_fallback` is enabled, CAS returns the nearest stable parent section rather than a guessed subsection.

### 6.3 PDF-derived provenance behavior

For PDF-derived text, page numbers are preferred as the primary local locator.

If section metadata survives extraction and mapping reliably, section information may be returned in addition to the page.

### 6.4 Repeated heading names

If a Markdown document contains repeated local headings such as `Notes`, `Examples`, or `Caveats`, CAS may downgrade locator confidence or fall back to a broader parent path if the repeated headings cannot be distinguished safely.

### 6.5 Strict local mode

When `provenance_mode` is `strict_local`, candidates without sufficient local provenance are filtered out during final selection.

This mode is useful for citation-sensitive evaluation but can increase `no_context` outcomes on weakly structured corpora.

## 7. Selection and Assembly Rules

### 7.1 Candidate retrieval

The first-stage retriever returns up to `top_k_candidates` passages from the selected corpus.

The default production configuration uses **30 candidates** before reranking.

### 7.2 Reranking

If `rerank_enabled` is true, candidates are reranked before assembly.

Reranking is bypassed only when:

- the request explicitly disables it; or
- the deployment has reranking disabled by policy.

### 7.3 Final context size

The service returns at most `top_k_context` passages, subject to the `max_context_tokens` ceiling.

The default final passage count is **6**.

### 7.4 Diversity rule for synthesis queries

When `query_type` is `synthesis`, the service applies a diversity heuristic to avoid returning multiple near-duplicate passages from the same local region.

The current diversity rule prefers no more than **2 passages from the same document section path** unless the evidence pool is otherwise too weak.

### 7.5 Narrowness rule for lookup queries

When `query_type` is `lookup`, CAS favors highly localized passages over broader thematic passages, even when the broader passages have similar semantic scores.

This rule exists to improve answer inspectability and reduce irrelevant neighbor contamination.

## 8. Error Handling

### 8.1 Status codes

Common HTTP status codes include:

- `200` for successful responses, including `partial` and `no_context` statuses;
- `400` for malformed requests;
- `403` for unauthorized corpus access;
- `404` for unknown corpus IDs;
- `408` for timeout conditions;
- `429` for rate limit violations;
- `500` for internal server errors;
- `503` for temporary service unavailability.

### 8.2 Malformed request behavior

Requests are rejected with `400` if they contain:

- missing required fields;
- invalid enum values;
- invalid filter shapes;
- numeric fields outside allowed bounds.

### 8.3 No-context behavior

If no acceptable evidence package is found, the service returns HTTP `200` with:

- `status = "no_context"`
- an empty `returned_passages` array
- one or more warnings explaining the main reason when available

This is intentional. Absence of usable context is not treated as a transport failure.

## 9. Operational Limits

### 9.1 Default request timeout

The server-side default request timeout is **4000 ms**.

### 9.2 Interactive latency target

The service is tuned for an interactive target of **under 2500 ms median end-to-end latency** under normal load.

This target includes retrieval, reranking, and context assembly, but excludes downstream answer generation.

### 9.3 Maximum payload sizes

The maximum accepted request body size is **256 KB**.

The maximum response size is deployment-dependent, but the service is tuned so that standard successful responses remain well below **512 KB**.

### 9.4 Rate limits

Default per-caller rate limits are:

- **60 requests per minute**
- burst allowance up to **10 concurrent in-flight requests**

These defaults may be overridden by deployment policy.

## 10. Service Configuration Reference

### 10.1 `assembly.default_top_k_candidates`

Type: integer

Default: `30`

Description: default first-stage candidate pool size.

### 10.2 `assembly.default_top_k_context`

Type: integer

Default: `6`

Description: default number of passages returned in final context.

### 10.3 `assembly.max_context_tokens`

Type: integer

Default: `2200`

Description: default token ceiling for concatenated context payloads.

### 10.4 `assembly.parent_fallback_enabled`

Type: boolean

Default: `true`

Description: allows degradation from unstable subsection-level provenance to nearest stable parent locator.

### 10.5 `assembly.strict_local_min_confidence`

Type: string enum

Default: `medium`

Allowed values:

- `high`
- `medium`

Description: minimum `locator_confidence` required to keep a passage when `strict_local` provenance mode is active.

### 10.6 `retrieval.rerank_enabled`

Type: boolean

Default: `true`

Description: enables reranking after first-stage retrieval.

### 10.7 `retrieval.default_query_type`

Type: string enum

Default: `unknown`

Description: query type used when the caller omits `query_type`.

### 10.8 `retrieval.lookup_locality_boost`

Type: float

Default: `1.25`

Allowed range: `0.5` to `3.0`

Description: scoring multiplier favoring localized passages for lookup queries.

### 10.9 `retrieval.section_diversity_limit`

Type: integer

Default: `2`

Description: maximum passages selected from a single section path in synthesis mode unless overridden by evidence scarcity logic.

### 10.10 `timeouts.request_timeout_ms`

Type: integer

Default: `4000`

Description: maximum permitted request duration before timeout handling.

## 11. Environment Variable Overrides

The following environment variables override service configuration at startup:

- `CAS_DEFAULT_TOP_K_CANDIDATES`
- `CAS_DEFAULT_TOP_K_CONTEXT`
- `CAS_MAX_CONTEXT_TOKENS`
- `CAS_PARENT_FALLBACK_ENABLED`
- `CAS_RERANK_ENABLED`
- `CAS_REQUEST_TIMEOUT_MS`

Environment overrides are parsed once at startup and do not hot-reload automatically.

If both file-based configuration and environment variables are present, environment variables take precedence.

## 12. Examples

### 12.1 Minimal request

```json
{
  "request_id": "req-1001",
  "query_text": "What provenance format is preferred for Markdown documents?",
  "corpus_id": "policy-corpus"
}