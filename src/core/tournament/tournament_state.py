from __future__ import annotations

from abc import ABC


class TournamentState(ABC):
    """
    A structure storing the current state of the tournament across phases.
    """

    is_complete: bool

    def __init__(self) -> None:
        self.is_complete = False


class DefaultTournamentState(TournamentState):
    """Concrete tournament status: which phase is active and whether it is finished."""

    def __init__(self, phase_count: int = 0) -> None:
        super().__init__()
        self.current_phase_index = 0
        self.phase_count = phase_count

    def advance_phase(self) -> None:
        self.current_phase_index += 1
        if self.phase_count and self.current_phase_index >= self.phase_count:
            self.is_complete = True
