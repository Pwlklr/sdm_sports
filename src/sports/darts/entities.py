from typing import List

class DartThrow:
    """
    Value Object representing a single dart thrown.
    Stores the target sector and multiplier, and evaluates points.
    """
    def __init__(self, sector: int, multiplier: int = 1) -> None:
        # Validate sector: 0 (Miss), 1-20 (Standard), 25 (Bullseye)
        if sector not in range(21) and sector != 25:
            raise ValueError(f"Invalid sector: {sector}. Must be 0-20 or 25.")
        
        # Validate multiplier: 1 (Single), 2 (Double), 3 (Treble)
        if multiplier not in [1, 2, 3]:
            raise ValueError(f"Invalid multiplier: {multiplier}. Must be 1, 2, or 3.")
            
        # Specific dartboard constraints
        if sector == 25 and multiplier == 3:
            raise ValueError("Bullseye (25) cannot have a Treble multiplier.")
            
        # Normalize misses (a miss is always 0 points, ignore multiplier)
        if sector == 0:
            self.multiplier = 1
        else:
            self.multiplier = multiplier
            
        self.sector = sector

    @property
    def points(self) -> int:
        """Calculates the total points for this specific throw."""
        return self.sector * self.multiplier

    def __str__(self) -> str:
        if self.sector == 0:
            return "Miss (0)"
        prefix = {1: "Single", 2: "Double", 3: "Treble"}[self.multiplier]
        return f"{prefix} {self.sector}"


class DartTurn:
    """
    Aggregate Root managing a sequence of up to 3 DartThrows.
    Calculates the running total for the visit.
    """
    def __init__(self) -> None:
        self._throws: List[DartThrow] = []
        self.is_busted: bool = False

    def add_throw(self, dart_throw: DartThrow) -> None:
        """Adds a throw to the turn if it is not yet finished."""
        if self.is_finished:
            raise ValueError("Cannot add throw. The turn is already finished or busted.")
        self._throws.append(dart_throw)

    @property
    def throws(self) -> List[DartThrow]:
        """Returns a copy of the recorded throws."""
        return self._throws.copy()

    @property
    def total_points(self) -> int:
        """Calculates the running total of points scored in this turn."""
        return sum(t.points for t in self._throws)

    @property
    def is_finished(self) -> bool:
        """A turn ends if 3 darts are thrown, or if the turn is flagged as busted."""
        return len(self._throws) >= 3 or self.is_busted

    def mark_busted(self) -> None:
        """Flags the turn as busted, forcing it to end."""
        self.is_busted = True