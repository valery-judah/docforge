# Commit Message Conventions

## Purpose
This file defines the preferred Conventional Commits style for this
repository.

## When To Use
Consult it before creating a commit, recommending a commit type, or reviewing
whether a commit message matches repo conventions.

## Canonical Format
Use the Conventional Commits structure:

```text
<type>[optional scope][optional !]: <description>

[optional body]

[optional footer(s)]
```

- `type` is required.
- `scope` is optional and should be a noun naming the affected area.
- `!` is optional and marks a breaking change in the type/scope prefix.
- `description` is a short summary of the change.
- `body` and `footer(s)` are optional and may be added when more context is
  useful.

Prefer lowercase `type` and lowercase `scope` for consistency.

## Approved Types
The core Conventional Commits specification gives special SemVer meaning to
`feat` and `fix`.

This repository also explicitly allows the common Angular-style and
`config-conventional` types:

- `build`: changes that affect the build system or external dependencies
- `chore`: repository maintenance, tooling, cleanup, dependency, or DevEx work
- `ci`: changes to CI configuration or automation scripts
- `docs`: documentation-only changes
- `feat`: a new feature or externally relevant capability
- `fix`: a bug fix or behavior restoration
- `perf`: a code change that improves performance
- `refactor`: internal restructuring without intended behavior change
- `revert`: reverts a previous commit
- `style`: formatting or presentation changes that do not affect behavior
- `test`: test-only additions or test maintenance

## Scope Guidance
Scopes are optional.

Use a scope only when it adds concrete context, for example:

- `chore(devex): use and clean a repo-local uv cache`
- `refactor(api): extract router factories`
- `feat(eval): collect query context bundles`
- `ci(github): run verification on pull requests`

Prefer stable nouns such as `api`, `worker`, `eval`, `devex`, `docs`,
`observability`, or `github`.

Do not add a scope just to satisfy a rule.

## Breaking Changes
Breaking changes may be marked in either standard Conventional Commits form:

- `type(scope)!: description`
- a `BREAKING CHANGE:` footer

Use those markers when a commit introduces an incompatible API or contract
change, even when the type is not `feat` or `fix`.

Example:

```text
feat(api)!: rename lifecycle status field

BREAKING CHANGE: clients must read `state` instead of `status`
```

## Choosing The Type
- Use `feat` when users or external integrations would observe a new capability
  or intended behavior change.
- Use `fix` when the main point is restoring behavior that was wrong.
- Use `refactor` when the main point is structural improvement while intended
  behavior stays the same.
- Use `docs` when documentation is the primary deliverable.
- Use `chore` for maintenance and workflow changes such as local tooling,
  cleanup tasks, or repository housekeeping.
- Use `build` for changes centered on dependency management, packaging, or the
  build system itself.
- Use `ci` for CI pipeline or automation wiring changes.
- Use `perf` when the change is primarily about performance improvement.
- Use `revert` when the commit’s purpose is to revert an earlier change.
- Use `style` for formatting-only or presentation-only changes that do not
  change meaning or behavior.
- Use `test` when the change is primarily new or updated tests.

Only `feat` and `fix` have SemVer meaning in the core specification unless a
commit also declares a breaking change.

## Boundary With Workstream Types
Commit types and workstream types are related but not identical.

Workstream taxonomy in `docs/harness/taxonomy/workstream-taxonomy.md`
classifies the primary shape of an effort, such as `feature`, `defect`,
`refactor`, or `operations-infrastructure`.

The rough mapping is:

- `feature` work often produces `feat` commits
- `defect` work often produces `fix` commits
- `refactor` work often produces `refactor` commits
- `operations-infrastructure` work often produces `chore`, `build`, or `ci`
  commits

Workstream types classify efforts. Commit types classify individual git history
entries. An `operations-infrastructure` workstream can still contain
`chore(...)`, `build(...)`, and `ci(...)` commits.

## Legacy History Note
Older history may contain unprefixed titles or non-canonical variants such as
`dox:`.

Treat those as legacy history, not as examples to copy forward. Prefer the
approved types in this file for new commits.

## Examples
- `feat: add swagger`
- `fix: project compile`
- `refactor: introduce settings management`
- `docs: improve AGENTS and README`
- `chore(devex): use and clean a repo-local uv cache`
- `build: update uv and dependency lock workflow`
- `ci(github): run verification on pull requests`
- `perf(retrieval): reduce chunk scoring overhead`
- `revert: revert "feat: add swagger"`
- `style: normalize markdown list indentation`
- `test: add regression coverage for repo clean`
