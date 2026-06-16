from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, ClassVar, TypeAlias

from src.core.contestant.models import Contestant, IndividualPlayer, Team
from src.core.shared.command_rejected import reject
from src.core.tournament.blueprint import PhaseDefinition, TournamentBlueprint
from src.core.tournament.command import (
    CloseRegistration,
    CorrectMatchOutcome,
    IssueSuspension,
    LiftSuspension,
    OpenRegistration,
    PerformDraw,
    RecordMatchOutcome,
    RegisterContestant,
    RegisterContestantRef,
    RegisterSquad,
    ScheduleFixtures,
    StartPhase,
    TournamentCommand,
)
from src.core.tournament.event import (
    ContestantRegistered,
    DrawPerformed,
    FixtureScheduled,
    MatchOutcomeRecorded,
    PhaseCompleted,
    PhaseStarted,
    RegistrationClosed,
    RegistrationOpened,
    SquadRegistered,
    RoundCompleted,
    SuspensionIssued,
    SuspensionLifted,
    SuspensionServed,
    TournamentCompleted,
    TournamentEvent,
    TournamentProjectionEvent,
)
from src.core.tournament.fixture_scheduler import (
    BracketScheduler,
    DoubleEliminationScheduler,
    FixtureScheduler,
    RoundRobinScheduler,
    ScheduledPairing,
)
from src.core.tournament.match_provider import MatchProvider
from src.core.tournament.phase import Phase
from src.core.tournament.phase_format import PhaseFormat
from src.core.tournament.phase_qualifiers import PhaseQualifiers
from src.core.tournament.phase_state import (
    BracketPhaseState,
    PhaseState,
    RoundRobinPhaseState,
)
from src.core.tournament.scheduling_mode import SchedulingMode
from src.core.tournament.sport_tournament_profile import SportTournamentProfile
from src.core.tournament.tournament_state import DefaultTournamentState

Handler: TypeAlias = Callable[..., list[TournamentEvent]]


