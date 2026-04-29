# Python Domain Modeling Conventions

## Purpose

This document defines how domain concepts must be represented in Python code in this repository.

The goals are:

* eliminate primitive obsession for meaningful domain concepts
* make invalid states harder to represent
* push validation to clear boundaries
* preserve strong static typing across the codebase
* keep domain logic separate from transport, persistence, and framework concerns

This is a correctness policy, not a stylistic preference.

---

## Core Principles

### 1. Model domain concepts explicitly

Do not pass raw primitives such as `str`, `int`, `float`, `dict`, or loosely shaped mappings through the system when they represent specific domain concepts.

If a value has domain meaning, model that meaning in the type system.

Examples:

* use `CorpusId` instead of a raw `str`
* use `DocumentId` instead of a raw `str`
* use a dedicated validated type for constrained strings, slugs, names, paths, or statuses
* use structured models instead of nested untyped dicts for entities, commands, and records

The cost of a stronger type is lower than the cost of leaking ambiguous primitives through the system.

### 2. Make illegal states harder to construct

Domain types should constrain values as early as practical.
The preferred design is:

* validate at the boundary
* convert into strong domain types
* let core logic operate on trusted values

Do not defer basic domain validation deeper into the call graph when it can be expressed clearly at the boundary.

### 3. Prefer explicit domain boundaries

Separate:

* external input and parsing
* validated domain values
* domain logic
* persistence and transport representations

Do not collapse API payloads, ORM rows, queue messages, and domain objects into the same shape unless they are genuinely the same concept.

### 4. Type safety is part of correctness

Static typing is not optional documentation.
New and modified code must preserve complete, explicit type information.

### 5. Domain rules belong near the domain

Validation and invariants should live with the type or model they protect, not scattered across unrelated service methods.

---

## Required Modeling Patterns

## Simple domain scalar types

Use a strong scalar type when a domain concept is fundamentally a validated primitive such as an identifier or constrained string.

Preferred pattern:

1. define a private `NewType`
2. define a validator that returns that `NewType`
3. export a public `Annotated` alias that combines the type with validation metadata
4. optionally provide a parsing helper for non-Pydantic manual construction

Example:

```python
from typing import Annotated, NewType
from pydantic import AfterValidator, Field

_DomainId = NewType("_DomainId", str)


def validate_domain_id(value: str) -> _DomainId:
    if not value.isalnum():
        raise ValueError("Domain ID must be alphanumeric")
    return _DomainId(value)


DomainId = Annotated[
    _DomainId,
    Field(min_length=1),
    AfterValidator(validate_domain_id),
]


def parse_domain_id(value: str) -> _DomainId:
    return validate_domain_id(value)
```

Use this pattern for simple validated scalar concepts where:

* the runtime representation is still a primitive
* the semantic meaning matters everywhere the value appears
* validation can be expressed as a local rule

### When to use a strong scalar type

Use a strong scalar type for:

* identifiers
* names with domain restrictions
* slugs
* normalized keys
* validated tokens or codes
* small constrained values that do not justify a full model

Do not keep these as bare strings just because the runtime payload is simple.

---

## Structured domain models

Use Pydantic `BaseModel` for structured domain data such as:

* entities
* value objects with multiple fields
* aggregates
* validated command or result shapes
* boundary models where parsing and validation are required

Guidelines:

* prefer immutable models (`frozen=True`) when mutation is not part of the domain contract
* type every field explicitly
* use strong scalar domain types for fields where appropriate
* express cross-field invariants using model validators
* keep the model focused on domain meaning, not framework convenience

Example:

```python
from pydantic import BaseModel, ConfigDict, model_validator


class CorpusRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    corpus_id: CorpusId
    name: str
    is_locked: bool
    archived: bool

    @model_validator(mode="after")
    def validate_state(self) -> "CorpusRecord":
        if self.archived and not self.is_locked:
            raise ValueError("Archived corpus must be locked")
        return self
```

### When to use a structured model instead of a scalar type

Use a model when:

* multiple fields together define the concept
* invariants span fields
* the object has stable domain meaning
* passing loose dicts would reduce clarity or safety

---

## Validation Strategy

### Validate at boundaries

Boundary layers should parse untrusted input and convert it into validated domain values.
Typical boundaries include:

* FastAPI request models
* repository deserialization points
* external API adapters
* queue consumers
* configuration loaders

Once data crosses a boundary as a domain type, downstream domain logic should not re-validate basic shape constraints unless that logic is specifically about state transitions or business rules.

### Trust validated internals

Do not repeatedly re-parse or re-check the same domain value in every service method.
Repeated defensive validation inside trusted internals usually signals weak boundaries or the wrong abstraction.

