from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, List, Optional

from src.core.contest.command import Command
from src.core.contest.event import Event
from src.core.contest.observer import Subject

if TYPE_CHECKING:
    from src.core.contestant.models import Contestant
    from src.core.contest.contest_state import ContestState
    from src.core.contest.result import Result
    from src.core.contest.rule_set import RuleSet


class Contest(Subject):
    """
    Aggregate root orchestrating decide -> apply -> notify -> react for each command.
    """

    def __init__(
        self,
        contestants: List[Contestant],
        initial_state: ContestState,
        ruleset: RuleSet,
        contest_id: str | None = None,
        result_factory: Callable[[ContestState], Result] | None = None,
    ) -> None:
        super().__init__()
        self.id = contest_id or str(uuid.uuid4())
        self.contestants = contestants
        self.current_state = initial_state
        self._ruleset = ruleset
        self._result_factory = result_factory
        self.result: Optional[Result] = None
        self._history: list[Event] = []

    @property
    def history(self) -> list[Event]:
        return self._history.copy()

    def handle(self, command: Command) -> list[Event]:
        emitted: list[Event] = []
        queue: list[Event] = list(self._ruleset.decide(command, self.current_state))

        while queue:
            fact = queue.pop(0)
            self.current_state.apply(fact)
            self._history.append(fact)
            emitted.append(fact)
            self.notify(fact)

            if (
                self.current_state.is_completed
                and self._result_factory
                and self.result is None
            ):
                self.result = self._result_factory(self.current_state)

            queue.extend(self._ruleset.react(fact, self.current_state))

        return emitted
