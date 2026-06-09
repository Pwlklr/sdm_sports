from typing import List


class DartThrow:
    """Read-model value for a recorded throw (geometry validated at system entry)."""

    def __init__(self, sector: int, multiplier: int = 1) -> None:
        self.sector = sector
        self.multiplier = 1 if sector == 0 else multiplier

    @property
    def points(self) -> int:
        return self.sector * self.multiplier

    def __str__(self) -> str:
        if self.sector == 0:
            return "Miss (0)"
        prefix = {1: "Single", 2: "Double", 3: "Treble"}[self.multiplier]
        return f"{prefix} {self.sector}"


class DartTurn:
    """Read model: throws recorded during a single visit."""

    def __init__(self) -> None:
        self._throws: List[DartThrow] = []

    def add_throw(self, dart_throw: DartThrow) -> None:
        self._throws.append(dart_throw)

    @property
    def throws(self) -> List[DartThrow]:
        return self._throws.copy()

    @property
    def total_points(self) -> int:
        return sum(t.points for t in self._throws)
