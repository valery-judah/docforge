# Docs Harness

## Purpose
`docs/harness/` holds reusable documentation scaffolding for this repository: taxonomy, templates, conventions, playbooks, and helper scripts for humans and agents.
It supports the canonical docs layout rooted at `docs/evergreen/`, `docs/workstreams/`, `docs/adrs/`, and `docs/harness/`.

## When To Use
- Starting a new workstream
- Creating durable or time-scoped docs in a consistent shape
- Checking repo documentation conventions before adding new material

## Layout
- `AGENTS.md`: harness-local usage notes for humans and agents
- `taxonomy/`: naming and lifecycle vocabulary for workstreams
- `templates/`: starter files for workstreams, evidence, handoff, decisions, and ADRs
- `conventions/`: lightweight rules for ADR placement, commit message conventions, and related doc conventions
- `playbooks/`: short procedures by work type
- `scripts/`: simple shell helpers for initializing and listing docs areas

## Placement Rules
- Durable system truth belongs in `docs/evergreen/`.
- Time-scoped execution history belongs in `docs/workstreams/`.
- Durable architectural decisions belong in `docs/adrs/`.
- RFC-like proposal material belongs inside the relevant workstream, not in a global `docs/rfcs/` directory.

## Starter Workflow
1. Decide the work is non-trivial enough to deserve a workstream.
2. Use `docs/harness/taxonomy/workstream-taxonomy.md` to choose the right `work_type` and status vocabulary.
3. Create or reuse a workstream folder under `docs/workstreams/`, typically with `make workstream-new type=<work_type> slug=<slug>`.
4. Fill the placeholders progressively during framing and execution.
5. Add decisions, evidence, handoff, and notes artifacts only when they improve continuity or validation.

## Working Rule
- Treat `WS-XXX-workstream.md` as the canonical local execution capsule.
- Treat `WS-XXX-framing.md` as the framing-stage scaffold for clarifying scope and decisions before execution.
- Treat the initial scaffold as placeholder-first; full framing can happen later.
- Elevate cross-cutting durable decisions to ADRs when needed.
