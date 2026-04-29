# Workstream Taxonomy

## Purpose
This file defines the top-level work taxonomy for workstreams in this repo.

Use it to choose a `work_type`, apply status vocabulary consistently, and keep classification tied to the primary deliverable rather than urgency or motivation.

## When To Use
- Starting a new workstream
- Reclassifying a workstream whose scope has become clearer
- Checking whether work is primarily a `feature`, `refactor`, `spike`, `defect`, or `operations-infrastructure`
- Checking whether the work belongs on the `WS` track or the `HR` track
- Deciding which documentation shape a work item needs

## Workstream Types
Use a small set of primary work types based on the main deliverable of the work item.

### `feature` (Evolution)
Work that changes the system's external behavior, contracts, or capabilities to deliver new value.

- Documentation focus: requirements, API or design docs, user or system flows, compatibility notes, rollout plans
- System impact: expands or changes the externally relevant system surface

### `refactor` (Structural Integrity)
Work that changes internal structure, module boundaries, or implementation without intending to change observable external behavior.

- Documentation focus: design rationale, ADRs, invariants, before/after notes, migration plans
- System impact: improves maintainability, extensibility, testability, or internal performance while preserving intended behavior

### `spike` (Discovery)
Time-boxed exploratory work intended to reduce uncertainty, compare options, or establish feasibility. The primary output is knowledge, not production code.

- Documentation focus: investigation notes, proof-of-concept findings, benchmark results, alternatives considered, recommendation
- System impact: informs later implementation work and preserves why certain paths were rejected

### `operations-infrastructure` (Service Foundation)
Work on the runtime environment, deployment machinery, observability, scaling configuration, delivery pipelines, and service-operability foundations.

- Documentation focus: runbooks, CI/CD designs, environment notes, alerting thresholds, SLO/SLI definitions, capacity plans, rollback procedures
- System impact: ensures the service can be built, deployed, observed, operated, and recovered reliably

### `defect` (Behavior Restoration)
Work that restores intended behavior after a bug, regression, or faulty implementation causes the system to behave incorrectly.

- Documentation focus: repro notes, expected-versus-actual behavior, root-cause analysis, fix notes, regression-test additions
- System impact: closes correctness or reliability gaps by bringing the system back to intended behavior

## Decision Rule
Classify each work item by answering:

**What is the primary deliverable?**

- New capability or intended behavior change: `feature`
- Restore incorrect behavior: `defect`
- Internal redesign with stable intended behavior: `refactor`
- Learn, de-risk, or decide before committing: `spike`
- Improve runtime, deployment, observability, or service-operability foundations: `operations-infrastructure`

If a work item touches multiple concerns, assign the primary type and record the rest as tags or local metadata.

## Classification Guidance
Use the type to describe the main engineering shape of the work, not its urgency, motivation, or business framing.

Do not create separate top-level types for:

- `hotfix`: urgency or delivery posture, not work type
- `tech-debt`: motivation, not work type
- `migration`: usually a `feature`, `refactor`, or `operations-infrastructure`
- `optimization`: usually a `refactor` or `feature`
- `docs`: usually attached to another work item unless documentation is itself the primary deliverable
- `research`: usually a `spike`
- `cleanup`: usually a `refactor` or `operations-infrastructure`

Recommended secondary tags:

- `security`
- `incident`
- `reliability`
- `remediation`
- `migration`
- `dependency`
- `docs`

This keeps the top-level taxonomy compact while preserving nuance.

## Boundary Notes
A few boundaries are easy to blur. Use these rules.

### Defect vs Operations / Infrastructure
- If the main output is restoring wrong application behavior, use `defect`.
- If the main output is improving deployability, operability, monitoring, runtime configuration, or resilience mechanisms, use `operations-infrastructure`.

Examples:

- Fix incorrect retry backoff logic in service code: `defect`
- Add alerting, dashboards, and rollback automation after the incident: `operations-infrastructure`

### Refactor vs Feature
- If intended external behavior changes, use `feature`.
- If intended external behavior stays stable and the main value is structural improvement, use `refactor`.

### Spike vs Everything Else
- If the main deliverable is a decision, feasibility result, comparison, or recommendation, use `spike`.
- If the main deliverable is merged production behavior or infrastructure change, do not use `spike`.

### Docs-Heavy Work
- If the work primarily changes durable or internal documentation structure while preserving intended product behavior, use `refactor`.
- If the work primarily investigates documentation shape, process, or authority boundaries before commitment, use `spike`.
- If documentation accompanies another main deliverable, classify by that main deliverable instead of using a separate docs type.

## Suggested Statuses
- `backlog`: defined but not yet active
- `active`: in progress
- `blocked`: waiting on an external dependency or decision
- `done`: implementation and expected evidence complete
- `archived`: retained for history but no longer active or current

## Track Convention
Use the path and ID prefix to show which system the work changes.

- `docs/workstreams/WS-...`: doc_forge service and runtime-related work
- `docs/harness-maintain/HR-...`: agentic-harness maintenance work for the documentation system that guides coding agents

Use `work_type` for the kind of work and `WS` versus `HR` for the affected system.

## Repo Convention
Keep classification in metadata and use the path and ID prefix for track selection.

Current repo convention:

```text
docs/workstreams/
  WS-001-auth-cache/
  WS-002-ci-hardening/
  WS-003-parser-investigation/
```

Inside each workstream:

```yaml
artifact_kind: workstream
id: WS-001
title: Auth cache redesign
work_type: feature
status: active
tags: [security, reliability]
```

This avoids path churn when work evolves from `spike` to `feature` or from `defect` to a broader follow-on, while keeping the doc_forge/runtime track separate from the agentic-harness track.

## Examples
- Investigate whether to move auth cache to Redis: `spike`
- Implement Redis-backed auth cache after the decision: `feature`
- Restructure the auth module for testability with no intended behavior change: `refactor`
- Fix a stale token validation bug: `defect`
- Upgrade Python, `uv`, the CI image, and the lint pipeline: `operations-infrastructure`
- Add deployment health checks and paging thresholds: `operations-infrastructure`
- Fix retry logic causing auth timeouts in production: `defect`
- Write the operator runbook for a failover procedure: `operations-infrastructure`
- Evaluate three approaches for PDF parsing: `spike`
- Split a monolithic service component into clearer internal boundaries with stable behavior: `refactor`

## Rule Of Thumb
When uncertain:

- choose `spike` if you are still deciding
- choose `feature` if users or external integrations will observe a new or changed behavior
- choose `refactor` if only internals should change
- choose `defect` if something is wrong and must be restored
- choose `operations-infrastructure` if the service foundation is what is being changed

These categories are intentionally small because they map to meaningfully different documentation shapes and review expectations.
