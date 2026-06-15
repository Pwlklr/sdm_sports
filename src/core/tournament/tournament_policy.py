from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.core.tournament.event import (
    MatchCompleted,
    PhaseCompleted,
    PlayerRegistered,
    TournamentEvent,
)

if TYPE_CHECKING:
    from src.core.tournament.tournament import Tournament


class TournamentPolicy(ABC):
    """
    Defines and enforces the global business rules of the entire tournament
    by reacting to lifecycle events.
    """

    @abstractmethod
    def handle(
        self,
        event: TournamentEvent,
        tournament: "Tournament",
    ) -> list[TournamentEvent]:
        pass


class DefaultTournamentPolicy(TournamentPolicy):
    """Standard tournament reactions: register entrants and advance phases as they complete."""

    def handle(
        self,
        event: TournamentEvent,
        tournament: "Tournament",
    ) -> list[TournamentEvent]:
        if isinstance(event, PlayerRegistered):
            tournament.register_contestant(event.contestant)
            return []

        if isinstance(event, MatchCompleted):
            return self._on_match_completed(event, tournament)

        return []

    def _on_match_completed(
        self, event: MatchCompleted, tournament: "Tournament"
    ) -> list[TournamentEvent]:
        phase = tournament.current_phase
        if phase is None:
            return []
        phase.record_match_result(event.match)
        if not phase.check_completion():
            return []
        qualifiers = phase.get_qualifiers()
        tournament.advance_to_next_phase()
        return [PhaseCompleted(phase.name, qualifiers)]
