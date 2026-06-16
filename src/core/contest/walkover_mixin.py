from __future__ import annotations

from abc import abstractmethod

from src.core.contest.contest_state import ContestState
from src.core.contest.event import Event, OfficialOverrideEvent
from src.core.shared import CommandRejected


class WalkoverMixin:
    """
    Reusable mixin providing the two-path walkover decision:

    - Pre-finish (match not yet finished):
      calls ``_walkover_conclusion`` to emit the finishing event.
    - Post-finish (result already recorded):
      calls ``_walkover_override`` to emit an override event.

    An in-progress match (started but not finished) is rejected.

    Sports inherit this mixin and implement the two abstract helpers.
    The concrete AwardWalkover command + winner validation remain in
    each sport's AdminRules mixin so they can stay sport-specific.
    """

    @abstractmethod
    def _walkover_conclusion(
        self, winner_id: str, reason: str, **kwargs: object
    ) -> list[Event]:
        """Emit the sport-specific event that finishes the match with a walkover."""
        ...

    @abstractmethod
    def _walkover_override(
        self, winner_id: str, reason: str, **kwargs: object
    ) -> list[OfficialOverrideEvent]:
        """Emit the sport-specific override event for a post-finish walkover."""
        ...

    def _resolve_walkover(
        self,
        winner_id: str,
        reason: str,
        state: ContestState,
        **kwargs: object,
    ) -> list[Event]:
        """
        Core two-path routing: emit conclusion or override depending on match state.

        Raises ``CommandRejected`` if the match is in-progress (started but not
        finished), because an administrative walkover mid-match is not allowed.
        """
        if state.match_started and not state.is_finished:
            raise CommandRejected(
                "Match in progress — administrative walkover unavailable during play."
            )

        if not state.is_finished:
            return self._walkover_conclusion(winner_id, reason, **kwargs)

        return list(self._walkover_override(winner_id, reason, **kwargs))
