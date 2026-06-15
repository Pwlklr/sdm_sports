import pytest

from dataclasses import replace

from src.core.shared.command_rejected import CommandRejected
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.commands import (
    CommitFoul,
    EndPeriod,
    ScoreGoal,
    TakePenaltyKick,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_rule_set import FootballRuleSet
from src.sports.football.contest.state import FootballContestState, MatchPhase, create_football_contest_state


def _process(state: FootballContestState, ruleset: FootballRuleSet, command) -> FootballContestState:
    queue = list(ruleset.decide(command, state))
    while queue:
        fact = queue.pop(0)
        state = state.apply(fact)
        queue.extend(ruleset.react(fact, state))
    return state


def _apply_facts(state: FootballContestState, facts) -> FootballContestState:
    for fact in facts:
        state = state.apply(fact)
    return state


@pytest.fixture
def match_setup() -> tuple[FootballContestState, FootballRuleSet, Team, Team]:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    config = FootballMatchConfig(number_of_halves=2, allow_draw=True)
    state = create_football_contest_state([home, away], config=config)
    ruleset = FootballRuleSet(config)
    from src.sports.football.contest.events import MatchStarted, PeriodStarted
    from src.sports.football.contest.entities import PeriodKind

    state = _apply_facts(
        state,
        [MatchStarted(), PeriodStarted(kind=PeriodKind.REGULAR, index=0)],
    )
    return state, ruleset, home, away


def test_goal_increments_score(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup
    state = _apply_facts(
        state, ruleset.decide(ScoreGoal(team_index=0, minute=10), state)
    )
    assert state.scores["home"] == 1
    assert state.scores["away"] == 0


def test_own_goal_credits_opponent(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup
    state = _apply_facts(
        state, ruleset.decide(ScoreGoal(team_index=0, minute=12, own_goal=True), state)
    )
    assert state.scores["away"] == 1
    assert state.scores["home"] == 0


def test_second_yellow_triggers_dismissal(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup
    state = _process(
        state,
        ruleset,
        CommitFoul(team_index=0, minute=30, card="yellow", offender_id="p9"),
    )
    assert state.disciplinary.yellows_for("p9") == 1
    assert not state.disciplinary.is_dismissed("p9")

    state = _process(
        state,
        ruleset,
        CommitFoul(team_index=0, minute=30, card="yellow", offender_id="p9"),
    )
    assert state.disciplinary.is_dismissed("p9")


def test_rejects_minute_beyond_clock(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup
    with pytest.raises(CommandRejected):
        ruleset.decide(ScoreGoal(team_index=0, minute=999), state)


def test_draw_allowed_ends_match_after_regulation(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup
    for _ in range(2):
        state = _process(state, ruleset, EndPeriod())

    assert state.is_finished is True
    assert state.was_draw is True
    assert state.winner is None


def test_decisive_regulation_winner(
    match_setup: tuple[FootballContestState, FootballRuleSet, Team, Team],
) -> None:
    state, ruleset, home, away = match_setup
    state = _apply_facts(
        state, ruleset.decide(ScoreGoal(team_index=0, minute=10), state)
    )
    for _ in range(2):
        state = _process(state, ruleset, EndPeriod())

    assert state.is_finished is True
    assert state.winner == home
    assert state.decided_by == "regulation"


def test_knockout_draw_goes_to_extra_time_then_penalties() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    config = FootballMatchConfig(
        number_of_halves=2, allow_draw=False, extra_time_halves=2
    )
    state = create_football_contest_state([home, away], config=config)
    ruleset = FootballRuleSet(config)

    from src.sports.football.contest.events import MatchStarted, PeriodStarted
    from src.sports.football.contest.entities import PeriodKind

    state = _apply_facts(
        state,
        [MatchStarted(), PeriodStarted(kind=PeriodKind.REGULAR, index=0)],
    )

    for _ in range(2):
        state = _process(state, ruleset, EndPeriod())

    assert state.phase == MatchPhase.EXTRA_TIME

    for _ in range(2):
        state = _process(state, ruleset, EndPeriod())

    assert state.phase == MatchPhase.PENALTIES
    assert not state.is_finished


def test_penalty_shootout_resolves() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    config = FootballMatchConfig(allow_draw=False, penalty_shootout_rounds=3)
    state = create_football_contest_state([home, away], config=config)
    ruleset = FootballRuleSet(config)
    state = replace(state, phase=MatchPhase.PENALTIES)

    for scored_home, scored_away in [(True, True), (True, False), (True, False)]:
        state = _process(
            state, ruleset, TakePenaltyKick(team_index=0, scored=scored_home)
        )
        if state.is_finished:
            break
        state = _process(
            state, ruleset, TakePenaltyKick(team_index=1, scored=scored_away)
        )

    assert state.is_finished is True
    assert state.winner == home
    assert state.decided_by == "penalties"