class TournamentPolicy(ABC):
    command_handlers: ClassVar[dict[type[TournamentCommand], Handler]] = {}
    reaction_handlers: ClassVar[dict[type[TournamentProjectionEvent], Handler]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls is TournamentPolicy:
            return
        merged_cmd: dict[type[TournamentCommand], Handler] = {}
        merged_react: dict[type[TournamentProjectionEvent], Handler] = {}
        for base in reversed(cls.__mro__):
            for key in ("command_handlers", "_own_command_handlers"):
                handlers = getattr(base, key, None)
                if isinstance(handlers, dict):
                    merged_cmd.update(handlers)
            for key in ("reaction_handlers", "_own_reaction_handlers"):
                handlers = getattr(base, key, None)
                if isinstance(handlers, dict):
                    merged_react.update(handlers)
        cls.command_handlers = merged_cmd
        cls.reaction_handlers = merged_react

    def decide(
        self,
        command: TournamentCommand,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        *,
        blueprint: TournamentBlueprint,
        profile: SportTournamentProfile,
        match_provider: MatchProvider | None = None,
        contestant_registry: dict[str, Any] | None = None,
    ) -> list[TournamentEvent]:
        handler = self.command_handlers.get(type(command))
        if handler:
            return handler(
                self,
                command,
                state,
                history,
                blueprint=blueprint,
                profile=profile,
                match_provider=match_provider,
                contestant_registry=contestant_registry,
            )
        return []

    def react(
        self,
        fact: TournamentProjectionEvent,
        state: DefaultTournamentState,
        *,
        blueprint: TournamentBlueprint,
        profile: SportTournamentProfile,
        match_provider: MatchProvider | None = None,
        contestant_registry: dict[str, Any] | None = None,
    ) -> list[TournamentEvent]:
        handler = self.reaction_handlers.get(type(fact))
        if handler:
            return handler(
                self,
                fact,
                state,
                blueprint=blueprint,
                profile=profile,
                match_provider=match_provider,
                contestant_registry=contestant_registry,
            )
        return []

    @abstractmethod
    def build_phases(self, blueprint: TournamentBlueprint) -> tuple[Phase, ...]:
        pass


def _scheduler_for(phase_def: PhaseDefinition) -> FixtureScheduler:
    if phase_def.format == PhaseFormat.ROUND_ROBIN:
        return RoundRobinScheduler()
    if phase_def.format == PhaseFormat.DOUBLE_ELIMINATION:
        return DoubleEliminationScheduler()
    return BracketScheduler(phase_def.scheduling_mode)


def _pool_for_phase(
    state: DefaultTournamentState, phase_def: PhaseDefinition
) -> list[str]:
    if phase_def.requires:
        ids = state.qualifiers_by_phase.get(phase_def.requires)
        if ids:
            return list(ids)
    return list(state.contestants.keys())


def _validate_players_in_roster(
    contestant: Contestant, player_ids: tuple[str, ...]
) -> None:
    if isinstance(contestant, Team):
        roster_ids = {player.id for player in contestant.roster}
        for player_id in player_ids:
            if player_id not in roster_ids:
                reject(
                    f"Player '{player_id}' is not on team {contestant.name}'s roster."
                )
        return
    if isinstance(contestant, IndividualPlayer):
        for player_id in player_ids:
            if player_id != contestant.id:
                reject(
                    f"Player '{player_id}' is not contestant {contestant.name}."
                )


def _validate_squad_for_contestant(
    contestant: Contestant,
    player_ids: tuple[str, ...],
    profile: SportTournamentProfile,
) -> None:
    _validate_players_in_roster(contestant, player_ids)
    profile.squad_policy.validate_squad(contestant, player_ids)


def _emit_fixtures(
    policy: TournamentPolicy,
    state: DefaultTournamentState,
    phase_def: PhaseDefinition,
    pairings: list[ScheduledPairing],
    *,
    match_provider: MatchProvider | None,
    contestant_registry: dict[str, Any] | None,
) -> list[TournamentEvent]:
    events: list[TournamentEvent] = []
    registry = contestant_registry or {}
    suspended = state.discipline.suspended_ids()

    # Serve one match of suspension for all suspended players at fixture creation.
    # The player is excluded from this fixture's squad — that counts as serving.
    for player_id in suspended:
        events.append(SuspensionServed(player_id=player_id))

    for pairing in pairings:
        contest_id = f"{phase_def.id}-{pairing.slot_id}"
        if match_provider is not None:
            sides = []
            for cid in (pairing.side_a_id, pairing.side_b_id):
                contestant = registry.get(cid)
                if contestant is None:
                    reject(f"Unknown contestant '{cid}'")
                sides.append(contestant)
            eligible_squads = {
                pairing.side_a_id: frozenset(state.squads[pairing.side_a_id]),
                pairing.side_b_id: frozenset(state.squads[pairing.side_b_id]),
            }
            match_provider.create(
                sides,
                match_config=phase_def.match_config,
                contest_id=contest_id,
                suspended_player_ids=suspended,
                eligible_squads=eligible_squads,
            )
        events.append(
            FixtureScheduled(
                phase_id=phase_def.id,
                contest_id=contest_id,
                slot_id=pairing.slot_id,
                side_a_id=pairing.side_a_id,
                side_b_id=pairing.side_b_id,
                round_index=pairing.round_index,
            )
        )
    return events


class RegistrationPolicyMixin(TournamentPolicy):
    _own_command_handlers: ClassVar[dict[type[TournamentCommand], Handler]] = {}

    def decide_open_registration(
        self,
        command: OpenRegistration,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        if state.registration_open:
            reject("Registration is already open")
        return [RegistrationOpened()]

    def decide_register_contestant(
        self,
        command: RegisterContestant,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        *,
        profile: SportTournamentProfile,
        contestant_registry: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        if not state.registration_open:
            reject("Registration is closed")
        if command.contestant_id in state.contestants:
            return []
        events: list[TournamentEvent] = [
            ContestantRegistered(
                contestant_id=command.contestant_id,
                contestant_name=command.contestant_name,
            )
        ]
        registry = contestant_registry or {}
        contestant = registry.get(command.contestant_id)
        if contestant is not None:
            auto = profile.squad_policy.default_squad(contestant)
            if auto is not None:
                _validate_squad_for_contestant(contestant, auto, profile)
                events.append(
                    SquadRegistered(
                        contestant_id=command.contestant_id,
                        player_ids=auto,
                    )
                )
        return events

    def decide_register_squad(
        self,
        command: RegisterSquad,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        *,
        profile: SportTournamentProfile,
        contestant_registry: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        if not state.registration_open:
            reject("Registration is closed")
        if command.contestant_id not in state.contestants:
            reject(f"Contestant '{command.contestant_id}' is not registered.")
        registry = contestant_registry or {}
        contestant = registry.get(command.contestant_id)
        if contestant is None:
            reject(f"Unknown contestant '{command.contestant_id}'.")
        _validate_squad_for_contestant(contestant, command.player_ids, profile)
        return [
            SquadRegistered(
                contestant_id=command.contestant_id,
                player_ids=command.player_ids,
            )
        ]

    def decide_register_contestant_ref(
        self,
        command: RegisterContestantRef,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        c = command.contestant
        return self.decide_register_contestant(
            RegisterContestant(contestant_id=c.id, contestant_name=c.name),
            state,
            history,
            **kwargs,
        )

    def decide_close_registration(
        self,
        command: CloseRegistration,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        *,
        blueprint: TournamentBlueprint,
        profile: SportTournamentProfile,
        contestant_registry: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        if not state.registration_open:
            reject("Registration is not open")
        registry = contestant_registry or {}
        for contestant_id, contestant_name in state.contestants.items():
            if contestant_id not in state.squads:
                reject(
                    f"Contestant '{contestant_name}' has no tournament squad registered."
                )
            contestant = registry.get(contestant_id)
            if contestant is None:
                reject(f"Unknown contestant '{contestant_id}'.")
            player_ids = state.squads[contestant_id]
            _validate_squad_for_contestant(contestant, player_ids, profile)
        events: list[TournamentEvent] = [RegistrationClosed()]
        first = blueprint.first_phase()
        if first is not None:
            events.append(
                PhaseStarted(
                    phase_id=first.id,
                    phase_name=first.name,
                    format=first.format,
                    scheduling_mode=first.scheduling_mode,
                )
            )
        return events


RegistrationPolicyMixin._own_command_handlers = {
    OpenRegistration: RegistrationPolicyMixin.decide_open_registration,
    RegisterContestant: RegistrationPolicyMixin.decide_register_contestant,
    RegisterContestantRef: RegistrationPolicyMixin.decide_register_contestant_ref,
    RegisterSquad: RegistrationPolicyMixin.decide_register_squad,
    CloseRegistration: RegistrationPolicyMixin.decide_close_registration,
}


class PhaseProgressionPolicyMixin(TournamentPolicy):
    _own_command_handlers: ClassVar[dict[type[TournamentCommand], Handler]] = {}
    _own_reaction_handlers: ClassVar[dict[type[TournamentProjectionEvent], Handler]] = (
        {}
    )

    def decide_start_phase(
        self,
        command: StartPhase,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        *,
        blueprint: TournamentBlueprint,
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        phase_def = blueprint.get_phase(command.phase_id or "")
        if phase_def is None:
            first = blueprint.first_phase()
            if first is None:
                reject("No phases in blueprint")
            phase_def = first
        if phase_def.requires and phase_def.requires not in state.completed_phase_ids:
            reject(f"Phase '{phase_def.requires}' is not completed")
        return [
            PhaseStarted(
                phase_id=phase_def.id,
                phase_name=phase_def.name,
                format=phase_def.format,
                scheduling_mode=phase_def.scheduling_mode,
            )
        ]

    def decide_schedule_fixtures(
        self,
        command: ScheduleFixtures,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        *,
        blueprint: TournamentBlueprint,
        match_provider: MatchProvider | None = None,
        contestant_registry: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        phase = state.active_phase()
        if phase is None:
            reject("No active phase")
        phase_def = blueprint.get_phase(phase.id)
        if phase_def is None:
            reject("Unknown active phase")
        pool = _pool_for_phase(state, phase_def)
        if len(pool) < 2:
            reject("At least two contestants required")
        scheduler = _scheduler_for(phase_def)
        pairings = scheduler.initial_round(pool, round_index=0)
        return _emit_fixtures(
            self,
            state,
            phase_def,
            pairings,
            match_provider=match_provider,
            contestant_registry=contestant_registry,
        )

    def decide_perform_draw(
        self,
        command: PerformDraw,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        *,
        blueprint: TournamentBlueprint,
        match_provider: MatchProvider | None = None,
        contestant_registry: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        phase = state.active_phase()
        if phase is None:
            reject("No active phase")
        ps = state.active_phase_state()
        if not isinstance(ps, BracketPhaseState):
            reject("Draw only applies to bracket phases")
        if ps.status.value != "awaiting_draw":
            reject("Phase is not awaiting draw")
        phase_def = blueprint.get_phase(phase.id)
        if phase_def is None:
            reject("Unknown phase")
        prev_round = ps.current_round_index - 1
        winners_by_slot: dict[str, str] = {
            slot.slot_id: slot.winner_id
            for slot in ps.slots
            if slot.round_index == prev_round and slot.winner_id
        }
        scheduler = _scheduler_for(phase_def)
        pairings = scheduler.next_round(
            list(winners_by_slot.values()),
            round_index=ps.current_round_index,
            winners_by_slot=winners_by_slot,
        )
        events: list[TournamentEvent] = [
            DrawPerformed(
                phase_id=phase.id,
                round_index=ps.current_round_index,
                pairings=tuple((p.side_a_id, p.side_b_id) for p in pairings),
            )
        ]
        events.extend(
            _emit_fixtures(
                self,
                state,
                phase_def,
                pairings,
                match_provider=match_provider,
                contestant_registry=contestant_registry,
            )
        )
        return events

    def react_phase_started(
        self,
        fact: PhaseStarted,
        state: DefaultTournamentState,
        *,
        blueprint: TournamentBlueprint,
        match_provider: MatchProvider | None = None,
        contestant_registry: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        return self.decide_schedule_fixtures(
            ScheduleFixtures(phase_id=fact.phase_id),
            state,
            [],
            blueprint=blueprint,
            match_provider=match_provider,
            contestant_registry=contestant_registry,
            **kwargs,
        )


PhaseProgressionPolicyMixin._own_command_handlers = {
    StartPhase: PhaseProgressionPolicyMixin.decide_start_phase,
    ScheduleFixtures: PhaseProgressionPolicyMixin.decide_schedule_fixtures,
    PerformDraw: PhaseProgressionPolicyMixin.decide_perform_draw,
}

PhaseProgressionPolicyMixin._own_reaction_handlers = {
    PhaseStarted: PhaseProgressionPolicyMixin.react_phase_started,
}


def _phase_for_contest(
    state: DefaultTournamentState, contest_id: str
) -> tuple[str, PhaseState] | None:
    for phase_id, ps in state.phase_states.items():
        if contest_id in {f.contest_id for f in ps.fixtures}:
            return phase_id, ps
    return None


class MatchOutcomePolicyMixin(TournamentPolicy):
    _own_command_handlers: ClassVar[dict[type[TournamentCommand], Handler]] = {}
    _own_reaction_handlers: ClassVar[dict[type[TournamentProjectionEvent], Handler]] = (
        {}
    )

    def _record_outcome(
        self,
        command: RecordMatchOutcome | CorrectMatchOutcome,
        state: DefaultTournamentState,
        *,
        profile: SportTournamentProfile,
    ) -> list[TournamentEvent]:
        located = _phase_for_contest(state, command.contest_id)
        if located is None:
            reject("Contest does not belong to any phase")
        phase_id, ps = located
        if command.contest_id not in ps.outcomes and command.contest_id not in {
            f.contest_id for f in ps.fixtures
        }:
            reject("Contest does not belong to any phase")
        snapshot = profile.outcome_interpreter.interpret(
            command.contest_id, command.result
        )
        existing = ps.outcomes.get(command.contest_id)
        if (
            existing is not None
            and isinstance(command, RecordMatchOutcome)
            and existing.same_as(snapshot)
        ):
            return []
        return [MatchOutcomeRecorded(phase_id=phase_id, snapshot=snapshot)]

    def decide_record_match_outcome(
        self,
        command: RecordMatchOutcome,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        *,
        profile: SportTournamentProfile,
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        return self._record_outcome(command, state, profile=profile)

    def decide_correct_match_outcome(
        self,
        command: CorrectMatchOutcome,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        *,
        profile: SportTournamentProfile,
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        return self._record_outcome(command, state, profile=profile)

    def react_match_outcome_recorded(
        self,
        fact: MatchOutcomeRecorded,
        state: DefaultTournamentState,
        *,
        blueprint: TournamentBlueprint,
        profile: SportTournamentProfile,
        match_provider: MatchProvider | None = None,
        contestant_registry: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        events: list[TournamentEvent] = []
        if profile.discipline_carryover is not None:
            for player_id, matches in profile.discipline_carryover.carryover(
                fact.snapshot, state.discipline
            ):
                events.append(SuspensionIssued(player_id=player_id, matches=matches))
        phase_def = blueprint.get_phase(fact.phase_id)
        ps = state.phase_states.get(fact.phase_id)
        if phase_def is None or ps is None:
            return events

        view = PhaseQualifiers(profile.tiebreaker)

        if isinstance(ps, RoundRobinPhaseState):
            if ps.all_fixtures_resolved():
                quals = view.resolve(state, fact.phase_id, phase_def.qualification)
                events.append(
                    PhaseCompleted(phase_id=fact.phase_id, qualifier_ids=quals)
                )
            return events

        if isinstance(ps, BracketPhaseState):
            bps: BracketPhaseState = ps
            for slot in bps.slots:
                if slot.contest_id == fact.snapshot.contest_id:
                    bps = replace_slot_winner(
                        bps, slot.slot_id, fact.snapshot.winner_id
                    )
                    break
            round_idx = _round_for_contest(bps, fact.snapshot.contest_id)
            if round_idx is not None and bps.round_complete(round_idx):
                total_rounds = _total_rounds(len(_pool_for_phase(state, phase_def)))
                if round_idx >= total_rounds - 1 and fact.snapshot.winner_id:
                    events.append(
                        PhaseCompleted(
                            phase_id=fact.phase_id,
                            qualifier_ids=(fact.snapshot.winner_id,),
                        )
                    )
                    return events
                if phase_def.scheduling_mode == SchedulingMode.DRAW_BETWEEN_ROUNDS:
                    events.append(
                        RoundCompleted(phase_id=fact.phase_id, round_index=round_idx)
                    )
                    return events
                winners = _winners_for_round(bps, round_idx)
                scheduler = _scheduler_for(phase_def)
                pairings = scheduler.next_round(
                    winners,
                    round_index=round_idx + 1,
                    winners_by_slot=_winners_by_slot(bps, round_idx),
                )
                events.extend(
                    _emit_fixtures(
                        self,
                        state,
                        phase_def,
                        pairings,
                        match_provider=match_provider,
                        contestant_registry=contestant_registry,
                    )
                )
        return events

    def react_phase_completed(
        self,
        fact: PhaseCompleted,
        state: DefaultTournamentState,
        *,
        blueprint: TournamentBlueprint,
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        next_phase = blueprint.next_phase_after(fact.phase_id)
        if next_phase is None:
            champion = fact.qualifier_ids[0] if fact.qualifier_ids else None
            return [TournamentCompleted(champion_id=champion)]
        return [
            PhaseStarted(
                phase_id=next_phase.id,
                phase_name=next_phase.name,
                format=next_phase.format,
                scheduling_mode=next_phase.scheduling_mode,
            )
        ]


def replace_slot_winner(
    bps: BracketPhaseState, slot_id: str, winner_id: str | None
) -> BracketPhaseState:
    from dataclasses import replace

    slots = tuple(
        replace(s, winner_id=winner_id) if s.slot_id == slot_id else s
        for s in bps.slots
    )
    return replace(bps, slots=slots)


def _round_for_contest(bps: BracketPhaseState, contest_id: str) -> int | None:
    for f in bps.fixtures:
        if f.contest_id == contest_id:
            return f.round_index
    return None


def _winners_for_round(bps: BracketPhaseState, round_index: int) -> list[str]:
    winners: list[str] = []
    for slot in bps.slots:
        if slot.round_index == round_index and slot.winner_id:
            winners.append(slot.winner_id)
    return winners


def _winners_by_slot(bps: BracketPhaseState, round_index: int) -> dict[str, str]:
    result: dict[str, str] = {}
    for slot in bps.slots:
        if slot.round_index == round_index and slot.winner_id:
            result[slot.slot_id] = slot.winner_id
    return result


def _total_rounds(n: int) -> int:
    import math

    if n < 2:
        return 0
    return int(math.ceil(math.log2(n)))


MatchOutcomePolicyMixin._own_command_handlers = {
    RecordMatchOutcome: MatchOutcomePolicyMixin.decide_record_match_outcome,
    CorrectMatchOutcome: MatchOutcomePolicyMixin.decide_correct_match_outcome,
}
MatchOutcomePolicyMixin._own_reaction_handlers = {
    MatchOutcomeRecorded: MatchOutcomePolicyMixin.react_match_outcome_recorded,
    PhaseCompleted: MatchOutcomePolicyMixin.react_phase_completed,
}


class SuspensionPolicyMixin(TournamentPolicy):
    """Admin commands for manually issuing and lifting player suspensions."""

    _own_command_handlers: ClassVar[dict[type[TournamentCommand], Handler]] = {}

    def decide_issue_suspension(
        self,
        command: IssueSuspension,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        if command.matches <= 0:
            reject("Suspension must be for at least one match.")
        return [SuspensionIssued(player_id=command.player_id, matches=command.matches)]

    def decide_lift_suspension(
        self,
        command: LiftSuspension,
        state: DefaultTournamentState,
        history: list[TournamentEvent],
        **kwargs: Any,
    ) -> list[TournamentEvent]:
        if command.player_id not in state.discipline.suspensions:
            reject(f"Player '{command.player_id}' has no active suspension.")
        return [SuspensionLifted(player_id=command.player_id)]


SuspensionPolicyMixin._own_command_handlers = {
    IssueSuspension: SuspensionPolicyMixin.decide_issue_suspension,
    LiftSuspension: SuspensionPolicyMixin.decide_lift_suspension,
}


class DefaultTournamentPolicy(
    RegistrationPolicyMixin,
    PhaseProgressionPolicyMixin,
    MatchOutcomePolicyMixin,
    SuspensionPolicyMixin,
    TournamentPolicy,
):
    def build_phases(self, blueprint: TournamentBlueprint) -> tuple[Phase, ...]:
        return tuple(
            Phase(
                id=p.id,
                name=p.name,
                format=p.format,
                scheduling_mode=p.scheduling_mode,
                match_config=p.match_config,
            )
            for p in blueprint.phases
        )
