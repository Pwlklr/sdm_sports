import pytest

from src.core.contest import Contest
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.commands import CommitFoul, ScoreGoal, StartMatch
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_rule_set import FootballRuleSet
from src.sports.football.contest.state import FootballContestState
from src.sports.football.football_sport_factory import FootballSportFactory


def _started_contest() -> Contest:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    contest = FootballSportFactory().create_contest(
        [home, away], FootballMatchConfig()
    )
    contest.handle(StartMatch())
    return contest


def _handle_foul(contest: Contest, **kwargs: object) -> None:
    contest.handle(CommitFoul(**kwargs))  # type: ignore[arg-type]


def test_two_yellows_lead_to_dismissal_via_contest() -> None:
    contest = _started_contest()
    state = contest.current_state

    _handle_foul(
        contest,
        team_index=0,
        minute=10,
        card="yellow",
        offender_id="p9",
    )
    assert state.disciplinary.yellows_for("p9") == 1
    assert not state.disciplinary.is_dismissed("p9")

    _handle_foul(
        contest,
        team_index=0,
        minute=30,
        card="yellow",
        offender_id="p9",
    )
    assert state.disciplinary.is_dismissed("p9")


def test_dismissed_player_cannot_receive_more_cards() -> None:
    contest = _started_contest()
    state = contest.current_state

    _handle_foul(
        contest,
        team_index=0,
        minute=10,
        card="red",
        offender_id="p9",
    )
    assert state.disciplinary.is_dismissed("p9")

    _handle_foul(
        contest,
        team_index=0,
        minute=20,
        card="yellow",
        offender_id="p9",
    )
    assert state.disciplinary.yellows_for("p9") == 0

    _handle_foul(
        contest,
        team_index=0,
        minute=25,
        card="red",
        offender_id="p9",
    )
    assert state.disciplinary.yellows_for("p9") == 0


def test_direct_red_dismisses_without_yellows() -> None:
    contest = _started_contest()
    state = contest.current_state

    _handle_foul(
        contest,
        team_index=0,
        minute=33,
        card="red",
        offender_id="p9",
    )
    assert state.disciplinary.is_dismissed("p9")
    assert state.disciplinary.yellows_for("p9") == 0


def test_foul_without_card_does_not_change_discipline() -> None:
    contest = _started_contest()
    state = contest.current_state

    _handle_foul(
        contest,
        team_index=0,
        minute=12,
        card=None,
        offender_id="p9",
        reason="Late tackle",
    )
    assert state.disciplinary.yellows_for("p9") == 0
    assert not state.disciplinary.is_dismissed("p9")


def test_score_goal_records_scorer_and_minute() -> None:
    contest = _started_contest()
    state = contest.current_state

    contest.handle(
        ScoreGoal(team_index=0, minute=23, scorer_id="p9", penalty=True)
    )
    period = state.current_period
    assert period is not None
    assert len(period.goals) == 1
    goal = period.goals[0]
    assert goal.minute == 23
    assert goal.scorer_id == "p9"
    assert goal.penalty is True


def test_ruleset_rejects_card_for_dismissed_player() -> None:
    state = FootballContestState(
        [Team("H", "h"), Team("A", "a")],
        config=FootballMatchConfig(),
    )
    team = state.teams[0]
    assert isinstance(team, Team)
    team.add_player(IndividualPlayer("X", "x"))
    state.disciplinary.dismiss("x")
    ruleset = FootballRuleSet(FootballMatchConfig())

    events = ruleset.decide(
        CommitFoul(team_index=0, minute=10, card="yellow", offender_id="x"),
        state,
    )
    assert events == []
