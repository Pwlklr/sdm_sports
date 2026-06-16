from __future__ import annotations

import src.sports.darts.register_contest  # noqa: F401
import src.sports.darts.register_tournament  # noqa: F401
from dataclasses import dataclass

from src.core.contest.command import Command
from src.core.contest.contest_result import ContestResult, RankedEntry
from src.core.contest.event import Event, ProjectionEvent
from src.core.contest.rule_set import RuleSet
from src.core.contestant import IndividualPlayer
from tests.core.contest_test_support import (
    EmptySideMetrics,
    StatefulContestState,
    make_contest,
)
from src.core.tournament import (
    FixtureScheduled,
    RecordMatchOutcome,
    Tournament,
)
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.descriptor import DARTS_SPORT


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


def _make_tournament(blueprint_id: str = "league") -> Tournament:
    return Tournament.from_blueprint(
        "Test Cup",
        DARTS_SPORT.id,
        blueprint_id,
        match_config=DartsMatchConfig(),
    )


def test_f1_league_setup_schedules_fixtures() -> None:
    players = [
        IndividualPlayer("P1", "p1"),
        IndividualPlayer("P2", "p2"),
        IndividualPlayer("P3", "p3"),
    ]
    tournament = _make_tournament("league")
    tournament.open_registration()
    for p in players:
        tournament.register_contestant(p)
    events = tournament.close_registration()
    scheduled = [e for e in events if isinstance(e, FixtureScheduled)]
    assert len(scheduled) == 3
    assert tournament.active_phase_id() == "group"


def test_f2_record_match_outcome_updates_standings() -> None:
    p1 = IndividualPlayer("P1", "p1")
    p2 = IndividualPlayer("P2", "p2")
    tournament = _make_tournament("league")
    tournament.open_registration()
    tournament.register_contestant(p1)
    tournament.register_contestant(p2)
    tournament.close_registration()
    contest_id = tournament.pending_match_ids()[0]
    match = make_contest(DummyState([p1, p2]), DummyRuleSet(), contest_id=contest_id)
    tournament.register_match(match)
    match.handle(EndCommand())
    tournament.handle(
        RecordMatchOutcome(
            contest_id=contest_id,
            result=DummyResult(p1, p2),
        )
    )
    ps = tournament.state.phase_states["group"]
    assert ps.outcomes[contest_id].winner_id == p1.id
    assert ps.standings[p1.id].points == 3


def test_f4_knockout_progressive_schedules_next_round() -> None:
    players = [IndividualPlayer(f"P{i}", f"p{i}") for i in range(1, 5)]
    tournament = _make_tournament("knockout_8")
    tournament.open_registration()
    for p in players:
        tournament.register_contestant(p)
    tournament.close_registration()
    assert len(tournament.pending_match_ids()) == 2
    semis = list(tournament.pending_match_ids())
    for cid in semis:
        match = tournament.get_match(cid)
        assert match is not None
        winner, loser = match.contestants[0], match.contestants[1]
        match.handle(EndCommand())
        tournament.handle(
            RecordMatchOutcome(
                contest_id=cid,
                result=DummyResult(winner, loser),
            )
        )
    pending_after_semis = tournament.pending_match_ids()
    assert len(pending_after_semis) == 1


def test_f10_idempotent_record_match_outcome() -> None:
    p1 = IndividualPlayer("P1", "p1")
    p2 = IndividualPlayer("P2", "p2")
    tournament = _make_tournament("league")
    tournament.open_registration()
    tournament.register_contestant(p1)
    tournament.register_contestant(p2)
    tournament.close_registration()
    contest_id = tournament.pending_match_ids()[0]
    match = make_contest(DummyState([p1, p2]), DummyRuleSet(), contest_id=contest_id)
    tournament.register_match(match)
    match.handle(EndCommand())
    result = DummyResult(p1, p2)
    tournament.handle(RecordMatchOutcome(contest_id=contest_id, result=result))
    history_len = len(tournament.history)
    tournament.handle(RecordMatchOutcome(contest_id=contest_id, result=result))
    assert len(tournament.history) == history_len


def test_tournament_from_events_replay() -> None:
    from src.core.tournament.blueprint_factory import TournamentBlueprintFactory

    tournament = _make_tournament("league")
    tournament.open_registration()
    p1 = IndividualPlayer("P1", "p1")
    tournament.register_contestant(p1)
    events = tournament.history
    blueprint = TournamentBlueprintFactory.get("league")
    replayed = Tournament.from_events(
        "Test Cup",
        DARTS_SPORT.id,
        blueprint,
        events,
        tournament_id=tournament.id,
    )
    assert replayed.state.contestants[p1.id] == p1.name
    assert replayed.state.registration_open is True


def test_world_cup_blueprint_has_two_macro_phases() -> None:
    from src.core.tournament.blueprint_factory import TournamentBlueprintFactory

    bp = TournamentBlueprintFactory.get("world_cup")
    assert len(bp.phases) == 2
    assert bp.phases[0].id == "group"
    assert bp.phases[1].id == "knockout"
    assert bp.phases[1].requires == "group"


def test_correct_match_outcome_upserts() -> None:
    from src.core.tournament.command import CorrectMatchOutcome

    p1 = IndividualPlayer("P1", "p1")
    p2 = IndividualPlayer("P2", "p2")
    tournament = _make_tournament("league")
    tournament.open_registration()
    tournament.register_contestant(p1)
    tournament.register_contestant(p2)
    tournament.close_registration()
    contest_id = tournament.pending_match_ids()[0]
    match = make_contest(DummyState([p1, p2]), DummyRuleSet(), contest_id=contest_id)
    tournament.register_match(match)
    match.handle(EndCommand())
    tournament.handle(
        RecordMatchOutcome(contest_id=contest_id, result=DummyResult(p1, p2))
    )
    tournament.handle(
        CorrectMatchOutcome(contest_id=contest_id, result=DummyResult(p2, p1))
    )
    assert (
        tournament.state.phase_states["group"].outcomes[contest_id].winner_id == p2.id
    )
