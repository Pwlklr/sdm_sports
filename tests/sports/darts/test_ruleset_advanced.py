import pytest
from src.sports.darts.ruleset import DartsRuleSet
from src.sports.darts.state import DartsContestState
from src.sports.darts.config import DartsMatchConfig
from src.sports.darts.events import DartThrownEvent, SetWonEvent, MatchEndedEvent
from src.sports.darts.player import DartPlayer

@pytest.fixture
def players():
    return [DartPlayer("p1", "A"), DartPlayer("p2", "B")]

def test_ruleset_match_completed(players):
    state = DartsContestState(players, DartsMatchConfig())
    state.is_completed = True
    # If match is completed, evaluating throws should do nothing
    events = DartsRuleSet().evaluate(DartThrownEvent("p1", 20, 1), state)
    assert len(events) == 0

def test_ruleset_invalid_player(players):
    state = DartsContestState(players, DartsMatchConfig())
    # Sending an event for a player not in the match
    events = DartsRuleSet().evaluate(DartThrownEvent("INVALID", 20, 1), state)
    assert len(events) == 0

def test_three_darts_switches_turn(players):
    state = DartsContestState(players, DartsMatchConfig())
    rs = DartsRuleSet()
    rs.evaluate(DartThrownEvent("p1", 20, 1), state)
    rs.evaluate(DartThrownEvent("p1", 20, 1), state)
    # Turn should still be p1 after 2 darts
    assert state.active_player.contestant_id == "p1"
    rs.evaluate(DartThrownEvent("p1", 20, 1), state)
    # Turn should auto-switch to p2 after 3 darts
    assert state.active_player.contestant_id == "p2"

def test_set_and_match_won(players):
    # Fast match: 1 leg to win set, 1 set to win match. Start score at 2.
    config = DartsMatchConfig(starting_score=2, legs_to_win_set=1, sets_to_win_match=1)
    state = DartsContestState(players, config)
    rs = DartsRuleSet()
    
    # Hit Double 1 (2 points) -> wins leg, wins set, wins match
    events = rs.evaluate(DartThrownEvent("p1", 1, 2), state)
    event_types = [type(e) for e in events]
    
    assert SetWonEvent in event_types
    assert MatchEndedEvent in event_types
    assert state.is_completed is True

def test_set_won_but_not_match(players):
    # 1 leg to win set, 2 sets to win match. Start score at 2.
    config = DartsMatchConfig(starting_score=2, legs_to_win_set=1, sets_to_win_match=2)
    state = DartsContestState(players, config)
    rs = DartsRuleSet()
    
    events = rs.evaluate(DartThrownEvent("p1", 1, 2), state)
    event_types = [type(e) for e in events]
    
    assert SetWonEvent in event_types
    assert MatchEndedEvent not in event_types
    assert state.is_completed is False
    assert state.sets_won["p1"] == 1