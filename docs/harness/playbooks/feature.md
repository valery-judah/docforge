# Feature Playbook

## When To Use
Use for new user-visible capability or meaningful product behavior expansion.

## Start Here
- Choose `feature` from `docs/harness/taxonomy/workstream-taxonomy.md`, then create the workstream with `make workstream-new type=feature slug=<slug>`.
- Treat `WS-XXX-workstream.md` as the canonical entrypoint for the workstream.
- Use `WS-XXX-framing.md` to complete the framing-stage problem, scope, and exit-criteria notes before execution.
- Add `decisions.md`, `evidence.md`, `handoff.md`, or `notes.md` only when they improve continuity, traceability, or validation.

## Phase 0 Minimum Artifact
- `WS-XXX-workstream.md` with the canonical section structure from `docs/harness/templates/workstream.md`
- A single concrete `Next step`
- Placeholder sections are acceptable until later framing work fills them in

## Framing Later
After creation, use the workstream card to progressively add:
- objective and scope details
- context notes
- boundaries and non-goals
- useful commands
- validation notes

## Minimum Evidence Expected
- What changed
- Validation performed
- Any compatibility or rollout notes

## Typical Exit Criteria
- Scope is implemented or intentionally narrowed
- Evidence shows the feature was validated
- Evergreen or ADR follow-up is captured when current system truth changed
- Remaining follow-up is captured in handoff or a new workstream
