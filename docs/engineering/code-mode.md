# Code Mode

## Purpose

This document defines how implementation agents must behave when making changes in this repository.

It is a repository-level execution contract.
Its purpose is to produce changes that are:

* correct
* small and reviewable
* consistent with repository conventions
* verified before being reported as complete
* explicit about uncertainty and risk

This document governs implementation behavior across languages and subsystems.
Language- and framework-specific policies are defined in the relevant engineering documents.

---

## Priority Order

When principles conflict, use this order:

1. Correctness
2. Complete the scoped task
3. Minimal blast radius
4. Follow repository conventions
5. Verifiability
6. Maintainability
7. Speed

Do not trade correctness for elegance or speed.
Do not widen scope for cleanliness unless the narrower change is insufficient for correctness or safety.

---

## Core Operating Principles

### 1. The repository is the source of truth

Read the existing code, tests, and local patterns before making changes.
Prefer repository conventions over generic best practices.

### 2. Solve the requested problem with the smallest safe change

Prefer the smallest coherent change set that fully addresses the task.
Keep diffs local and easy to review.
Do not introduce broad churn for style alone.

### 3. Work in discrete, verifiable steps

Break work into small steps that can be checked.
Do not make a large set of speculative edits and validate only at the end if narrower incremental validation is possible.

### 4. Verification is required for completion

Do not report a task as complete based on reasoning alone.
Completion requires the strongest relevant verification available within scope and environment constraints.

### 5. Be explicit about assumptions and uncertainty

Separate:

* verified facts
* reasoned but unverified claims
* blocked or unknown areas

Do not hide uncertainty behind confident wording.

### 6. Preserve existing behavior unless the task requires change

Avoid incidental behavior changes.
If the requested implementation requires changing existing behavior, keep the change narrowly targeted and make that impact explicit.

### 7. Do not optimize for ceremony

Process exists to reduce risk, not to produce performative planning.
Be concise, operational, and evidence-driven.

---

## Standard Workflow

### 1. Inspect first

Before editing:

* identify the relevant files and code paths
* read the nearest existing implementation patterns
* inspect relevant tests and interfaces
* determine whether the task changes behavior, structure, or both

Do not start by inventing a fresh pattern when the repository already has one.

### 2. Choose the narrowest viable strategy

Select the smallest implementation approach that can satisfy the requested outcome safely.

Bias toward under-changing rather than over-changing.
Do not generalize early.
Do not add abstractions, helpers, or indirection unless the task or local design clearly requires them.

### 3. Establish a verification seam

When practical, identify or create the most direct failing check for the required behavior before finishing the implementation.
This may be:

* a unit test
* an integration test
* an existing failing test
* a type error
* a compile error
* a narrowly targeted runtime check

Prefer targeted checks first, then broader checks as needed.

### 4. Implement incrementally

Make changes in small, coherent steps.
After each meaningful step, run the most relevant targeted verification available.

Avoid mixing unrelated edits in the same change.

### 5. Run the strongest relevant checks before finishing

Before declaring completion, run the strongest relevant checks that are feasible for the affected area.
Examples may include:

* targeted tests
* integration tests
* type checking
* linting
* compilation or build checks
* local runtime validation

Use the repository's documented verification commands.

### 6. Stop when the scoped task is solved and verified

Do not continue into optional cleanup, refactoring, or polish unless explicitly requested or required for correctness.

---

## Scope Discipline

### Stay inside the task boundary

Implement the requested change and the minimum directly supporting changes.
Do not opportunistically fix adjacent issues unless they block the task.
If you encounter adjacent issues, note them separately instead of folding them into the implementation by default.

### Avoid unnecessary churn

Do not introduce:

* broad renames
* file moves
* formatting-only changes mixed with logic changes
* speculative abstractions
* dependency additions without clear need
* architecture rewrites to satisfy a local task

### Broaden scope only with evidence

A broader change is justified only when a narrower change would be:

* incorrect
* unsafe
* inconsistent with required local design constraints
* impossible to verify responsibly

When broadening scope, do the minimum required and explain why.

---

## Verification Standard

### General rule

Every behavior change must be verified unless the environment blocks verification.

### Preferred order

Prefer:

1. the narrowest meaningful tests or checks that directly cover the change
2. the repository's standard static checks for the affected area
3. broader validation when the task touches shared infrastructure or cross-cutting behavior

### When verification is blocked

If tests or checks cannot be run, state explicitly:

* what you intended to verify
* what you actually verified
* what prevented full verification
* what risk remains because of that gap

Do not claim that a change "should work" as a substitute for reporting the verification gap.

---

## Reporting Requirements

When a task is complete, report:

1. what changed
2. why this approach was chosen
3. what was verified
4. any assumptions, limitations, or remaining risks

The report should be concise and factual.
Do not inflate confidence beyond the evidence.

---

## Proportionality

Apply process proportionally to task size and risk.

### Low-risk or trivial changes

For small, local, low-risk changes:

* brief inspection is enough
* lightweight planning is sufficient
* targeted verification may be enough

### Higher-risk changes

For changes involving shared infrastructure, concurrency, persistence, external integrations, or broad surface area:

* inspect more broadly
* make smaller incremental steps
* strengthen test coverage
* run broader checks
* report residual risks more explicitly

---

## Anti-Goals

Avoid the following behaviors:

* claiming completion without verification
* following generic best practices against repository conventions
* introducing abstractions before they are needed
* cleaning up unrelated code as a side quest
* widening scope because the broader solution feels nicer
* preserving ambiguity when a local inspection could resolve it
* hiding blocked work behind vague language
* producing large diffs where a smaller one would solve the task

---

## Relationship to Other Engineering Documents

This document defines implementation behavior.
Other engineering documents define domain-, language-, and subsystem-specific policy.

When working in a given area, follow this document first for process and decision discipline, then apply the relevant local policy documents for modeling, testing, logging, architecture, and checks.

Examples:

* domain modeling conventions define how meaningful concepts should be represented
* testing conventions define what and how to verify
* logging conventions define observability patterns and logger usage
* architecture conventions define layering and boundaries
* checks documentation defines the required local validation commands

These documents complement each other. They should not be treated as optional guidance.

---

## Default Behavior Under Uncertainty

When the task is ambiguous but a conservative interpretation is possible:

* prefer the least risky change that preserves existing behavior
* avoid speculative expansion
* make assumptions explicit in the final report

When the ambiguity prevents responsible implementation:

* stop at the boundary of what can be done safely
* report the blocker precisely
* do not fabricate certainty or invent requirements

---

## Definition of Done

A task is done only when:

* the requested scoped behavior has been implemented
* relevant code follows repository conventions
* appropriate verification has been run, or the verification gap has been stated explicitly
* the completion report accurately reflects what is verified and what is not

Anything less is partial completion, not done.
