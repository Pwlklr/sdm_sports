from src.sports.darts.contestant.dart_player import DartPlayer

def test_dart_player_str_representation() -> None:
    player = DartPlayer(contestant_id="player_1", name="Luke Littler")
    assert str(player) == "Luke Littler"
    assert player.id == "player_1"  # Corrected from contestant_id to id