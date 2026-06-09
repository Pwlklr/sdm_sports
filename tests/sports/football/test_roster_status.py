from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.roster_status import (
    format_player_card_suffix,
    format_squad_lines_from_state,
    roster_status_for_match,
    roster_status_for_team,
)
from src.sports.football.contest.state import FootballContestState


def _state() -> FootballContestState:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("Saka", "saka"))
    home.add_player(IndividualPlayer("Ode", "ode"))
    state = FootballContestState([home, away], config=FootballMatchConfig())
    state.disciplinary.record_yellow("saka")
    state.disciplinary.dismiss("ode")
    return state


def test_roster_status_merges_team_and_disciplinary() -> None:
    state = _state()
    home = state.teams[0]
    assert isinstance(home, Team)

    rows = roster_status_for_team(state, home)
    assert rows[0].name == "Saka"
    assert rows[0].yellow_cards == 1
    assert not rows[0].dismissed
    assert rows[1].dismissed is True


def test_roster_status_for_match_by_team_id() -> None:
    state = _state()
    home = state.teams[0]
    assert isinstance(home, Team)
    by_team = roster_status_for_match(state)
    assert home.id in by_team
    assert len(by_team[home.id]) == 2


def test_state_roster_status_accessor() -> None:
    state = _state()
    home = state.teams[0]
    assert isinstance(home, Team)
    assert state.roster_status(home)[1].dismissed


def test_format_player_card_suffix() -> None:
    state = _state()
    home = state.teams[0]
    assert isinstance(home, Team)
    rows = roster_status_for_team(state, home)
    assert "🟨" in format_player_card_suffix(rows[0])
    assert "🟥" in format_player_card_suffix(rows[1])


def test_format_squad_lines_from_state_shows_cards() -> None:
    state = _state()
    home = state.teams[0]
    assert isinstance(home, Team)
    lines = format_squad_lines_from_state(state, home)
    assert any("🟨" in line for line in lines)
    assert any("🟥" in line for line in lines)
