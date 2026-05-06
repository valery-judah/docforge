from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import overload


@dataclass(frozen=True, init=False)
class EmbeddingVector:
    values: tuple[float, ...]

    def __init__(self, values: Iterable[float | int | str]) -> None:
        coerced_values = tuple(float(value) for value in values)
        if not coerced_values:
            raise ValueError("embedding vector must not be empty")
        object.__setattr__(self, "values", coerced_values)

    @property
    def dimensions(self) -> int:
        return len(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self) -> Iterator[float]:
        return iter(self.values)

    @overload
    def __getitem__(self, index: int) -> float: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[float, ...]: ...

    def __getitem__(self, index: int | slice) -> float | tuple[float, ...]:
        return self.values[index]


@dataclass(frozen=True, init=False)
class EmbeddingBatch:
    vectors: tuple[EmbeddingVector, ...]

    def __init__(self, vectors: Iterable[EmbeddingVector]) -> None:
        coerced_vectors = tuple(vectors)
        if coerced_vectors:
            expected_dimensions = coerced_vectors[0].dimensions
            if any(vector.dimensions != expected_dimensions for vector in coerced_vectors):
                raise ValueError("embedding batch vectors must have consistent dimensions")
        object.__setattr__(self, "vectors", coerced_vectors)

    def __len__(self) -> int:
        return len(self.vectors)

    def __iter__(self) -> Iterator[EmbeddingVector]:
        return iter(self.vectors)

    @overload
    def __getitem__(self, index: int) -> EmbeddingVector: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[EmbeddingVector, ...]: ...

    def __getitem__(self, index: int | slice) -> EmbeddingVector | tuple[EmbeddingVector, ...]:
        return self.vectors[index]
