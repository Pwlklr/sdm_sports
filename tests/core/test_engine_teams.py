from src.core.system.sports_system_engine import SportsSystemEngine


def test_create_team_with_roster_keeps_players_off_global_individuals_list() -> None:
    engine = SportsSystemEngine()
    team = engine.create_team_with_roster("Arsenal FC", ["Saka", "Odegaard"])

    assert len(engine.list_teams()) == 1
    assert engine.list_teams()[0].name == "Arsenal FC"
    assert [p.name for p in team.roster] == ["Saka", "Odegaard"]
    assert engine.list_individual_players() == []


def test_list_individual_players_excludes_teams() -> None:
    engine = SportsSystemEngine()
    engine.create_individual_player("Phil Taylor")
    engine.create_team("Empty FC")

    assert len(engine.list_individual_players()) == 1
    assert engine.list_teams()[0].name == "Empty FC"
