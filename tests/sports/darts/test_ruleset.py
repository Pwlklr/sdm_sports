import pytest
from typing import List
from src.core.contest_event import ContestEvent
from src.sports.darts.player import DartPlayer
from src.sports.darts.state import DartsContestState
from src.sports.darts.config import DartsMatchConfig
from src.sports.darts.events import DartThrownEvent, ScoreBustedEvent, LegWonEvent
from src.sports.darts.ruleset import DartsRuleSet

@pytest.fixture
def players() -> List[DartPlayer]:
    return [
        DartPlayer(contestant_id="p1", name="Luke Littler"),
        DartPlayer(contestant_id="p2", name="Luke Humphries")
    ]

@pytest.fixture
def state(players: List[DartPlayer]) -> DartsContestState:
    config = DartsMatchConfig(starting_score=501, legs_to_win_set=3, sets_to_win_match=2)
    return DartsContestState(players=players, config=config)

@pytest.fixture
def ruleset() -> DartsRuleSet:
    return DartsRuleSet()

def test_valid_throw_updates_score(ruleset: DartsRuleSet, state: DartsContestState) -> None:
    event = DartThrownEvent(player_id="p1", sector=20, multiplier=3) 
    resulting_events = ruleset.evaluate(event, state)
    assert state.current_scores["p1"] == 441
    assert len(resulting_events) == 0

def test_bust_rule_score_below_zero(ruleset: DartsRuleSet, state: DartsContestState) -> None:
    state.current_scores["p1"] = 50
    state.turn_start_scores["p1"] = 50  # FIXED: Sync backup score
    
    event = DartThrownEvent(player_id="p1", sector=20, multiplier=3) 
    resulting_events = ruleset.evaluate(event, state)
    
    assert len(resulting_events) == 1
    assert isinstance(resulting_events[0], ScoreBustedEvent)
    assert state.current_scores["p1"] == 50

def test_bust_rule_score_leaves_one(ruleset: DartsRuleSet, state: DartsContestState) -> None:
    state.current_scores["p1"] = 20
    state.turn_start_scores["p1"] = 20  # FIXED: Sync backup score
    
    event = DartThrownEvent(player_id="p1", sector=19, multiplier=1) 
    resulting_events = ruleset.evaluate(event, state)
    
    assert len(resulting_events) == 1
    assert isinstance(resulting_events[0], ScoreBustedEvent)

def test_leg_won_on_double(ruleset: DartsRuleSet, state: DartsContestState) -> None:
    state.current_scores["p1"] = 40
    state.turn_start_scores["p1"] = 40
    
    event = DartThrownEvent(player_id="p1", sector=20, multiplier=2) 
    resulting_events = ruleset.evaluate(event, state)
    
    assert len(resulting_events) == 1
    assert isinstance(resulting_events[0], LegWonEvent)
    assert state.current_scores["p1"] == 501 

def test_bust_rule_reaches_zero_without_double(ruleset: DartsRuleSet, state: DartsContestState) -> None:
    state.current_scores["p1"] = 20
    state.turn_start_scores["p1"] = 20 # FIXED: Sync backup score
    
    event = DartThrownEvent(player_id="p1", sector=20, multiplier=1) 
    resulting_events = ruleset.evaluate(event, state)
    
    assert len(resulting_events) == 1
    assert isinstance(resulting_events[0], ScoreBustedEvent)
    assert state.current_scores["p1"] == 20