from typing import List, Optional
from src.core.contestant import Contestant
from src.core.tournament_phase import TournamentPhase

class Tournament:
    """
    The Aggregate Root for a complete competition. 
    Manages player registration, phase transitions, and global state.
    """
    def __init__(self, name: str, tournament_id: str) -> None:
        self.id = tournament_id
        self.name = name
        self.contestants: List[Contestant] = []
        self.phases: List[TournamentPhase] = []
        self.current_phase_idx: int = 0
        self.is_completed: bool = False

    def register_contestant(self, contestant: Contestant) -> None:
        if contestant not in self.contestants:
            self.contestants.append(contestant)

    def add_phase(self, phase: TournamentPhase) -> None:
        self.phases.append(phase)

    @property
    def current_phase(self) -> Optional[TournamentPhase]:
        if not self.phases:
            return None
        if self.current_phase_idx < len(self.phases):
            return self.phases[self.current_phase_idx]
        return None

    def advance_phase(self) -> None:
        """Moves the tournament to the next phase if the current one is done."""
        phase = self.current_phase
        if phase:
            phase.check_completion()
            if phase.is_completed:
                self.current_phase_idx += 1
                
        if self.current_phase_idx >= len(self.phases) and len(self.phases) > 0:
            self.is_completed = True