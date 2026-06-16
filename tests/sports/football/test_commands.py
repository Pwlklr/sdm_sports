from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.commands import (
    CommitFoul,
    EndPeriod,
    ScoreGoal,
    StartMatch,
    SubmitLineup,
    TakePenaltyKick,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.core.contest import ContestFactory
from src.sports.football.descriptor import FOOTBALL_SPORT
from src.sports.football.contest.football_contest_state import MatchPhase


def _contest():
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("Striker", "player-home-1"))
    away.add_player(IndividualPlayer("Defender", "x"))
    config = FootballMatchConfig(players_on_pitch=1, min_players_on_pitch=1)
    contest = ContestFactory.create(FOOTBALL_SPORT.id, [home, away], config)
    contest.handle(StartMatch())
    contest.handle(
        SubmitLineup(team_index=0, starting=("player-home-1",), bench=()),
    )
    contest.handle(SubmitLineup(team_index=1, starting=("x",), bench=()))
    return contest


def _contest_not_started():
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("Striker", "player-home-1"))
    away.add_player(IndividualPlayer("Defender", "x"))
    config = FootballMatchConfig(players_on_pitch=1, min_players_on_pitch=1)
    return ContestFactory.create(FOOTBALL_SPORT.id, [home, away], config)


def test_start_command_kicks_off() -> None:
    contest = _contest_not_started()
    contest.handle(StartMatch())
    state = contest.current_state
    assert state.match_started is True
    assert state.current_period is not None


def test_score_goal_command() -> None:
    contest = _contest()
    contest.handle(ScoreGoal(team_index=0, minute=23))
    assert contest.current_state.scores["home"] == 1


def test_commit_foul_command() -> None:
    contest = _contest()
    contest.handle(CommitFoul(team_index=1, minute=30, card="red", offender_id="x"))
    assert contest.current_state.disciplinary.is_dismissed("x")


def test_end_period_command() -> None:
    contest = _contest_not_started()
    contest.handle(StartMatch())
    contest.handle(EndPeriod())
    assert contest.current_state.current_period is not None


def test_penalty_kick_command() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("Striker", "player-home-1"))
    away.add_player(IndividualPlayer("Defender", "x"))
    config = FootballMatchConfig(
        allow_draw=False,
        extra_time_halves=0,
        penalty_shootout_rounds=1,
        players_on_pitch=1,
        min_players_on_pitch=1,
    )
    contest = ContestFactory.create(FOOTBALL_SPORT.id, [home, away], config)
    contest.handle(StartMatch())
    contest.handle(
        SubmitLineup(team_index=0, starting=("player-home-1",), bench=()),
    )
    contest.handle(SubmitLineup(team_index=1, starting=("x",), bench=()))
    # Exhaust regulation periods to reach penalty phase
    contest.handle(EndPeriod())
    contest.handle(EndPeriod())
    assert contest.current_state.phase == MatchPhase.PENALTIES
    contest.handle(TakePenaltyKick(team_index=0, scored=True))
    assert contest.current_state.penalty_scores["home"] == 1
