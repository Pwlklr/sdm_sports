import pytest

from src.core.contest.event import EventReversed
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.darts.contest.commands import StartMatch as DartsStart, ThrowDart
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.darts_sport_factory import DartsSportFactory
from src.sports.darts.contest.events import DartScored
from src.sports.football.contest.commands import ScoreGoal, StartMatch
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.events import GoalScored
from src.sports.football.football_sport_factory import FootballSportFactory


def _two_team_match() -> object:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    match = FootballSportFactory().create_contest([home, away], FootballMatchConfig())
    match.handle(StartMatch())
    return match


def test_reversing_a_goal_recomputes_score() -> None:
    match = _two_team_match()
    match.handle(ScoreGoal(team_index=0, minute=10))
    match.handle(ScoreGoal(team_index=0, minute=20))
    goal = next(e for e in match.history if isinstance(e, GoalScored))

    match.reverse_event(goal.event_id, reason="offside")

    assert match.current_state.scores["home"] == 1
    assert any(isinstance(e, EventReversed) for e in match.history)
    assert sum(isinstance(e, GoalScored) for e in match.history) == 2


def test_reverse_event_requires_known_event() -> None:
    match = _two_team_match()
    with pytest.raises(ValueError):
        match.reverse_event("does-not-exist")


def test_reverse_event_without_state_factory_raises() -> None:
    from src.core.contest import Contest, ContestState, RuleSet
    from src.core.contest.command import Command
    from src.core.contest.event import Event
    from dataclasses import dataclass

    @dataclass(frozen=True, kw_only=True)
    class Noop(Command):
        pass

    class S(ContestState):
        def apply(self, fact: Event) -> None:
            pass

    class R(RuleSet):
        def decide_noop(self, command: "Noop", state: "S") -> list[Event]:
            return []

        command_handlers = {Noop: decide_noop}
        reaction_handlers = {}

    contest = Contest([], S(), R(), state_factory=None)
    with pytest.raises(ValueError):
        contest.reverse_event("x")


def test_reversal_drops_causal_descendants() -> None:
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    match = DartsSportFactory().create_contest(players, DartsMatchConfig())
    match.handle(DartsStart())
    match.handle(ThrowDart(sector=20, multiplier=3))
    first_dart = next(e for e in match.history if isinstance(e, DartScored))
    score_after = match.current_state.scores["a"]

    match.reverse_event(first_dart.event_id, reason="correction")

    assert match.current_state.scores["a"] == match.current_state.starting_score
    assert score_after < match.current_state.starting_score
