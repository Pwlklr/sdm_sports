from __future__ import annotations

import pytest

from dataclasses import dataclass

from src.core.contest.command import Command, ReverseDecision
from src.core.contest.contest_state import ContestState
from src.core.contest.event import Event, EventReversed
from src.core.contest.result import Result
from src.core.contest.rule_set import RuleSet
from src.core.contestant.models import IndividualPlayer, Team
from src.core.contest import ContestFactory
from src.sports.darts.contest.commands import RevokeDartThrow, StartMatch as DartsStart, ThrowDart
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.events import DartScored
from src.sports.darts.descriptor import DARTS_SPORT
from src.sports.football.contest.commands import ScoreGoal, StartMatch, VarOverturnGoal
from src.sports.football.contest.events import GoalScored
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.descriptor import FOOTBALL_SPORT
from tests.core.contest_test_support import EmptyResult, StatefulContestState, make_contest


def _two_team_match() -> object:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    match = ContestFactory.create(FOOTBALL_SPORT.id, [home, away], FootballMatchConfig())
    match.handle(StartMatch())
    return match


def test_reversing_a_goal_recomputes_score() -> None:
    match = _two_team_match()
    match.handle(ScoreGoal(team_index=0, minute=10))
    match.handle(ScoreGoal(team_index=0, minute=20))
    goal = next(e for e in match.history if isinstance(e, GoalScored))

    match.handle(VarOverturnGoal(target_event_id=goal.event_id, reason="offside"))

    assert match.current_state.scores["home"] == 1
    assert any(isinstance(e, EventReversed) for e in match.history)
    assert sum(isinstance(e, GoalScored) for e in match.history) == 2


def test_reverse_decision_requires_known_event() -> None:
    match = _two_team_match()
    with pytest.raises(ValueError):
        match.handle(ReverseDecision(target_event_id="does-not-exist"))


def test_reverse_decision_rebuilds_via_state_reset() -> None:
    @dataclass(frozen=True, kw_only=True)
    class Noop(Command):
        pass

    class S(StatefulContestState):
        def apply(self, fact: Event) -> None:
            pass

        def reset(self) -> S:
            return S(self.contestants)

        def build_result(self) -> Result:
            return EmptyResult()

    class R(RuleSet):
        def decide_noop(self, command: Noop, state: S) -> list[Event]:
            return []

        command_handlers = {Noop: decide_noop}
        reaction_handlers = {}

    @dataclass(frozen=True, kw_only=True)
    class DummyFact(Event):
        pass

    contest = make_contest(S([]), R())
    contest._record_event(DummyFact(event_id="x"))
    contest.handle(ReverseDecision(target_event_id="x", reason="test"))
    assert isinstance(contest.current_state, S)


def test_reversal_drops_causal_descendants() -> None:
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    match = ContestFactory.create(DARTS_SPORT.id, players, DartsMatchConfig())
    match.handle(DartsStart())
    match.handle(ThrowDart(sector=20, multiplier=3))
    first_dart = next(e for e in match.history if isinstance(e, DartScored))
    score_after = match.current_state.scores["a"]

    match.handle(RevokeDartThrow(target_event_id=first_dart.event_id, reason="correction"))

    assert match.current_state.scores["a"] == match.current_state.config.starting_score
    assert score_after < match.current_state.config.starting_score
