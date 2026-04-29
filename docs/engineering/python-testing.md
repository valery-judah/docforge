# Python Testing Conventions

## Purpose

This document defines the testing policy for Python code in this repository.

The goals are:

* verify behavior with the smallest reliable test surface
* keep tests readable, deterministic, and cheap to run
* align tests with the repository's domain modeling, typing, and logging conventions
* catch regressions without coupling tests to incidental implementation details

This document complements the repository's architecture and check guidance. It does not redefine layering rules or the required verification commands.

---

## Core Principles

### 1. Test behavior, not incidental structure

Prefer tests that validate observable behavior, contracts, and domain rules.
Do not lock tests to private implementation details unless there is no better seam.

### 2. Use the narrowest meaningful test

Start with the smallest test that can prove the requirement:

* pure domain logic: unit test
* service orchestration across collaborators: service-level test
* framework wiring, serialization, auth, dependency injection: integration or API test

Do not reach for end-to-end style tests when a narrower test proves the same behavior.

### 3. Prefer deterministic tests

Tests must be stable across runs and environments.
Avoid dependence on wall-clock time, random values, global process state, network access, or shared mutable fixtures unless those dependencies are explicitly controlled.

### 4. Keep tests aligned with domain types

Where production code uses validated domain types, tests should use those same types and constructors rather than bypassing validation with raw primitives.
Use realistic domain values, not arbitrary strings and dicts, unless the test is specifically about invalid input.

### 5. Fail at boundaries, trust validated internals

Boundary tests should verify validation, parsing, and error mapping.
Internal domain tests should assume validated inputs unless the domain object itself owns the validation rule under test.

### 6. Every behavior change needs verification

For any behavior change, add or update tests unless the environment or code shape makes that infeasible.
If a test cannot be added, state the reason explicitly in the implementation summary.

---

## Test Categories

### Unit tests

Use unit tests for:

* pure functions
* validators and parsing helpers
* domain models and domain services
* business rules
* error conditions with no framework or IO dependency

A good unit test:

* runs without network or database access
* uses explicit inputs and outputs
* avoids heavy mocking
* asserts one coherent behavior

Examples:

* `DomainId` rejects invalid values
* a Pydantic model enforces a cross-field invariant
* a domain service raises a specific domain exception for an invalid transition

### Service-level tests

Use service-level tests for application services that coordinate collaborators such as repositories, queues, or external clients.

These tests should:

* instantiate the service directly
* inject fakes, stubs, or narrow mocks for collaborators
* verify orchestration and domain outcomes
* avoid framework bootstrapping unless framework behavior is the subject of the test

Prefer simple fakes over deeply configured mocks when practical.

### Integration tests

Use integration tests when the behavior depends on wiring between real components, such as:

* repository implementations
* persistence mappings
* FastAPI routing and dependency injection
* request/response serialization
* middleware interactions
* logging context propagation where that behavior matters

Integration tests should still remain scoped. They should not become broad end-to-end workflows by default.

### API tests

Use API tests for HTTP behavior that must be verified through the actual FastAPI surface, including:

* status codes
* response schemas
* request validation
* dependency overrides
* auth and permission boundaries
* exception-to-response mapping

Prefer API tests over raw endpoint function calls when the behavior depends on FastAPI itself.

---

## What to Test by Concern

### Domain identifiers and validated scalars

Test:

* acceptance of valid values
* rejection of invalid values
* boundary conditions
* any normalization or parsing behavior

Do not duplicate validation logic in the test itself. Use assertions that reflect the public contract.

### Pydantic models

Test:

* required fields
* field validation
* cross-field invariants
* serialization behavior only when it is part of the contract

Avoid snapshotting full model dumps unless the full serialized shape is intentionally stable and important.

### Domain services

Test:

* successful paths
* domain rule enforcement
* raised exception types
* emitted side effects through collaborator calls when those side effects are part of the contract

Do not assert internal call sequences more tightly than necessary.

### Repositories and adapters

Test:

* mapping between storage and domain types
* behavior on not found / conflict / invalid state cases
* transaction or persistence semantics when relevant

Prefer integration tests for real repository implementations.

### FastAPI handlers

Test:

* request validation
* response payloads and status codes
* dependency override behavior
* error mapping
* auth / permission behavior where applicable

Avoid testing framework internals or duplicating FastAPI behavior beyond the application contract.

---

## FastAPI Testing Rules

### Prefer exercising routes through the app surface

If you are testing HTTP behavior, use the FastAPI test client or the repository's established app-level test pattern.
This verifies routing, validation, serialization, and dependency injection together.

### Raw endpoint execution is a special case

Directly calling `route.endpoint(...)` bypasses FastAPI dependency injection.
Only do this when you intentionally want a narrow handler-level test and understand the consequences.

If the endpoint depends on an injected logger, raw endpoint execution must manually bind the logger before invocation; otherwise the default `Depends(...)` object will be passed through and logging calls will fail.

Use the repository's established helper pattern for extracting endpoints and binding dependencies when direct execution is necessary.

### Override dependencies explicitly

When API tests require alternate collaborators, use FastAPI dependency overrides or the repository's equivalent mechanism.
Do not monkeypatch broad global state when a dependency override will provide a cleaner seam.

