from __future__ import annotations

import uuid

from collections.abc import Iterable

from dataclasses import replace

from typing import TYPE_CHECKING, List

from src.core.contest.command import Command, ReverseDecision
from src.core.contest.contest_result import ContestResult
from src.core.contest.contest_session import ContestSessionStatus
from src.core.contest.contest_state import ContestState
from src.core.contest.result_builder import ResultBuilder
from src.core.contest.rule_set import RuleSet
from src.core.contest.event import (
    Event,
    EventReversed,
    OfficialOverrideEvent,
    ProjectionEvent,
)
from src.core.contest.observer import Subject

if TYPE_CHECKING:
    from src.core.contestant.models import Contestant


class Contest(Subject):
    """Event-sourced aggregate root."""

    def __init__(
        self,
        state: ContestState,
        ruleset: RuleSet,
        result_builder: ResultBuilder,
        contest_id: str | None = None,
    ) -> None:
        super().__init__()
        self.id = contest_id or str(uuid.uuid4())
        self.current_state = state
        self._ruleset = ruleset
        self._result_builder = result_builder
        self._history: list[Event] = []
        self._suspended = False

    @property
    def is_suspended(self) -> bool:
        return self._suspended

    @property
    def session_status(self) -> ContestSessionStatus:
        if self.current_state.is_finished:
            return ContestSessionStatus.FINISHED
        if self._suspended:
            return ContestSessionStatus.SUSPENDED
        if self.current_state.match_started:
            return ContestSessionStatus.IN_PROGRESS
        return ContestSessionStatus.NOT_STARTED

    def suspend(self) -> None:
        if self.current_state.is_finished:
            raise ValueError("Cannot suspend a finished contest.")
        if not self.current_state.match_started:
            raise ValueError("Cannot suspend a contest that has not started.")
        self._suspended = True

    def resume(self) -> None:
        if not self._suspended:
            raise ValueError("Contest is not suspended.")
        self._suspended = False

    @property
    def contestants(self) -> List[Contestant]:
        return self.current_state.contestants

    @classmethod
    def from_events(
        cls,
        state: ContestState,
        ruleset: RuleSet,
        result_builder: ResultBuilder,
        events: Iterable[Event],
        contest_id: str | None = None,
    ) -> Contest:
        """Rehydrate a contest by replaying a persisted event log."""
        contest = cls(state, ruleset, result_builder, contest_id=contest_id)
        contest._history = list(events)
        contest._rebuild_state()
        return contest

    @property
    def history(self) -> list[Event]:
        return self._history.copy()

    def active_domain_events(self) -> list[Event]:
        """Domain facts currently affecting the projection (reversal candidates)."""
        return self._effective_base_events()

    def get_played_result(self) -> ContestResult:
        if not self.current_state.is_finished:
            raise ValueError("Match is not completed.")
        return self._result_builder.build(self.current_state, self._history)

    def get_official_result(self) -> ContestResult:
        if not self.current_state.is_finished:
            raise ValueError("Match is not completed.")
        walkovers = self._effective_walkover_events()
        if not walkovers:
            return self._result_builder.build(self.current_state, self._history)
        return self._result_builder.build_official(
            self.current_state, self._history, walkovers[-1]
        )

    def has_official_override(self) -> bool:
        """True when an active administrative override sits on the log."""
        return bool(self._effective_walkover_events())

    def official_override_reason(self) -> str | None:
        walkovers = self._effective_walkover_events()
        if not walkovers:
            return None
        return getattr(walkovers[-1], "reason", None)

    def handle(self, command: Command) -> list[Event]:
        if isinstance(command, ReverseDecision):
            return self._handle_reversal(command)
        return self._handle_domain_command(command)

    def _handle_domain_command(self, command: Command) -> list[Event]:
        emitted: list[Event] = []
        queue: list[Event] = list(
            self._ruleset.decide(command, self.current_state, self._history)
        )

        while queue:
            fact = queue.pop(0)
            self._record_event(fact)
            emitted.append(fact)

            for reaction in self._ruleset.react(fact, self.current_state):
                queue.append(replace(reaction, caused_by=fact.event_id))

        return emitted

    def _handle_reversal(self, command: ReverseDecision) -> list[Event]:
        markers = self._ruleset.decide_reversal(
            command, self.current_state, self._history
        )
        emitted: list[Event] = []
        for marker in markers:
            self._record_meta_event(marker)
            emitted.append(marker)
        self._rebuild_state()
        return emitted

    def _record_event(self, fact: Event) -> None:
        if isinstance(fact, OfficialOverrideEvent):
            self._record_audit_event(fact)
            return
        self.current_state = self.current_state.apply(fact)
        self._history.append(fact)
        self.notify(fact)

    def _record_audit_event(self, fact: Event) -> None:
        self._history.append(fact)
        self.notify(fact)

    def _record_meta_event(self, fact: Event) -> None:
        self._history.append(fact)
        self.notify(fact)

    def _rebuild_state(self) -> None:
        """Replay the effective projection log onto a fresh state."""
        self.current_state = self.current_state.reset()
        for event in self._effective_base_events():
            self.current_state = self.current_state.apply(event)
        self.notify(None)

    def _get_withdrawn_event_ids(self) -> set[str]:
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

    def _effective_events(self) -> list[Event]:
        withdrawn = self._get_withdrawn_event_ids()
        return [
            event
            for event in self._history
            if not isinstance(event, EventReversed) and event.event_id not in withdrawn
        ]

    def _effective_base_events(self) -> list[Event]:
        return [
            event
            for event in self._effective_events()
            if isinstance(event, ProjectionEvent)
        ]

    def _effective_walkover_events(self) -> list[OfficialOverrideEvent]:
        return [
            event
            for event in self._effective_events()
            if isinstance(event, OfficialOverrideEvent)
        ]
