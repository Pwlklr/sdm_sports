import pytest
from src.sports.darts.player import DartPlayer
from src.sports.darts.state import DartsContestState
from src.sports.darts.config import DartsMatchConfig

@pytest.fixture
def players() -> list[DartPlayer]:
    return [
        DartPlayer(contestant_id="p1", name="Luke Littler"),
        DartPlayer(contestant_id="p2", name="Luke Humphries")
    ]

def test_darts_state_initialization(players: list[DartPlayer]) -> None:
    config = DartsMatchConfig(starting_score=501)
    state = DartsContestState(players=players, config=config)
    
    assert state.current_scores["p1"] == 501
    assert state.current_scores["p2"] == 501
    assert state.legs_won["p1"] == 0
    assert state.active_player == players[0]

def test_darts_state_switch_turn(players: list[DartPlayer]) -> None:
    config = DartsMatchConfig(starting_score=501)
    state = DartsContestState(players=players, config=config)
    
    assert state.active_player.contestant_id == "p1"
    state.switch_turn()
    assert state.active_player.contestant_id == "p2"
    state.switch_turn()
    assert state.active_player.contestant_id == "p1"

def test_update_score(players: list[DartPlayer]) -> None:
    config = DartsMatchConfig(starting_score=501)
    state = DartsContestState(players=players, config=config)
    
    state.update_score("p1", 60)
    assert state.current_scores["p1"] == 441