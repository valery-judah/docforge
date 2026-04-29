# ADR Directory Conventions

## Purpose
This file defines how ADR files should be named and when they should be created.

## When To Use
Consult it before adding a new ADR or deciding whether a decision should stay inside a workstream.

## Naming
Use `ADR-0001-short-slug.md`.

Examples:
- `ADR-0001-parser-contract-boundary.md`
- `ADR-0002-pdf-engine-selection.md`

## When To Create An ADR
Create an ADR when the decision is:
- durable
- cross-cutting
- likely to affect multiple workstreams or subsystems

## When To Keep It In A Workstream
Keep the decision only in the workstream when it is:
- still exploratory
- local to one effort
- likely to change before the implementation settles
