from typing import List
from src.core.state import ContestState
from src.core.ruleset import RuleSet
from src.core.events import ContestEvent
from src.core.participants import Team

class Contest:
    def __init__(
        self, 
        contest_id: str, 
        teams: List[Team], 
        initial_state: ContestState, 
        ruleset: RuleSet
    ):
        self.contest_id = contest_id
        self.teams = teams
        self.current_state = initial_state
        self._ruleset = ruleset

    def process_event(self, event: ContestEvent) -> None:
        self._ruleset.evaluate(event, self.current_state)