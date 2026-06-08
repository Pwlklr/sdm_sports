import pytest

from src.core.contestant import Team
from src.sports.football.config import FootballMatchConfig
from src.sports.football.events import (
    EndPeriodEvent,
    FoulCommittedEvent,
    GoalScoredEvent,
    PenaltyKickEvent,
)
from src.sports.football.ruleset import FootballRuleSet
from src.sports.football.state import FootballContestState, MatchPhase


@pytest.fixture
def match_setup() -> tuple[FootballContestState, FootballRuleSet, Team, Team]:
    home = Team("Home", "home")
    away = Team("Away", "away")
    config = FootballMatchConfig(number_of_halves=2, allow_draw=True)
    state = FootballContestState([home, away], config=config)
    ruleset = FootballRuleSet()
    return state, ruleset, home, away


def test_goal_increments_score(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup

    ruleset.evaluate(GoalScoredEvent(home, minute=10), state)

    assert state.scores["home"] == 1
    assert state.scores["away"] == 0
    assert state.current_period is not None


def test_own_goal_credits_opponent(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup

    ruleset.evaluate(GoalScoredEvent(home, own_goal=True), state)

    assert state.scores["away"] == 1
    assert state.scores["home"] == 0


def test_second_yellow_triggers_dismissal(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup

    ruleset.evaluate(FoulCommittedEvent(home, card="yellow", offender_id="p9"), state)
    assert not state.disciplinary.is_dismissed("p9")

    ruleset.evaluate(FoulCommittedEvent(home, card="yellow", offender_id="p9"), state)
    assert state.disciplinary.is_dismissed("p9")


def test_straight_red_dismisses(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup

    ruleset.evaluate(FoulCommittedEvent(home, card="red", offender_id="p4"), state)

    assert state.disciplinary.is_dismissed("p4")


def test_draw_allowed_ends_match_after_regulation(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup

    ruleset.evaluate(EndPeriodEvent(), state)
    assert not state.is_completed
    ruleset.evaluate(EndPeriodEvent(), state)

    assert state.is_completed is True
    assert state.was_draw is True
    assert state.winner is None


def test_decisive_regulation_winner(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup

    ruleset.evaluate(GoalScoredEvent(home), state)
    ruleset.evaluate(EndPeriodEvent(), state)
    ruleset.evaluate(EndPeriodEvent(), state)

    assert state.is_completed is True
    assert state.winner == home
    assert state.decided_by == "regulation"


def test_knockout_draw_goes_to_extra_time_then_penalties() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    config = FootballMatchConfig(
        number_of_halves=2, allow_draw=False, extra_time_halves=2
    )
    state = FootballContestState([home, away], config=config)
    ruleset = FootballRuleSet()

    # Two scoreless regular halves -> extra time
    ruleset.evaluate(EndPeriodEvent(), state)
    ruleset.evaluate(EndPeriodEvent(), state)
    assert state.phase == MatchPhase.EXTRA_TIME

    # Two scoreless extra halves -> penalties
    ruleset.evaluate(EndPeriodEvent(), state)
    ruleset.evaluate(EndPeriodEvent(), state)
    assert state.phase == MatchPhase.PENALTIES
    assert not state.is_completed


def test_penalty_shootout_resolves() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    config = FootballMatchConfig(allow_draw=False, penalty_shootout_rounds=3)
    state = FootballContestState([home, away], config=config)
    ruleset = FootballRuleSet()
    state.phase = MatchPhase.PENALTIES

    # Home scores all three, away scores once -> home clinches
    for scored_home, scored_away in [(True, True), (True, False), (True, False)]:
        ruleset.evaluate(PenaltyKickEvent(home, scored_home), state)
        if not state.is_completed:
            ruleset.evaluate(PenaltyKickEvent(away, scored_away), state)

    assert state.is_completed is True
    assert state.winner == home
    assert state.decided_by == "penalties"


def test_goals_ignored_after_completion(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup
    state.is_completed = True

    ruleset.evaluate(GoalScoredEvent(home), state)

    assert state.scores["home"] == 0
