# Observability Operations

## Purpose
Use this guide when you need to decide which local databases and stacks to
start, how to run query or eval scenarios, and where logs, query bundles, and
eval results will be collected.

This document is operational. It does not redefine architecture or evaluation
semantics.

## Systems And Stores
There are two separate local stacks with different roles.

### 1. Main runtime stack
- Compose file: `docker-compose.yml`
- Primary database: the runtime Postgres service `db`
- Default host port: `5432`
- Services:
  - `db`
  - `api`
  - `worker`
  - optional `ollama` profile
- Responsibility:
  - ingest documents
  - answer queries
  - run the lifecycle worker
  - emit repo-local JSON logs
  - expose review and query routes used by context collection

### 2. Central observability stack
- Compose file: `docker-compose.observability.yml`
- Metadata database: `telemetry-postgres`
- Default host port: `5433`
- Other services:
  - `loki`
  - `grafana`
  - `vector`
  - `evalops-loader`
- Responsibility:
  - index collected query bundles into Postgres
  - ship repo-local JSON logs into Loki
  - provide a central UI in Grafana

## When To Start Which Database
### Start only the main runtime database and stack when:
- you are ingesting documents manually
- you are running live local queries
- you are debugging the application itself before central analysis matters

Command:
```bash
make docker-up-build
```

### Start only the observability stack when:
- you already have data under `data/logs/` and `data/context/queries/`
- you want to inspect existing runs without producing new ones
- you want Grafana, Loki, and the observability Postgres available for analysis

Command:
```bash
make observability-up-build
```

### Start both stacks when:
- you want to produce new runtime data and inspect it centrally right away
- you are running eval-focused scenarios and want Postgres/Loki/Grafana ready
  while the runs happen
- you want loader and log shipping to pick up new artifacts as they appear

Recommended order:
1. `make docker-up-build`
2. `make observability-up-build`

This order is preferred because the main stack is the data producer. The
observability stack can also be started later, since it ingests filesystem
artifacts after the fact.

### For docker-backed e2e only
You do not need `docker-compose.yml`.

The e2e suite starts its own isolated runtime stack. If you want central
analysis while or after e2e runs, start only the observability stack yourself:
```bash
make observability-up-build
uv run poe test-e2e
```

## Storage Paths And What They Mean
### Raw service logs
- Compose runs:
  - `data/logs/compose/runs/<run_id>/api.jsonl`
  - `data/logs/compose/runs/<run_id>/worker.jsonl`
- Compose shortcuts:
  - `data/logs/compose/latest/api.jsonl`
  - `data/logs/compose/latest/worker.jsonl`
- E2E runs:
  - `data/logs/e2e/runs/<session_id>/<test_id>/api.jsonl`
  - `data/logs/e2e/runs/<session_id>/<test_id>/worker.jsonl`
- E2E shortcuts:
  - `data/logs/e2e/latest/`

These are the raw JSONL logs emitted by `api` and `worker`. They are the source
for Loki ingestion.

### Query-centric context bundles
- Root:
  - `data/context/queries/<query_id>/`
- Core files:
  - `manifest.json`
  - `summary.json`
  - `citations.json`
  - `trace.json`
  - `replay.json`
  - `query-response.json` when final artifacts are available
- Optional eval files:
  - `eval-result.json`
  - `execution-metadata.json`
- Filtered query log view:
  - `logs/query-events.jsonl`

These bundles are the source for observability Postgres indexing.

## Central Observability Data Flow
### Postgres
`telemetry-postgres` is the primary central persistence layer.

`evalops-loader` scans `data/context/queries/` and writes normalized metadata.
Key indexed entities:
- query runs
- bundle assets
- eval case results
- raw log source links

`vector` ingests JSONL service logs and writes parsed log rows into `service_log_events`.
Because the application uses strongly-typed structured logging, the `event` column corresponds to a stable taxonomy (e.g., `query.run.completed`), and the `payload` JSONB column contains predictable, strictly-typed domain properties (e.g., `error_code`, `duration_ms`, `stage_name`).

### Loki
`vector` tails `data/logs/**/*.jsonl`, parses the JSON, attaches labels, and
ships the events into Loki for stream-oriented exploration.

Important standard labels:
- `service`
- `environment`
- `source_family`
- `source_kind`

Important structured metadata (queryable but not indexed as high-cardinality labels):
- `event` (maps to the internal `LogEvent` taxonomy)
- `query_id`
- `workspace_id`
- `run_id`
- `test_id`
- `case_id`

### Grafana
Grafana is the operator UI over both stores:
- Postgres for query/eval metadata lookup
- Loki for raw service log exploration

## Scenario Playbooks
### Scenario 1: Live local query, then central inspection
Use this when you want to run a manual query over a local workspace and then
inspect the run centrally.

1. Start the main stack:
```bash
make docker-up-build
```
2. Optionally start observability:
```bash
make observability-up-build
```
3. Run your upload and query flow through the HTTP API.
4. Collect the query bundle:
```bash
uv run poe collect-query-context <query_id>
```
5. If observability was started after the query, force a metadata scan:
```bash
uv run poe observability-loader-scan
```
6. Inspect:
```bash
uv run poe show-query-context <query_id>
```

