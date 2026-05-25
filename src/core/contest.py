from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.observer import Subject

if TYPE_CHECKING:
    from src.core.contest_event import ContestEvent
    from src.core.contest_state import ContestState
    from src.core.ruleset import RuleSet
    from src.core.team import Team


class Contest(Subject):
    contest_id: str
    teams: list[Team]
    current_state: ContestState

    def __init__(
        self,
        contest_id: str,
        teams: list[Team],
        initial_state: ContestState,
        ruleset: RuleSet,
    ) -> None:
        super().__init__()
        self.contest_id = contest_id
        self.teams = teams
        self.current_state = initial_state
        self._ruleset = ruleset

    def process_event(self, event: ContestEvent) -> None:
        self._ruleset.evaluate(event, self.current_state)
        self.notify()
