from __future__ import annotations

from src.core.contest.event import EventReversed
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.commands import (
    CommitFoul,
    RevokeCaution,
    ScoreGoal,
    StartMatch,
    SubmitLineup,
    SubstitutePlayer,
    VarOverturnGoal,
)
from src.sports.football.contest.events import GoalScored, PlayerCautioned, PlayerDismissed
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.core.contest import ContestFactory
from src.sports.football.descriptor import FOOTBALL_SPORT


def _test_config() -> FootballMatchConfig:
    return FootballMatchConfig(players_on_pitch=1, min_players_on_pitch=1)


def _started_match():
    config = _test_config()
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P1", "p1"))
    home.add_player(IndividualPlayer("P2", "p2"))
    away.add_player(IndividualPlayer("A1", "a1"))
    match = ContestFactory.create(FOOTBALL_SPORT.id, [home, away], config)
    match.handle(StartMatch())
    match.handle(SubmitLineup(team_index=0, starting=("p1",), bench=("p2",)))
    match.handle(SubmitLineup(team_index=1, starting=("a1",)))
    return match, home


def test_var_overturn_goal_keeps_later_substitution() -> None:
    match, home = _started_match()
    match.handle(ScoreGoal(team_index=0, minute=10))
    match.handle(
        SubstitutePlayer(
            team_index=0,
            player_out="p1",
            player_in="p2",
            minute=15,
        )
    )
    goal = next(e for e in match.history if isinstance(e, GoalScored))

    match.handle(VarOverturnGoal(target_event_id=goal.event_id, reason="var"))

    state = match.current_state
    assert state.scores["home"] == 0
    lineup = state.lineup_for(home.id)
    assert lineup is not None
    assert not lineup.is_on_pitch("p1")
    assert lineup.is_on_pitch("p2")


def test_revoke_second_yellow_also_withdraws_auto_red() -> None:
    match, home = _started_match()
    match.handle(
        CommitFoul(
            team_index=0,
            minute=10,
            card="yellow",
            offender_id="p1",
        )
    )
    match.handle(
        CommitFoul(
            team_index=0,
            minute=20,
            card="yellow",
            offender_id="p1",
        )
    )
    cautions = [e for e in match.history if isinstance(e, PlayerCautioned)]
    second_yellow = cautions[1]

    match.handle(RevokeCaution(target_event_id=second_yellow.event_id, reason="review"))

    assert not match.current_state.disciplinary.is_dismissed("p1")
    assert match.current_state.disciplinary.yellows_for("p1") == 1


def test_revoke_first_yellow_keeps_second_and_removes_auto_red() -> None:
    match, home = _started_match()
    match.handle(
        CommitFoul(
            team_index=0,
            minute=10,
            card="yellow",
            offender_id="p1",
        )
    )
    match.handle(
        CommitFoul(
            team_index=0,
            minute=20,
            card="yellow",
            offender_id="p1",
        )
    )
    cautions = [e for e in match.history if isinstance(e, PlayerCautioned)]
    first_yellow = cautions[0]

    match.handle(RevokeCaution(target_event_id=first_yellow.event_id, reason="review"))

    assert not match.current_state.disciplinary.is_dismissed("p1")
    assert match.current_state.disciplinary.yellows_for("p1") == 1
    assert sum(isinstance(e, PlayerDismissed) for e in match.history) == 1
    assert any(isinstance(e, EventReversed) for e in match.history)


def test_var_rehydrated_contest_matches_live_reversal() -> None:
    match, _ = _started_match()
    match.handle(ScoreGoal(team_index=0, minute=10))
    match.handle(ScoreGoal(team_index=0, minute=20))
    goal = next(e for e in match.history if isinstance(e, GoalScored))

    match.handle(VarOverturnGoal(target_event_id=goal.event_id, reason="var"))

    replayed = ContestFactory.from_events(
        FOOTBALL_SPORT.id,
        list(match.contestants),
        _test_config(),
        match.history,
    )

    assert replayed.current_state.scores == match.current_state.scores
