# Harness Agent Guide

## Purpose
This file gives short practical guidance for humans and agents using the docs harness.


## Starting A Workstream
If the task is to start a new non-trivial workstream, first use `docs/harness/taxonomy/workstream-taxonomy.md` to choose the right `work_type`.

Then run:

```bash
make workstream-new type=<work_type> slug=<slug>
```

Example:

```bash
make workstream-new type=feature slug=parser-contract-cleanup
```

The underlying script remains available for direct use when needed:

```bash
docs/harness/scripts/new-workstream.sh <work_type> <slug>
```

This creates:

```text
docs/workstreams/WS-###-<slug>/WS-###-workstream.md
docs/workstreams/WS-###-<slug>/WS-###-framing.md
```

## What The Generated `WS-###-workstream.md` Is
The generated `WS-###-workstream.md` is an initial workstream card, not a fully framed plan.

At creation time it is valid for the file to contain placeholders for:
- objective details
- relevant context
- boundaries
- commands
- validation notes

Those details can be filled later during framing and execution.

## What The Generated `WS-###-framing.md` Is
The generated `WS-###-framing.md` is the scaffold for the framing stage of the workstream.

Use it to capture problem definition, scope, constraints, key decisions, expected outputs, and exit criteria before execution.

## Working Rule
- Use root `AGENTS.md` for repo-level routing decisions before creating a workstream card.
- Use `docs/harness/taxonomy/workstream-taxonomy.md` when classifying the workstream and choosing a matching playbook.
- Treat the generated workstream card as the canonical lightweight execution artifact for the workstream.
- Treat the framing file as the place to shape the framing-stage understanding before execution starts.
- Fill the placeholders progressively as the work becomes clearer.
- Add `decisions.md`, `evidence.md`, `handoff.md`, or `notes.md` only when they help continuity or validation.

## Command Rule
- Use root `AGENTS.md` for repo-wide command conventions and validation defaults.
- If the workstream card later includes useful commands, treat them as local notes, not as a separate command authority.
