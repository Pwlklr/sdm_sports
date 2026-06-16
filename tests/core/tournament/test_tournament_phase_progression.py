"""Tests for tournament phase progression paths.

Covers:
- PhaseCompleted emitted after all RR fixtures resolved
- DrawPerformed / RoundCompleted for DRAW_BETWEEN_ROUNDS knockout
- Group → knockout transition (world_cup blueprint: group phase completes, knockout starts)
- PerformDraw command handled correctly
- TournamentCompleted at end of final phase
"""

from __future__ import annotations

import src.sports.darts.register_contest  # noqa: F401
import src.sports.darts.register_tournament  # noqa: F401
from dataclasses import dataclass

from src.core.contest.command import Command
from src.core.contest.contest_result import ContestResult, RankedEntry
from src.core.contest.event import Event, ProjectionEvent
from src.core.contest.rule_set import RuleSet
from src.core.contestant import IndividualPlayer
from src.core.tournament import FixtureScheduled, RecordMatchOutcome, Tournament
from src.core.tournament.event import (
    PhaseCompleted,
    PhaseStarted,
    RoundCompleted,
    TournamentCompleted,
)
from src.core.tournament.command import PerformDraw
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.descriptor import DARTS_SPORT
from tests.core.contest_test_support import (
    EmptySideMetrics,
    StatefulContestState,
    make_contest,
)

# ---------------------------------------------------------------------------
# Minimal test doubles (matches that can be "ended" on demand)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class EndCommand(Command):
    pass


@dataclass(frozen=True, kw_only=True)
class EndFact(ProjectionEvent):
    pass


class DummyState(StatefulContestState):
    def apply(self, fact: Event) -> DummyState:
        if isinstance(fact, EndFact):
            finished = DummyState(self.contestants)
            finished._finished = True
            return finished
        return DummyState(self.contestants)

    def reset(self) -> DummyState:
        return DummyState(self.contestants)


class DummyRuleSet(RuleSet):
    def decide_end(
        self, command: EndCommand, state: DummyState, history: list[Event]
    ) -> list[Event]:
        return [EndFact()]

    command_handlers = {EndCommand: decide_end}
    reaction_handlers = {}


class DummyResult(ContestResult):
    def __init__(self, winner, loser) -> None:
        self._ranking = (
            RankedEntry(contestant=winner, place=1),
            RankedEntry(contestant=loser, place=2),
        )

    def is_finished(self) -> bool:
        return True

    def ranking(self):
        return self._ranking

    def side_metrics(self):
        return EmptySideMetrics()


def _resolve_match(tournament: Tournament, contest_id: str, players: list) -> None:
    match = make_contest(
        DummyState(players),
        DummyRuleSet(),
        contest_id=contest_id,
    )
    tournament.register_match(match)
    match.handle(EndCommand())
    tournament.handle(
        RecordMatchOutcome(
            contest_id=contest_id,
            result=DummyResult(players[0], players[1]),
        )
    )


