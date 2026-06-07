import pytest
from src.sports.darts.ruleset import DartsRuleSet
from src.sports.darts.state import DartsContestState
from src.sports.darts.config import DartsMatchConfig
from src.sports.darts.events import DartThrownEvent, SetWon, MatchEnded, OcheFaultEvent
from src.sports.darts.player import DartPlayer
from src.sports.darts.entities import DartThrow

@pytest.fixture
def players() -> list[DartPlayer]:
    return [DartPlayer("p1", "A"), DartPlayer("p2", "B")]

def test_ruleset_match_completed(players: list[DartPlayer]) -> None:
    state = DartsContestState(players, DartsMatchConfig())
    state.is_completed = True
    events = DartsRuleSet().evaluate(DartThrownEvent(players[0], DartThrow(20, 1)), state)
    assert len(events) == 0

def test_three_darts_switches_turn(players: list[DartPlayer]) -> None:
    state = DartsContestState(players, DartsMatchConfig())
    rs = DartsRuleSet()
    rs.evaluate(DartThrownEvent(players[0], DartThrow(20, 1)), state)
    rs.evaluate(DartThrownEvent(players[0], DartThrow(20, 1)), state)
    assert state.current_player.id == "p1"
    rs.evaluate(DartThrownEvent(players[0], DartThrow(20, 1)), state)
    assert state.current_player.id == "p2"

def test_set_and_match_won(players: list[DartPlayer]) -> None:
    config = DartsMatchConfig(starting_score=2, legs_to_win_set=1, sets_to_win_match=1, in_multiplier=1, out_multiplier=2)
    state = DartsContestState(players, config)
    rs = DartsRuleSet()
    
    events = rs.evaluate(DartThrownEvent(players[0], DartThrow(1, 2)), state)
    event_types = [type(e) for e in events]
    
    assert SetWon in event_types
    assert MatchEnded in event_types
    assert state.is_completed is True

def test_set_won_but_not_match(players: list[DartPlayer]) -> None:
    config = DartsMatchConfig(starting_score=2, legs_to_win_set=1, sets_to_win_match=2, in_multiplier=1, out_multiplier=2)
    state = DartsContestState(players, config)
    rs = DartsRuleSet()
    
    events = rs.evaluate(DartThrownEvent(players[0], DartThrow(1, 2)), state)
    event_types = [type(e) for e in events]
    
    assert SetWon in event_types
    assert MatchEnded not in event_types
    assert state.is_completed is False
    assert state.sets_won["p1"] == 1

def test_oche_fault_scores_zero_but_consumes_dart(players: list[DartPlayer]) -> None:
    """Verifies the Penalty Pipeline intercepts and zeroes out the throw."""
    state = DartsContestState(players, DartsMatchConfig(starting_score=501))
    rs = DartsRuleSet()
    rs.evaluate(OcheFaultEvent(players[0]), state)
    
    assert state.scores["p1"] == 501
    assert state.current_player == players[0]
    assert state.current_turn is not None
    assert len(state.current_turn.throws) == 1
    assert state.current_turn.throws[0].points == 0

def test_missed_dart_scores_zero(players: list[DartPlayer]) -> None:
    """Verifies that throwing a 0 naturally registers a miss."""
    state = DartsContestState(players, DartsMatchConfig(starting_score=501))
    rs = DartsRuleSet()
    rs.evaluate(DartThrownEvent(players[0], DartThrow(0, 1)), state)
    
    assert state.scores["p1"] == 501
    assert state.current_turn is not None
    assert len(state.current_turn.throws) == 1
    assert state.current_turn.throws[0].points == 0