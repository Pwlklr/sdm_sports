from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import replace
from typing import Any

from src.core.contest.contest import Contest
from src.core.contestant.models import Contestant
from src.core.tournament.blueprint import TournamentBlueprint
from src.core.tournament.blueprint_factory import TournamentBlueprintFactory
from src.core.tournament.command import (
    CloseRegistration,
    OpenRegistration,
    RegisterContestantRef,
    TournamentCommand,
)
from src.core.tournament.event import (
    TournamentEvent,
    TournamentProjectionEvent,
)
from src.core.tournament.match_provider import MatchProvider
from src.core.tournament.phase_standings_view import PhaseStandingsView
from src.core.tournament.sport_tournament_profile import SportTournamentProfile
from src.core.tournament.sport_tournament_registry import SportTournamentRegistry
from src.core.tournament.tournament_policy import DefaultTournamentPolicy, TournamentPolicy
from src.core.tournament.tournament_state import DefaultTournamentState


class ContestMatchProvider:
    def __init__(self, sport_id: str, registry: dict[str, Contest]) -> None:
        self._sport_id = sport_id
        self._registry = registry

    def create(
        self,
        sides: list[Contestant],
        *,
        match_config: Any,
        contest_id: str | None = None,
        suspended_player_ids: frozenset[str] | None = None,
    ) -> Contest:
        from src.core.contest.contest_factory import ContestFactory

        options: dict[str, Any] = {}
        if suspended_player_ids:
            options["suspended_player_ids"] = suspended_player_ids
        contest = ContestFactory.create(
            self._sport_id,
            sides,
            match_config,
            contest_id=contest_id,
            **options,
        )
        self._registry[contest.id] = contest
        return contest


class Tournament:
    """Event-sourced aggregate root for a competition."""

    def __init__(
        self,
        name: str,
        tournament_id: str,
        sport_id: str,
        blueprint: TournamentBlueprint,
        *,
        policy: TournamentPolicy | None = None,
        profile: SportTournamentProfile | None = None,
        state: DefaultTournamentState | None = None,
        match_registry: dict[str, Contest] | None = None,
    ) -> None:
        self.id = tournament_id
        self.name = name
        self._sport_id = sport_id
        self._blueprint = blueprint
        self._policy = policy or DefaultTournamentPolicy()
        self._profile = profile or SportTournamentRegistry.get(sport_id)
        self._match_registry = match_registry if match_registry is not None else {}
        self._match_provider = ContestMatchProvider(sport_id, self._match_registry)
        self._contestant_registry: dict[str, Contestant] = {}
        phases = self._policy.build_phases(blueprint)
        self._state = state or DefaultTournamentState(
            sport_id=sport_id,
            blueprint_id=blueprint.id,
            phases=phases,
        )
        self._history: list[TournamentEvent] = []

    @classmethod
    def from_blueprint(
        cls,
        name: str,
        sport_id: str,
        blueprint_id: str,
        *,
        tournament_id: str | None = None,
        match_config: Any = None,
    ) -> Tournament:
        blueprint = TournamentBlueprintFactory.get(blueprint_id)
        if match_config is not None:
            from src.core.tournament.blueprint import PhaseDefinition

            phases = tuple(
                PhaseDefinition(
                    id=p.id,
                    name=p.name,
                    format=p.format,
                    scheduling_mode=p.scheduling_mode,
                    match_config=match_config,
                    qualification=p.qualification,
                    requires=p.requires,
                    group_count=p.group_count,
                )
                for p in blueprint.phases
            )
            blueprint = replace(blueprint, phases=phases)
        return cls(
            name,
            tournament_id or str(uuid.uuid4()),
            sport_id,
            blueprint,
        )

    @classmethod
    def from_events(
        cls,
        name: str,
        sport_id: str,
        blueprint: TournamentBlueprint,
        events: Iterable[TournamentEvent],
        *,
        tournament_id: str | None = None,
        profile: SportTournamentProfile | None = None,
    ) -> Tournament:
        tournament = cls(
            name,
            tournament_id or str(uuid.uuid4()),
            sport_id,
            blueprint,
            profile=profile,
        )
        tournament._history = list(events)
        tournament._rebuild_state()
        return tournament

    @property
    def history(self) -> list[TournamentEvent]:
        return self._history.copy()

    @property
    def state(self) -> DefaultTournamentState:
        return self._state

    @property
    def is_completed(self) -> bool:
        return self._state.is_complete

    @property
    def matches(self) -> dict[str, Contest]:
        return dict(self._match_registry)

    def get_match(self, contest_id: str) -> Contest | None:
        return self._match_registry.get(contest_id)

    def register_contestant(self, contestant: Contestant) -> list[TournamentEvent]:
        self._contestant_registry[contestant.id] = contestant
        return self.handle(
            RegisterContestantRef(contestant=contestant)
        )

    def open_registration(self) -> list[TournamentEvent]:
        return self.handle(OpenRegistration())

    def close_registration(self) -> list[TournamentEvent]:
        events = self.handle(CloseRegistration())
        return events

    def handle(self, command: TournamentCommand) -> list[TournamentEvent]:
        emitted: list[TournamentEvent] = []
        queue: list[TournamentEvent] = list(
            self._policy.decide(
                command,
                self._state,
                self._history,
                blueprint=self._blueprint,
                profile=self._profile,
                match_provider=self._match_provider,
                contestant_registry=self._contestant_registry,
            )
        )
        while queue:
            fact = queue.pop(0)
            emitted.extend(self._record_event(fact))
            if isinstance(fact, TournamentProjectionEvent):
                for reaction in self._policy.react(
                    fact,
                    self._state,
                    blueprint=self._blueprint,
                    profile=self._profile,
                    match_provider=self._match_provider,
                    contestant_registry=self._contestant_registry,
                ):
                    queue.append(reaction)
        return emitted

    def _record_event(self, fact: TournamentEvent) -> list[TournamentEvent]:
        if isinstance(fact, TournamentProjectionEvent):
            self._state = self._state.apply(fact)
        self._history.append(fact)
        return [fact]

    def _rebuild_state(self) -> None:
        self._state = DefaultTournamentState(
            sport_id=self._sport_id,
            blueprint_id=self._blueprint.id,
            phases=self._policy.build_phases(self._blueprint),
        )
        for event in self._history:
            if isinstance(event, TournamentProjectionEvent):
                self._state = self._state.apply(event)

    def standings_view(self) -> PhaseStandingsView:
        return PhaseStandingsView(self._profile.tiebreaker)

    def active_phase_id(self) -> str | None:
        return self._state.active_phase_id

    def pending_match_ids(self) -> list[str]:
        ps = self._state.active_phase_state()
        if ps is None:
            return []
        return sorted(ps.pending_fixture_contest_ids())