def _make_tournament(blueprint_id: str) -> Tournament:
    return Tournament.from_blueprint(
        "Test",
        DARTS_SPORT.id,
        blueprint_id,
        match_config=DartsMatchConfig(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def _get_fixture_sides(tournament: Tournament, contest_id: str, all_players: list):
    """Return the two contestants for a scheduled fixture."""
    fixture_event = next(
        e
        for e in tournament.history
        if hasattr(e, "contest_id") and e.contest_id == contest_id
    )
    side_a = next(p for p in all_players if p.id == fixture_event.side_a_id)
    side_b = next(p for p in all_players if p.id == fixture_event.side_b_id)
    return [side_a, side_b]


def test_phase_completed_emitted_after_all_rr_fixtures_resolved() -> None:
    """After the last RR fixture is recorded, PhaseCompleted must be emitted."""
    players = [IndividualPlayer(f"P{i}", f"p{i}") for i in range(1, 4)]
    tournament = _make_tournament("league")
    tournament.open_registration()
    for p in players:
        tournament.register_contestant(p)
    tournament.close_registration()

    pending = list(tournament.pending_match_ids())
    # 3 players → 3 round-robin fixtures
    assert len(pending) == 3

    for cid in pending[:-1]:
        sides = _get_fixture_sides(tournament, cid, players)
        _resolve_match(tournament, cid, sides)

    # PhaseCompleted should NOT appear yet
    assert not any(isinstance(e, PhaseCompleted) for e in tournament.history)

    # Resolve last fixture
    last_cid = pending[-1]
    sides = _get_fixture_sides(tournament, last_cid, players)
    _resolve_match(tournament, last_cid, sides)

    assert any(isinstance(e, PhaseCompleted) for e in tournament.history)


def test_tournament_completed_after_final_phase() -> None:
    """A single-phase knockout tournament completes after the final match."""
    players = [IndividualPlayer(f"P{i}", f"p{i}") for i in range(1, 3)]
    tournament = _make_tournament("knockout_8")
    tournament.open_registration()
    for p in players:
        tournament.register_contestant(p)
    tournament.close_registration()

    cid = tournament.pending_match_ids()[0]
    sides = _get_fixture_sides(tournament, cid, players)
    _resolve_match(tournament, cid, sides)

    assert any(isinstance(e, TournamentCompleted) for e in tournament.history)
    completed = next(
        e for e in tournament.history if isinstance(e, TournamentCompleted)
    )
    assert completed.champion_id == players[0].id


def test_group_to_knockout_phase_transition() -> None:
    """world_cup blueprint: completing the group phase starts the knockout phase."""
    players = [IndividualPlayer(f"P{i}", f"p{i}") for i in range(1, 5)]
    tournament = _make_tournament("world_cup")
    tournament.open_registration()
    for p in players:
        tournament.register_contestant(p)
    tournament.close_registration()

    assert tournament.active_phase_id() == "group"
    group_fixtures = list(tournament.pending_match_ids())
    assert len(group_fixtures) > 0

    for cid in group_fixtures:
        sides = _get_fixture_sides(tournament, cid, players)
        _resolve_match(tournament, cid, sides)

    # After group completes, knockout phase should start
    phase_started_events = [
        e for e in tournament.history if isinstance(e, PhaseStarted)
    ]
    phase_ids_started = [e.phase_id for e in phase_started_events]
    assert "knockout" in phase_ids_started


def _make_draw_between_rounds_tournament(t_id: str) -> Tournament:
    from src.core.tournament.blueprint_factory import TournamentBlueprintFactory
    from src.core.tournament.scheduling_mode import SchedulingMode
    from dataclasses import replace

    base_bp = TournamentBlueprintFactory.get("knockout_8")
    draw_phase = replace(
        base_bp.phases[0],
        scheduling_mode=SchedulingMode.DRAW_BETWEEN_ROUNDS,
        match_config=DartsMatchConfig(),
    )
    bp = replace(base_bp, phases=(draw_phase,))
    return Tournament("Test", t_id, DARTS_SPORT.id, bp)


def _resolve_all_round0(tournament: Tournament, players: list) -> None:
    """Resolve round-0 fixtures matching each pair from the scheduled slots."""
    for cid in list(tournament.pending_match_ids()):
        # Find the two sides for this fixture from the scheduled events
        fixture_event = next(
            e
            for e in tournament.history
            if hasattr(e, "contest_id") and e.contest_id == cid
        )
        side_a = next(p for p in players if p.id == fixture_event.side_a_id)
        side_b = next(p for p in players if p.id == fixture_event.side_b_id)
        _resolve_match(tournament, cid, [side_a, side_b])


def test_round_completed_emitted_for_draw_between_rounds() -> None:
    """DRAW_BETWEEN_ROUNDS knockout: after a round, RoundCompleted is emitted instead of auto-scheduling."""
    players = [IndividualPlayer(f"P{i}", f"p{i}") for i in range(1, 5)]
    tournament = _make_draw_between_rounds_tournament("t1")
    tournament.open_registration()
    for p in players:
        tournament.register_contestant(p)
    tournament.close_registration()

    round0_fixtures = list(tournament.pending_match_ids())
    assert len(round0_fixtures) == 2

    _resolve_all_round0(tournament, players)

    # After round 0 completes in DRAW_BETWEEN_ROUNDS mode, a RoundCompleted event is emitted
    assert any(isinstance(e, RoundCompleted) for e in tournament.history)
    rc = next(e for e in tournament.history if isinstance(e, RoundCompleted))
    assert rc.round_index == 0


def test_perform_draw_schedules_next_round_fixtures() -> None:
    """PerformDraw command schedules the next round after a RoundCompleted."""
    players = [IndividualPlayer(f"P{i}", f"p{i}") for i in range(1, 5)]
    tournament = _make_draw_between_rounds_tournament("t2")
    tournament.open_registration()
    for p in players:
        tournament.register_contestant(p)
    tournament.close_registration()

    _resolve_all_round0(tournament, players)

    fixtures_before = len(tournament.history)
    tournament.handle(PerformDraw(phase_id=tournament.active_phase_id() or "knockout"))

    # PerformDraw should schedule new FixtureScheduled events
    new_fixtures = [
        e
        for e in tournament.history[fixtures_before:]
        if isinstance(e, FixtureScheduled)
    ]
    assert len(new_fixtures) >= 1
