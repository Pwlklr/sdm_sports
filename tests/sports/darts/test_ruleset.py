import pytest
from src.core.contestant import IndividualPlayer
from src.sports.darts.state import DartsContestState
from src.sports.darts.ruleset import DartsRuleSet
from src.sports.darts.events import DartThrownEvent
from src.sports.darts.entities import DartThrow

@pytest.fixture
def match_setup() -> tuple[DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer]:
    p1 = IndividualPlayer("Player 1", "p1")
    p2 = IndividualPlayer("Player 2", "p2")
    state = DartsContestState([p1, p2], starting_score=501, sets_to_win=1, legs_to_win_set=1)
    ruleset = DartsRuleSet()
    state.start_new_turn()
    return state, ruleset, p1, p2

def test_normal_throw_progression(match_setup: tuple[DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer]) -> None:
    state, ruleset, p1, p2 = match_setup
    
    # P1 throws a Treble 20 (60 points)
    throw = DartThrow(20, 3)
    event = DartThrownEvent(p1, throw)
    
    ruleset.evaluate(event, state)
    
    assert state.scores["p1"] == 441
    assert state.current_player == p1 # Still P1's turn (1 dart thrown)

def test_bust_rule_reverts_score(match_setup: tuple[DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer]) -> None:
    state, ruleset, p1, p2 = match_setup
    state.scores["p1"] = 50
    state.turn_starting_score = 50
    
    # P1 hits Treble 20 (60 points) -> BUST
    throw = DartThrow(20, 3)
    event = DartThrownEvent(p1, throw)
    
    ruleset.evaluate(event, state)
    
    assert state.scores["p1"] == 50 # Score reverted
    assert state.current_player == p2 # Turn passed to P2 automatically

def test_bust_on_single_one_remaining(match_setup: tuple[DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer]) -> None:
    state, ruleset, p1, p2 = match_setup
    state.scores["p1"] = 20
    state.turn_starting_score = 20
    
    # P1 hits Single 19 (1 point remaining) -> BUST (cannot finish on 1)
    throw = DartThrow(19, 1)
    event = DartThrownEvent(p1, throw)
    
    ruleset.evaluate(event, state)
    
    assert state.scores["p1"] == 20 # Score reverted

def test_win_leg_double_out(match_setup: tuple[DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer]) -> None:
    state, ruleset, p1, p2 = match_setup
    state.scores["p1"] = 40
    state.turn_starting_score = 40
    
    # P1 hits Double 20 (40 points) -> WIN
    throw = DartThrow(20, 2)
    event = DartThrownEvent(p1, throw)
    
    ruleset.evaluate(event, state)
    
    assert state.is_completed is True
    assert state.sets_won["p1"] == 1

def test_bust_on_zero_without_double(match_setup: tuple[DartsContestState, DartsRuleSet, IndividualPlayer, IndividualPlayer]) -> None:
    state, ruleset, p1, p2 = match_setup
    state.scores["p1"] = 20
    state.turn_starting_score = 20
    
    # P1 hits Single 20 (0 points, but not a double) -> BUST
    throw = DartThrow(20, 1)
    event = DartThrownEvent(p1, throw)
    
    ruleset.evaluate(event, state)
    
    assert state.scores["p1"] == 20 # Reverted
    assert state.current_player == p2