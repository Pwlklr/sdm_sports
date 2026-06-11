from src.core.contest import Contest
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.commands import (
    CommitFoul,
    EndPeriod,
    ScoreGoal,
    StartMatch,
    TakePenaltyKick,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.core.contest import ContestFactory
from src.sports.football.descriptor import FOOTBALL_SPORT
from src.sports.football.contest.state import MatchPhase


def _contest() -> Contest:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("Striker", "player-home-1"))
    away.add_player(IndividualPlayer("Defender", "x"))
    return ContestFactory.create(FOOTBALL_SPORT.id, [home, away], FootballMatchConfig())


def test_start_command_kicks_off() -> None:
    contest = _contest()
    contest.handle(StartMatch())
    state = contest.current_state
    assert state.match_started is True
    assert state.current_period is not None


def test_score_goal_command() -> None:
    contest = _contest()
    contest.handle(StartMatch())
    contest.handle(ScoreGoal(team_index=0, minute=23))
    assert contest.current_state.scores["home"] == 1


def test_commit_foul_command() -> None:
    contest = _contest()
    contest.handle(StartMatch())
    contest.handle(CommitFoul(team_index=1, minute=30, card="red", offender_id="x"))
    assert contest.current_state.disciplinary.is_dismissed("x")


def test_end_period_command() -> None:
    contest = _contest()
    contest.handle(StartMatch())
    contest.handle(EndPeriod())
    assert contest.current_state.current_period is not None


def test_penalty_kick_command() -> None:
    contest = _contest()
    contest.handle(StartMatch())
    contest.current_state.phase = MatchPhase.PENALTIES
    contest.handle(TakePenaltyKick(team_index=0, scored=True))
    assert contest.current_state.penalty_scores["home"] == 1
