import pytest

from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.commands import (
    CommitFoul,
    EndPeriod,
    ScoreGoal,
    TakePenaltyKick,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_rule_set import FootballRuleSet
from src.sports.football.contest.state import FootballContestState, MatchPhase


@pytest.fixture
def match_setup() -> tuple[FootballContestState, FootballRuleSet, Team, Team]:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    config = FootballMatchConfig(number_of_halves=2, allow_draw=True)
    state = FootballContestState([home, away], config=config)
    ruleset = FootballRuleSet(config)
    from src.sports.football.contest.events import MatchStarted, PeriodStarted
    from src.sports.football.contest.entities import PeriodKind

    for fact in [MatchStarted(), PeriodStarted(kind=PeriodKind.REGULAR, index=0)]:
        state.apply(fact)
    return state, ruleset, home, away


def test_goal_increments_score(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup

    facts = ruleset.decide(ScoreGoal(team_index=0, minute=10), state)
    for fact in facts:
        state.apply(fact)

    assert state.scores["home"] == 1
    assert state.scores["away"] == 0


def test_own_goal_credits_opponent(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup

    facts = ruleset.decide(ScoreGoal(team_index=0, minute=12, own_goal=True), state)
    for fact in facts:
        state.apply(fact)

    assert state.scores["away"] == 1
    assert state.scores["home"] == 0


def test_second_yellow_triggers_dismissal(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup

    queue = list(
        ruleset.decide(
            CommitFoul(team_index=0, minute=30, card="yellow", offender_id="p9"), state
        )
    )
    while queue:
        fact = queue.pop(0)
        state.apply(fact)
        queue.extend(ruleset.react(fact, state))

    assert state.disciplinary.yellows_for("p9") == 1
    assert not state.disciplinary.is_dismissed("p9")

    queue = list(
        ruleset.decide(
            CommitFoul(team_index=0, minute=30, card="yellow", offender_id="p9"), state
        )
    )
    while queue:
        fact = queue.pop(0)
        state.apply(fact)
        queue.extend(ruleset.react(fact, state))

    assert state.disciplinary.is_dismissed("p9")


def test_rejects_minute_beyond_clock(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup
    assert ruleset.decide(ScoreGoal(team_index=0, minute=999), state) == []


def test_draw_allowed_ends_match_after_regulation(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup

    for _ in range(2):
        queue = list(ruleset.decide(EndPeriod(), state))
        while queue:
            fact = queue.pop(0)
            state.apply(fact)
            queue.extend(ruleset.react(fact, state))

    assert state.is_completed is True
    assert state.was_draw is True
    assert state.winner is None


def test_decisive_regulation_winner(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup

    for fact in ruleset.decide(ScoreGoal(team_index=0, minute=10), state):
        state.apply(fact)

    for _ in range(2):
        queue = list(ruleset.decide(EndPeriod(), state))
        while queue:
            fact = queue.pop(0)
            state.apply(fact)
            queue.extend(ruleset.react(fact, state))

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
    ruleset = FootballRuleSet(config)

    from src.sports.football.contest.events import MatchStarted, PeriodStarted
    from src.sports.football.contest.entities import PeriodKind

    for fact in [MatchStarted(), PeriodStarted(kind=PeriodKind.REGULAR, index=0)]:
        state.apply(fact)

    for _ in range(2):
        queue = list(ruleset.decide(EndPeriod(), state))
        while queue:
            fact = queue.pop(0)
            state.apply(fact)
            queue.extend(ruleset.react(fact, state))

    assert state.phase == MatchPhase.EXTRA_TIME

    for _ in range(2):
        queue = list(ruleset.decide(EndPeriod(), state))
        while queue:
            fact = queue.pop(0)
            state.apply(fact)
            queue.extend(ruleset.react(fact, state))

    assert state.phase == MatchPhase.PENALTIES
    assert not state.is_completed


def test_penalty_shootout_resolves() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    config = FootballMatchConfig(allow_draw=False, penalty_shootout_rounds=3)
    state = FootballContestState([home, away], config=config)
    ruleset = FootballRuleSet(config)
    state.phase = MatchPhase.PENALTIES

    for scored_home, scored_away in [(True, True), (True, False), (True, False)]:
        queue = list(
            ruleset.decide(TakePenaltyKick(team_index=0, scored=scored_home), state)
        )
        while queue:
            fact = queue.pop(0)
            state.apply(fact)
            queue.extend(ruleset.react(fact, state))
        if state.is_completed:
            break
        queue = list(
            ruleset.decide(TakePenaltyKick(team_index=1, scored=scored_away), state)
        )
        while queue:
            fact = queue.pop(0)
            state.apply(fact)
            queue.extend(ruleset.react(fact, state))

    assert state.is_completed is True
    assert state.winner == home
    assert state.decided_by == "penalties"