### Keep normalization and validation explicit

If a value requires normalization, make that behavior explicit in the parser or validator.
Do not scatter ad hoc trimming, casing, or format conversion through call sites.

---

## Typing Rules

### Full type hints are required

All functions and methods must have explicit parameter and return types.
Do not omit `-> None` for side-effect-only functions.

### Avoid `Any`

Do not introduce `typing.Any` in new code unless interfacing with an untyped external dependency and there is no narrower honest type.
Convert external data into explicit domain types as early as possible.

### Avoid unchecked dict plumbing

Do not pass around opaque `dict[str, object]` or nested mappings as a substitute for domain models.
If the shape matters, model it.

### Use explicit unions and optionals

When absence or multiple states are valid, express them directly in the type instead of encoding them with sentinel primitives.

### Type ignores require justification

Do not use `# type: ignore` without a short explanation of the limitation being worked around.

### Local type validation is part of completion

Type correctness must be checked locally using the repository's standard type-checking command before declaring implementation complete.

---

## Error Semantics

### Validation errors

For low-level validators and parsing helpers, raise `ValueError` or a more specific domain exception when the value violates the type contract.

### Domain errors

When a failure is about business rules or domain state rather than raw parsing, use a specific domain exception type.
Do not collapse meaningful failures into generic `Exception`.

Examples:

* invalid identifier format: `ValueError` or `InvalidCorpusIdError`
* invalid state transition: `DocumentAlreadyArchivedError`
* missing domain object: `CorpusNotFoundError`

### Do not swallow exceptions silently

Either handle exceptions intentionally at a defined boundary or let them propagate to the application's error-handling layer.
Do not silently convert failures into `None`, empty containers, or default success values unless that behavior is explicitly part of the contract.

---

## Architectural Boundaries

### Keep domain logic pure where possible

Domain modules should not depend on:

* FastAPI request or response objects
* database session objects
* ORM model classes used only for persistence concerns
* transport-specific payload shapes
* logging or tracing as a substitute for explicit return values

Pure domain logic should be reusable independent of framework and infrastructure.

### Separate domain from persistence and transport

Use repositories, mappers, or adapter layers to translate between:

* API payloads and domain models
* storage representations and domain models
* external service payloads and domain models

Do not let persistence or transport concerns dictate the shape of your domain types unless there is a strong, explicit reason.

### Keep domain types cohesive

Related domain types, validators, and exceptions should live together in obvious modules such as:

* `domain.py`
* `models.py`
* `identifiers.py`
* `exceptions.py`

Choose a structure that makes domain concepts easy to discover and hard to duplicate.

---

## Construction and Conversion Rules

### Prefer explicit construction

Construct domain values through typed constructors, validators, or parsing helpers.
Do not cast raw values into domain types without validation unless the value is already trusted and the code path makes that trust obvious.

### Avoid lossy back-and-forth conversion

Do not repeatedly convert domain values back into primitives and then reconstruct them later in the same workflow.
Convert once at the boundary and preserve the typed value as long as possible.

### Keep serialization at the edges

Serialize domain types into JSON-safe or storage-safe forms only when crossing a boundary.
Do not optimize internal APIs around serialized representations.

---

## Review Heuristics

A domain model is usually well-formed if:

* the type names reveal domain meaning clearly
* invalid values are rejected close to the boundary
* core logic operates on trusted, explicit types
* structured data is modeled rather than passed as loose dicts
* business-rule failures use specific exception types
* the design reduces ambiguity without introducing unnecessary abstraction

A model should be reconsidered if:

* the same raw primitive is interpreted differently in multiple places
* validation rules are duplicated across services or handlers
* the code relies on comments to explain what a primitive means
* untyped dicts carry meaningful application state
* transport or persistence shapes leak into core domain logic

---

## Anti-Patterns

Avoid the following:

* raw `str` or `int` values for meaningful domain identifiers
* nested `dict` payloads used as de facto domain models
* validators spread across handlers, services, and repositories with no canonical source
* generic `Exception` for domain-rule failures
* repeated parsing of already-validated values
* framework types embedded in domain models
* using `Any` to sidestep modeling work
* silent fallback behavior that hides invalid state

---

## Minimum Expectations for New Code

For new or modified Python code that introduces or changes domain concepts:

* represent meaningful concepts with strong types
* validate untrusted input at boundaries
* use Pydantic models for structured validated shapes
* keep type hints complete
* use specific exceptions for domain failures
* preserve separation between domain logic and IO/framework concerns
* follow existing local naming and module patterns

When in doubt, prefer a slightly stronger and clearer domain type over a convenient primitive.
