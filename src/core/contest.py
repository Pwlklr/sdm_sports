from typing import List
from src.core.state import ContestState
from src.core.ruleset import RuleSet
from src.core.events import ContestEvent
from src.core.participants import Team
from src.core.observer import Subject


class Contest(Subject):
    """A generic container representing a single match between teams[cite: 6]."""

    def __init__(
        self,
        contest_id: str,
        teams: List[Team],
        initial_state: ContestState,
        ruleset: RuleSet,
    ):
        super().__init__()
        self.contest_id = contest_id
        self.teams = teams
        self.current_state = initial_state
        self._ruleset = ruleset

    def process_event(self, event: ContestEvent) -> None:
        """Delegates the event to be handled based on the RuleSet assigned[cite: 6]."""
        self._ruleset.evaluate(event, self.current_state)
        # Notify observers (like the TournamentPhase) that state may have changed
        self.notify()
