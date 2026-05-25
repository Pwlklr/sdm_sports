from __future__ import annotations

from abc import ABC


class TournamentState(ABC):
    """
    A structure storing the current state of the tournament across phases.
    """

    is_complete: bool

    def __init__(self) -> None:
        self.is_complete = False
