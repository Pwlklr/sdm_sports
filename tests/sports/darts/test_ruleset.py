import pytest

from src.core.contestant import IndividualPlayer
from src.sports.darts.contest.commands import ThrowDart
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.events import MatchStarted
from src.sports.darts.contest.darts_rule_set import DartsRuleSet
from src.sports.darts.contest.darts_contest_state import DartsContestState


@pytest.fixture
def match_setup() -> (
    tuple[DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer]
):
    p1 = IndividualPlayer("Player 1", "p1")
    p2 = IndividualPlayer("Player 2", "p2")
    config = DartsMatchConfig(
        starting_score=501, sets_to_win_match=1, legs_to_win_set=1
    )
    state = DartsContestState([p1, p2], config=config)
    ruleset = DartsRuleSet(config)
    state.apply(MatchStarted())
    return state, ruleset, p1, p2


def _handle_throw(
    state: DartsContestState, ruleset: DartsRuleSet, sector: int, multiplier: int
) -> None:
    queue = list(ruleset.decide(ThrowDart(sector=sector, multiplier=multiplier), state))
    while queue:
        fact = queue.pop(0)
        state.apply(fact)
        queue.extend(ruleset.react(fact, state))


def test_normal_throw_progression(
    match_setup: tuple[
        DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer
    ],
) -> None:
    state, ruleset, p1, p2 = match_setup
    _handle_throw(state, ruleset, 20, 3)
    assert state.scores["p1"] == 441
    assert state.current_player == p1


def test_bust_rule_reverts_score(
    match_setup: tuple[
        DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer
    ],
) -> None:
    state, ruleset, p1, p2 = match_setup
    state.scores["p1"] = 50
    state.turn_starting_score = 50
    _handle_throw(state, ruleset, 20, 3)
    assert state.scores["p1"] == 50
    assert state.current_player == p2


def test_bust_on_single_one_remaining(
    match_setup: tuple[
        DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer
    ],
) -> None:
    state, ruleset, p1, p2 = match_setup
    state.scores["p1"] = 20
    state.turn_starting_score = 20
    _handle_throw(state, ruleset, 19, 1)
    assert state.scores["p1"] == 20


def test_win_leg_double_out(
    match_setup: tuple[
        DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer
    ],
) -> None:
    state, ruleset, p1, p2 = match_setup
    state.scores["p1"] = 40
    state.turn_starting_score = 40
    _handle_throw(state, ruleset, 20, 2)
    assert state.is_completed is True
    assert state.sets_won["p1"] == 1


def test_bust_on_zero_without_double(
    match_setup: tuple[
        DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer
    ],
) -> None:
    state, ruleset, p1, p2 = match_setup
    state.scores["p1"] = 20
    state.turn_starting_score = 20
    _handle_throw(state, ruleset, 20, 1)
    assert state.scores["p1"] == 20
    assert state.current_player == p2


def _double_in_setup() -> tuple[DartsContestState, DartsRuleSet]:
    config = DartsMatchConfig(
        starting_score=501,
        sets_to_win_match=1,
        legs_to_win_set=1,
        in_multiplier=2,
        out_multiplier=2,
    )
    state = DartsContestState(
        [IndividualPlayer("Player 1", "p1"), IndividualPlayer("Player 2", "p2")],
        config=config,
    )
    state.apply(MatchStarted())
    return state, DartsRuleSet(config)


def test_double_in_opening_dart_without_double_scores_zero() -> None:
    state, ruleset = _double_in_setup()
    _handle_throw(state, ruleset, 20, 1)
    assert state.scores["p1"] == 501


def test_double_in_opening_dart_with_double_scores() -> None:
    state, ruleset = _double_in_setup()
    _handle_throw(state, ruleset, 20, 2)
    assert state.scores["p1"] == 461


def test_double_in_only_first_scoring_dart_is_gated() -> None:
    state, ruleset = _double_in_setup()
    _handle_throw(state, ruleset, 20, 2)
    _handle_throw(state, ruleset, 20, 1)
    assert state.scores["p1"] == 441
