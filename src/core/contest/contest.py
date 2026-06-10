from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING, List, Optional

from src.core.contest.command import Command
from src.core.contest.event import Event, EventReversed
from src.core.contest.observer import Subject

if TYPE_CHECKING:
    from src.core.contestant.models import Contestant
    from src.core.contest.contest_state import ContestState
    from src.core.contest.result import Result
    from src.core.contest.result_override import ResultOverride
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
        state_factory: Callable[[], ContestState] | None = None,
    ) -> None:
        super().__init__()
        self.id = contest_id or str(uuid.uuid4())
        self.contestants = contestants
        self.current_state = initial_state
        self._ruleset = ruleset
        self._result_factory = result_factory
        self._state_factory = state_factory
        self.result: Optional[Result] = None
        self.result_override: Optional[ResultOverride] = None
        self._history: list[Event] = []

    @property
    def history(self) -> list[Event]:
        return self._history.copy()

    @property
    def home(self) -> Optional[Contestant]:
        """Home side for a two-sided contest (the first listed contestant)."""
        return self.contestants[0] if len(self.contestants) == 2 else None

    @property
    def away(self) -> Optional[Contestant]:
        """Away side for a two-sided contest (the second listed contestant)."""
        return self.contestants[1] if len(self.contestants) == 2 else None

    @property
    def official_result(self) -> Optional[Result]:
        """The result that counts officially: an administrative override or the sporting result."""
        if self.result_override is not None:
            return self.result_override.result
        return self.result

    def handle(self, command: Command) -> list[Event]:
        emitted: list[Event] = []
        queue: list[Event] = list(self._ruleset.decide(command, self.current_state))

        while queue:
            fact = queue.pop(0)
            self.current_state.apply(fact)
            self._history.append(fact)
            emitted.append(fact)
            self.notify(fact)
            self._refresh_result()

            for reaction in self._ruleset.react(fact, self.current_state):
                queue.append(replace(reaction, caused_by=fact.event_id))

        return emitted

    def reverse_event(self, event_id: str, reason: str = "reversed") -> EventReversed:
        """Withdraw an event by appending a compensating EventReversed and rebuilding state."""
        if self._state_factory is None:
            raise ValueError(
                "Cannot reverse events: this contest was created without a state_factory."
            )
        if not any(event.event_id == event_id for event in self._history):
            raise ValueError(f"Event '{event_id}' is not part of this contest history.")

        marker = EventReversed(target_event_id=event_id, reason=reason)
        self._history.append(marker)
        self._rebuild_state()
        self.notify(marker)
        return marker

    def _reversed_closure(self) -> set[str]:
        """Ids of all events that are withdrawn: directly reversed ones plus their causal descendants."""
        withdrawn: set[str] = {
            event.target_event_id
            for event in self._history
            if isinstance(event, EventReversed)
        }
        changed = True
        while changed:
            changed = False
            for event in self._history:
                if event.caused_by in withdrawn and event.event_id not in withdrawn:
                    withdrawn.add(event.event_id)
                    changed = True
        return withdrawn

    def _rebuild_state(self) -> None:
        assert self._state_factory is not None
        withdrawn = self._reversed_closure()
        self.current_state = self._state_factory()
        self.result = None
        for event in self._history:
            if isinstance(event, EventReversed):
                continue
            if event.event_id in withdrawn:
                continue
            self.current_state.apply(event)
            self._refresh_result()
        self.notify(None)

    def _refresh_result(self) -> None:
        if (
            self.current_state.is_completed
            and self._result_factory
            and self.result is None
        ):
            self.result = self._result_factory(self.current_state)