Use this path when the starting point is a known `query_id`.

### Scenario 2: Docker-backed e2e runtime coverage
Use this when the goal is stack verification, query contract smoke, or
lifecycle coverage under the isolated e2e runtime.

1. Start central observability if you want immediate indexing/log shipping:
```bash
make observability-up-build
```
2. Run the suite:
```bash
uv run poe test-e2e
```

Results:
- raw logs land under `data/logs/e2e/runs/...`
- query bundles are written for query/eval flows that collect them
- the loader can index those bundles into observability Postgres
- Loki ingests the e2e `api` and `worker` JSON logs

This is good for broad runtime confidence, but it is not the most direct path
for answer-layer eval analysis.

### Scenario 3: Eval-focused smoke runs
Use this when you care primarily about authored eval behavior and want the
central stores to capture query ids, case ids, outcomes, and logs.

1. Start central observability:
```bash
make observability-up-build
```
2. Run the authored answer-layer e2e smoke:
```bash
uv run pytest e2e/test_eval_answer_layer_smoke.py -m e2e -o addopts="-q -s"
```
3. Optionally run query-runtime smoke alongside it:
```bash
uv run pytest e2e/test_query_runtime_smoke.py -m e2e -o addopts="-q -s"
```

What gets collected:
- per-scenario e2e `api` and `worker` logs under `data/logs/e2e/runs/...`
- query-centric bundles under `data/context/queries/<query_id>/`
- eval-specific assets in those bundles when the case is eval-backed:
  - `eval-result.json`
  - `execution-metadata.json`
- indexed rows in observability Postgres keyed by:
  - `query_id`
  - `case_id`
  - `run_id`
  - `test_id`
- corresponding Loki log streams labeled with the same identifiers when present

This is the preferred path when the main question is eval behavior.

### Scenario 4: Analyze existing data later
Use this when runs already happened and you only want analysis.

1. Start observability:
```bash
make observability-up-build
```
2. Run a one-shot rescan if needed:
```bash
uv run poe observability-loader-scan
```
3. Inspect `data/context/queries/` directly or use Grafana/Loki.

This works because the observability stack is downstream of on-disk artifacts.
It does not need to be running at the time the original query or eval ran.

## How Eval Data Is Collected
### For eval-backed e2e runs
The eval support path writes query-centric bundles automatically for executed
cases. Those bundles may include:
- `query-response.json`
- `eval-result.json`
- `execution-metadata.json`

The observability loader reads the manifest first, then enriches from the
optional eval files when they exist.

### For manual or compose queries
The bundle is not guaranteed to exist until you collect it explicitly:
```bash
uv run poe collect-query-context <query_id>
```

Once that bundle exists:
- Postgres can index it
- Loki already has the raw logs if the run was Docker-backed
- Grafana can be used to pivot between metadata and logs

## How To Find Things Later
### If you know the query id
1. Run:
```bash
uv run poe show-query-context <query_id>
```
2. Use the bundle root from that output.
3. In Grafana or Loki, query by `query_id`.

### If you know the case id
Use the observability Postgres datasource in Grafana to find the matching
`query_id`, `run_id`, `test_id`, and `evaluator_outcome`, then pivot into Loki
or the bundle root.

### If you know only the latest local run
Run:
```bash
make docker-log-index
```

That prints:
- the latest Compose log files
- the latest e2e log root
- the query bundle root

## Recommended Eval-First Workflow
When the main goal is eval analysis rather than general e2e confidence, use this
order:

1. `make observability-up-build`
2. `uv run pytest e2e/test_eval_answer_layer_smoke.py -m e2e -o addopts="-q -s"`
3. open Grafana on `http://127.0.0.1:3000`
4. inspect Postgres-backed metadata by `case_id` or `evaluator_outcome`
5. pivot to Loki by `query_id`
6. reopen the raw bundle under `data/context/queries/<query_id>/` when you need
   trace, replay, citations, or the full eval payload

This gives the cleanest answer to:
- what case ran
- what query it became
- what the system answered
- what the evaluator concluded
- what the `api` and `worker` logged

## Commands Summary
```bash
make docker-up-build
make observability-up-build
make observability-down
uv run poe observability-loader-scan
uv run poe test-e2e
uv run poe collect-query-context <query_id>
uv run poe show-query-context <query_id>
make docker-log-index
uv run pytest e2e/test_eval_answer_layer_smoke.py -m e2e -o addopts="-q -s"
uv run pytest e2e/test_query_runtime_smoke.py -m e2e -o addopts="-q -s"
```

## Troubleshooting
- If observability Postgres shows no rows, check that bundles exist under
  `data/context/queries/` and run `uv run poe observability-loader-scan`.
- If Loki shows no logs, check `data/logs/` first; Loki only ingests what is
  already archived there.
- If you ran a manual Compose query and cannot find it centrally, collect the
  bundle explicitly with `uv run poe collect-query-context`.
- If Grafana is up but empty, verify both datasources are healthy and that the
  central stack is reading the repo-local `data/` mounts.
- If `vector` shows duplicate-fingerprint warnings for some e2e files, treat
  that as archive noise unless you also see missing logs. The current known
  issue is noisy but not a blocker for ingestion.
