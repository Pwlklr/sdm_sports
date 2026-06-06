from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, List, Optional

from src.core.observer import Subject

if TYPE_CHECKING:
    from src.core.contestant import Contestant
    from src.core.contest_event import ContestEvent
    from src.core.contest_state import ContestState
    from src.core.ruleset import RuleSet
    from src.core.result import Result


class Contest(Subject):
    """
    Base generic Match/Contest.
    """
    def __init__(
        self,
        contestants: List[Contestant],
        initial_state: ContestState,
        ruleset: RuleSet,
        contest_id: str | None = None
    ) -> None:
        super().__init__()
        self.id = contest_id or str(uuid.uuid4())
        self.contestants = contestants
        self.current_state = initial_state
        self._ruleset = ruleset
        self.result: Optional[Result] = None

    def process_event(self, event: ContestEvent) -> None:
        """
        Applies an event through the ruleset, which mutates the state.
        """
        self._ruleset.evaluate(event, self.current_state)
        self.notify()