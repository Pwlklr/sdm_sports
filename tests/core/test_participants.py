from __future__ import annotations


from src.core.contestant import Contestant
from src.core.team import Team


def test_team_manages_contestants():
    player1 = Contestant(contestant_id="P1", name="Player One")
    player2 = Contestant(contestant_id="P2", name="Player Two")
    team = Team(team_id="T1", name="Team A")

    team.add_member(player1)
    team.add_member(player2)

    assert team.team_id == "T1"
    assert len(team.members) == 2
    assert player1 in team.members
