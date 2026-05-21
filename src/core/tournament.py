from typing import List
from src.core.participants import Team
from src.core.contest import Contest
from src.core.observer import Observer

class TournamentPhase(Observer):
    """Represents a specific stage of the tournament[cite: 6]."""
    def __init__(self, phase_id: str):
        self.phase_id = phase_id
        self.contests: List[Contest] = []
        self.completed_contests: int = 0

    def add_contest(self, contest: Contest) -> None:
        self.contests.append(contest)
        # The phase observes the contest for completion
        contest.attach(self)

    def update(self, subject: Contest) -> None:
        """Triggered by the Contest.notify() method."""
        if subject.current_state.is_final:
            self.completed_contests += 1
            # Future implementation: Trigger recalculation of standings here

class Tournament:
    """The root aggregate managing the global list of participating teams and all phases[cite: 6]."""
    def __init__(self, tournament_id: str):
        self.tournament_id = tournament_id
        self.teams: List[Team] = []
        self.phases: List[TournamentPhase] = []

    def add_team(self, team: Team) -> None:
        self.teams.append(team)

    def add_phase(self, phase: TournamentPhase) -> None:
        self.phases.append(phase)