---

## Logging in Tests

### Do not disable logging behavior accidentally

If logging is part of the tested flow, provide a valid injected logger rather than letting the test fail on an unresolved dependency.

### Prefer injectable loggers in service tests

For services and classes that accept an optional logger, pass a test logger, fake logger, or mock explicitly when the test needs to observe logging behavior.
Otherwise, it is acceptable to ignore logging and focus on the primary business outcome.

### Assert logging only when it is part of the contract

Do not assert on every log line.
Assert logs only when they encode meaningful behavior such as:

* audit or compliance events
* failure classification
* key lifecycle transitions required for observability

When asserting logs, prefer checking stable event names and essential structured fields rather than brittle full-message comparisons.

---

## Use of Mocks, Fakes, and Fixtures

### Prefer fakes over deep mocks

Use small in-memory fakes for repositories and collaborators when they make tests easier to read and less coupled to implementation.

Use mocks when you need to verify:

* that a side effect occurred
* that a collaborator was called with a specific contract
* that a failure path was exercised

Avoid tests that assert long chains of internal calls.

### Keep fixtures explicit and local

Prefer fixtures that represent meaningful reusable setup.
Do not hide the core scenario in layers of indirection.

A fixture is warranted when it:

* removes repeated boilerplate
* encodes a stable domain setup pattern
* creates expensive shared resources safely

A fixture is not warranted when it obscures what the test actually depends on.

### Avoid autouse fixtures except for true global test concerns

Use `autouse=True` sparingly. Global fixtures often make tests harder to reason about.

---

## Data and Time

### Use explicit test data

Construct inputs deliberately.
Avoid placeholder values like `"foo"`, `"bar"`, or unstructured dict blobs when domain-specific values would make the test clearer.

### Control time and randomness

When logic depends on time, generate time values explicitly or freeze time using the repository's established pattern.
When logic depends on randomness or UUID generation, inject a deterministic source where practical.

### No live external services in default test suites

Do not call real network services, queues, or third-party APIs from normal test runs.
Use fakes, stubs, or controlled integration environments.

---

## Assertions

### Assert the contract, not the implementation story

A strong test asserts:

* returned values
* raised exception types
* persisted state
* emitted domain events
* relevant collaborator interactions
* stable log events, when applicable

Avoid asserting incidental formatting, intermediate locals, or exact internal execution order unless those are part of the required contract.

### Prefer specific assertions

Use the most specific assertion that communicates intent.
Examples:

* assert the exact exception class
* assert only the required response fields
* assert stable structured values rather than large snapshots

### Snapshot tests are restricted

Use snapshot tests only when the serialized output is intentionally large, stable, and expensive to assert by hand.
Do not use snapshots as a substitute for understanding the behavior under test.

---

## Typing and Test Code Quality

Test code is production code for correctness purposes.
The same standards apply unless the repository defines a narrower exception.

* Add type hints to new non-trivial fixtures, helpers, and factory functions.
* Keep helper APIs small and explicit.
* Avoid `Any` in tests unless required to interface with untyped third-party tooling.
* Do not use `# type: ignore` without a comment explaining the static-analysis limitation.
* Keep test helpers in the narrowest scope that supports reuse.

---

## Naming and Layout

### Test names

Name tests by behavior, not by function name alone.
Good patterns:

* `test_parse_domain_id_rejects_non_alphanumeric_values`
* `test_create_document_returns_conflict_when_corpus_is_locked`
* `test_readyz_returns_200_when_dependencies_are_healthy`

### Test modules

Match the repository's existing test layout.
In general:

* unit tests should mirror the source module structure
* integration tests should be grouped by boundary or subsystem
* shared helpers should live in explicit support modules, not hidden in unrelated tests

---

## Anti-Patterns

Avoid the following:

* broad end-to-end tests where a unit or integration test would suffice
* asserting private implementation details by default
* brittle mocks tied to call order rather than contract
* raw primitive setup when domain types exist
* hidden global fixtures that mutate shared state
* real network access in normal test runs
* asserting every log call
* snapshotting unstable output
* combining multiple unrelated behaviors in one test

---

## Minimum Expectations for a Change

For most code changes:

* add or update the narrowest meaningful tests
* cover both the primary success path and the relevant failure or boundary path
* keep the test readable without opening multiple helper layers
* use repository domain types, logger patterns, and dependency seams correctly

If the change touches FastAPI handlers, be explicit about whether the behavior is being verified at:

* the raw function level
* the dependency-injected application level

If the change touches validation or typing-sensitive domain logic, include tests that prove the intended boundary behavior.

---

## Review Heuristics

A test is usually good if:

* a reader can identify the behavior under test quickly
* the setup is minimal and domain-relevant
* the assertion is specific and stable
* the test would fail for the intended regression and not for unrelated refactors
* the test size matches the risk and scope of the behavior

A test should be reconsidered if:

* it knows too much about internals
* it requires extensive mocking to stay alive
* it duplicates framework behavior without testing application logic
* it uses unrealistic data that bypasses domain constraints
* it is difficult to explain what regression it protects against
