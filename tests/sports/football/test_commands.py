from src.core.contest import Contest
from src.core.contestant import Team
from src.sports.football.commands import (
    CommitFoulCommand,
    EndPeriodCommand,
    PenaltyKickCommand,
    ScoreGoalCommand,
    StartFootballMatchCommand,
)
from src.sports.football.config import FootballMatchConfig
from src.sports.football.ruleset import FootballRuleSet
from src.sports.football.state import FootballContestState, MatchPhase


def _contest() -> Contest:
    home = Team("Home", "home")
    away = Team("Away", "away")
    state = FootballContestState([home, away], config=FootballMatchConfig())
    return Contest([home, away], state, FootballRuleSet())


def test_start_command_kicks_off() -> None:
    contest = _contest()
    StartFootballMatchCommand().execute(contest)
    state = contest.current_state
    assert isinstance(state, FootballContestState)
    # MatchStarted has no handler; periods start lazily on the first real event.
    assert state.periods == []


def test_score_goal_command() -> None:
    contest = _contest()
    ScoreGoalCommand(team_index=0).execute(contest)
    state = contest.current_state
    assert isinstance(state, FootballContestState)
    assert state.scores["home"] == 1


def test_commit_foul_command() -> None:
    contest = _contest()
    CommitFoulCommand(team_index=1, card="red", offender_id="x").execute(contest)
    state = contest.current_state
    assert isinstance(state, FootballContestState)
    assert state.disciplinary.is_dismissed("x")


def test_end_period_command() -> None:
    contest = _contest()
    EndPeriodCommand().execute(contest)
    state = contest.current_state
    assert isinstance(state, FootballContestState)
    assert state.current_period is not None
    assert state.current_period.is_finished or len(state.periods) == 2


def test_penalty_kick_command() -> None:
    contest = _contest()
    state = contest.current_state
    assert isinstance(state, FootballContestState)
    state.phase = MatchPhase.PENALTIES

    PenaltyKickCommand(team_index=0, scored=True).execute(contest)
    assert state.penalty_scores["home"] == 1
