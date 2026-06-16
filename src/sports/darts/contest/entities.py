from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class DartThrow:
    sector: int
    multiplier: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "multiplier", 1 if self.sector == 0 else self.multiplier
        )

    @property
    def points(self) -> int:
        return self.sector * self.multiplier

    def __str__(self) -> str:
        if self.sector == 0:
            return "Miss (0)"
        prefix = {1: "Single", 2: "Double", 3: "Treble"}[self.multiplier]
        return f"{prefix} {self.sector}"


@dataclass(frozen=True, kw_only=True)
class DartTurn:
    throws: tuple[DartThrow, ...] = ()

    def with_throw(self, dart_throw: DartThrow) -> DartTurn:
        return DartTurn(throws=self.throws + (dart_throw,))

    @property
    def total_points(self) -> int:
        return sum(t.points for t in self.throws)
