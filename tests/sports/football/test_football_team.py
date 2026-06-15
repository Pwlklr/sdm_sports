from src.sports.football.contestant.football_team import FootballTeam

def test_football_team_str_representation() -> None:
    """Verifies Football team representation relies correctly on the name."""
    team = FootballTeam(contestant_id="team_1", name="Real Madrid")
    
    assert str(team) == "Real Madrid"
    assert team.id == "team_1"