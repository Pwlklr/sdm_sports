import pytest

from dataclasses import replace

from src.core.contest import Contest
from src.core.shared.command_rejected import CommandRejected
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.commands import CommitFoul, ScoreGoal, StartMatch, SubmitLineup
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_rule_set import FootballRuleSet
from src.sports.football.contest.football_contest_state import (
    create_football_contest_state,
)
from src.core.contest import ContestFactory
from src.sports.football.descriptor import FOOTBALL_SPORT


def _started_contest() -> Contest:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    contest = ContestFactory.create(
        FOOTBALL_SPORT.id,
        [home, away],
        FootballMatchConfig(players_on_pitch=1, min_players_on_pitch=1),
    )
    contest.handle(StartMatch())
    contest.handle(
        SubmitLineup(team_index=0, starting=("p9",), bench=()),
    )
    contest.handle(
        SubmitLineup(team_index=1, starting=("other",), bench=()),
    )
    return contest


def _handle_foul(contest: Contest, **kwargs: object) -> None:
    contest.handle(CommitFoul(**kwargs))  # type: ignore[arg-type]


def test_two_yellows_lead_to_dismissal_via_contest() -> None:
    contest = _started_contest()

    _handle_foul(
        contest,
        team_index=0,
        minute=10,
        card="yellow",
        offender_id="p9",
    )
    state = contest.current_state
    assert state.disciplinary.yellows_for("p9") == 1
    assert not state.disciplinary.is_dismissed("p9")

    _handle_foul(
        contest,
        team_index=0,
        minute=30,
        card="yellow",
        offender_id="p9",
    )
    state = contest.current_state
    assert state.disciplinary.is_dismissed("p9")


def test_dismissed_player_cannot_receive_more_cards() -> None:
    contest = _started_contest()

    _handle_foul(
        contest,
        team_index=0,
        minute=10,
        card="red",
        offender_id="p9",
    )
    state = contest.current_state
    assert state.disciplinary.is_dismissed("p9")

    with pytest.raises(CommandRejected):
        _handle_foul(
            contest,
            team_index=0,
            minute=20,
            card="yellow",
            offender_id="p9",
        )
    assert contest.current_state.disciplinary.yellows_for("p9") == 0

    with pytest.raises(CommandRejected):
        _handle_foul(
            contest,
            team_index=0,
            minute=25,
            card="red",
            offender_id="p9",
        )
    assert contest.current_state.disciplinary.yellows_for("p9") == 0


def test_direct_red_dismisses_without_yellows() -> None:
    contest = _started_contest()

    _handle_foul(
        contest,
        team_index=0,
        minute=33,
        card="red",
        offender_id="p9",
    )
    state = contest.current_state
    assert state.disciplinary.is_dismissed("p9")
    assert state.disciplinary.yellows_for("p9") == 0


def test_foul_without_card_does_not_change_discipline() -> None:
    contest = _started_contest()

    _handle_foul(
        contest,
        team_index=0,
        minute=12,
        card=None,
        offender_id="p9",
        reason="Late tackle",
    )
    state = contest.current_state
    assert state.disciplinary.yellows_for("p9") == 0
    assert not state.disciplinary.is_dismissed("p9")


def test_score_goal_records_scorer_and_minute() -> None:
    contest = _started_contest()

    contest.handle(ScoreGoal(team_index=0, minute=23, scorer_id="p9", penalty=True))
    state = contest.current_state
    period = state.current_period
    assert period is not None
    assert len(period.goals) == 1
    goal = period.goals[0]
    assert goal.minute == 23
    assert goal.scorer_id == "p9"
    assert goal.penalty is True


def test_ruleset_rejects_card_for_dismissed_player() -> None:
    home = Team("H", "h")
    away = Team("A", "a")
    home.add_player(IndividualPlayer("X", "x"))
    state = create_football_contest_state([home, away], FootballMatchConfig())
    state = replace(state, disciplinary=state.disciplinary.with_dismissal("x"))
    ruleset = FootballRuleSet(FootballMatchConfig())

    with pytest.raises(CommandRejected):
        ruleset.decide(
            CommitFoul(team_index=0, minute=10, card="yellow", offender_id="x"),
            state,
        )
