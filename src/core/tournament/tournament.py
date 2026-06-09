from __future__ import annotations

from typing import Any, List, Optional

from src.core.contest.contest import Contest
from src.core.contestant.models import Contestant
from src.core.tournament.tournament_disciplinary_board import TournamentDisciplinaryBoard
from src.core.tournament.event import (
    MatchCompleted,
    MatchScheduled,
    PhaseCompleted,
    PlayerRegistered,
    RegistrationClosed,
    RegistrationOpened,
    TournamentEvent,
)
from src.core.tournament.phase import GroupStagePhase, TournamentPhase
from src.core.tournament.tournament_registration import TournamentRegistration
from src.core.tournament.tournament_scheduler import TournamentScheduler


class Tournament:
    """
    Aggregate root for a complete competition.
    Processes tournament events and coordinates phases, registration, and scheduling.
    """

    def __init__(
        self,
        name: str,
        tournament_id: str,
        registration: TournamentRegistration | None = None,
        scheduler: TournamentScheduler | None = None,
        disciplinary_board: TournamentDisciplinaryBoard | None = None,
    ) -> None:
        self.id = tournament_id
        self.name = name
        self.contestants: List[Contestant] = []
        self.phases: List[TournamentPhase] = []
        self.current_phase_idx: int = 0
        self.is_completed: bool = False

        self.registration = registration or TournamentRegistration()
        self.scheduler = scheduler or TournamentScheduler()
        self.disciplinary_board = disciplinary_board or TournamentDisciplinaryBoard()
        self._history: list[TournamentEvent] = []

    @property
    def history(self) -> list[TournamentEvent]:
        return self._history.copy()

    @property
    def current_phase(self) -> Optional[TournamentPhase]:
        if not self.phases:
            return None
        if self.current_phase_idx < len(self.phases):
            return self.phases[self.current_phase_idx]
        return None

    def add_phase(self, phase: TournamentPhase) -> None:
        self.phases.append(phase)

    def register_contestant(self, contestant: Contestant) -> None:
        if contestant not in self.contestants:
            self.contestants.append(contestant)

    def handle(self, event: TournamentEvent) -> list[TournamentEvent]:
        self._history.append(event)
        emitted: list[TournamentEvent] = []

        if isinstance(event, RegistrationOpened):
            return emitted

        if isinstance(event, PlayerRegistered):
            self.register_contestant(event.contestant)
            return emitted

        if isinstance(event, RegistrationClosed):
            return emitted

        if isinstance(event, MatchScheduled):
            return emitted

        if isinstance(event, MatchCompleted):
            phase = self.current_phase
            if phase is not None:
                phase.record_match_result(event.match)
                if phase.check_completion():
                    qualifiers = phase.get_qualifiers()
                    emitted.append(PhaseCompleted(phase.name, qualifiers))
                    self._advance_phase()
            return emitted

        if isinstance(event, PhaseCompleted):
            return emitted

        return emitted

    def schedule_phase_fixtures(
        self,
        factory: Any,
        config: Any,
        contestants: list[Contestant] | None = None,
    ) -> list[TournamentEvent]:
        phase = self.current_phase
        if phase is None:
            return []

        pool = contestants if contestants is not None else self.contestants
        if isinstance(phase, GroupStagePhase):
            phase.initialize_standings(pool)

        emitted: list[TournamentEvent] = []
        for side_a, side_b in phase.get_matchups(pool):
            match = factory.create_contest([side_a, side_b], config)
            phase.add_contest(match)
            emitted.extend(self.scheduler.schedule_match(match))
        return emitted

    def open_registration(self) -> list[TournamentEvent]:
        emitted: list[TournamentEvent] = []
        for event in self.registration.open_registration():
            emitted.extend(self.handle(event))
        return emitted

    def register_player(self, contestant: Contestant) -> list[TournamentEvent]:
        events = self.registration.register(contestant)
        emitted: list[TournamentEvent] = []
        for event in events:
            emitted.extend(self.handle(event))
        return emitted

    def close_registration(
        self,
        factory: Any,
        config: Any,
    ) -> list[TournamentEvent]:
        events = self.registration.close_registration()
        emitted: list[TournamentEvent] = []
        for event in events:
            emitted.extend(self.handle(event))

        schedule_events = self.schedule_phase_fixtures(factory, config)
        for scheduled in schedule_events:
            self.handle(scheduled)
            emitted.append(scheduled)
        return emitted

    def complete_match(self, match: Contest) -> list[TournamentEvent]:
        return self.handle(MatchCompleted(match, match.result))

    def _advance_phase(self) -> None:
        self.current_phase_idx += 1
        if self.current_phase_idx >= len(self.phases) and self.phases:
            self.is_completed = True

    def advance_phase(self) -> None:
        phase = self.current_phase
        if phase:
            phase.check_completion()
            if phase.is_completed:
                self._advance_phase()
