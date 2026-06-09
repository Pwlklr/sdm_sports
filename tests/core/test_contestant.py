from src.core.contestant import IndividualPlayer, Team


def test_individual_player_creation() -> None:
    player = IndividualPlayer("Phil Taylor", contestant_id="p1")
    assert player.name == "Phil Taylor"
    assert player.id == "p1"
    assert player.display_name == "Phil Taylor"


def test_contestant_equality() -> None:
    player1 = IndividualPlayer("Player A", contestant_id="123")
    player2 = IndividualPlayer("Player A", contestant_id="123")
    player3 = IndividualPlayer("Player B", contestant_id="999")

    assert player1 == player2
    assert player1 != player3


def test_metadata_storage() -> None:
    metadata = {"nickname": "The Power", "nationality": "ENG"}
    p1 = IndividualPlayer("Phil Taylor", metadata=metadata)
    assert p1.metadata["nickname"] == "The Power"
    assert p1.metadata["nationality"] == "ENG"


def test_team_roster_management() -> None:
    team = Team("FC Python", contestant_id="t1")
    player1 = IndividualPlayer("Alice")
    player2 = IndividualPlayer("Bob")

    # Add players
    team.add_player(player1)
    team.add_player(player2)
    assert len(team.roster) == 2

    # Prevent duplicate additions
    team.add_player(player1)
    assert len(team.roster) == 2

    # Remove player
    team.remove_player(player1)
    assert len(team.roster) == 1
    assert player1 not in team.roster
    assert player2 in team.roster

    # Display name reflects roster size
    assert team.display_name == "FC Python (1 players)"


def test_team_roster_encapsulation() -> None:
    team = Team("Red Team")
    player = IndividualPlayer("Charlie")
    team.add_player(player)

    # Modifying the returned roster should not affect the team's internal roster
    roster_copy = team.roster
    roster_copy.clear()

    assert len(team.roster) == 1
