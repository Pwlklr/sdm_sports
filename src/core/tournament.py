from __future__ import annotations
import uuid
from typing import List

from src.core.tournament_aggregates import (
    TournamentRegistration, TournamentScheduler, TournamentDisciplinaryBoard
)
from src.core.tournament_phase import TournamentPhase

class Tournament:
    """
    Aggregate Root: Represents a complete tournament lifecycle.
    Owns the registration, scheduling, disciplinary tracking, and phases.
    """
    def __init__(self, name: str, tournament_id: str | None = None) -> None:
        self.id = tournament_id or str(uuid.uuid4())
        self.name = name
        
        # Sub-Aggregates
        self.registration = TournamentRegistration()
        self.scheduler = TournamentScheduler()
        self.disciplinary_board = TournamentDisciplinaryBoard()
        
        self.phases: List[TournamentPhase] = []

    def add_phase(self, phase: TournamentPhase) -> None:
        """Appends a new phase (e.g., Group Stage, Knockout) to the tournament."""
        self.phases.append(phase)