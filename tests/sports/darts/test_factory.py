"""Darts ContestFactory — create and rehydrate contests."""

import src.sports.darts.register_contest  # noqa: F401
import src.sports.darts.register_tournament  # noqa: F401

from src.core.contest import ContestFactory
from src.core.contestant.models import IndividualPlayer
from src.core.tournament import Tournament
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.commands import StartMatch, ThrowDart
from src.sports.darts.descriptor import DARTS_SPORT


def _players() -> tuple[IndividualPlayer, IndividualPlayer]:
    return IndividualPlayer("P1", "p1"), IndividualPlayer("P2", "p2")


def test_create_contest_uses_provided_config() -> None:
    p1, p2 = _players()
    match = ContestFactory.create(
        "darts", [p1, p2], DartsMatchConfig(starting_score=301)
    )
    assert match.current_state.config.starting_score == 301


def test_from_events_rehydrates_to_same_state() -> None:
    p1, p2 = _players()
    config = DartsMatchConfig(starting_score=301)
    live = ContestFactory.create("darts", [p1, p2], config)
    live.handle(StartMatch())
    live.handle(ThrowDart(sector=20, multiplier=3))

    rehydrated = ContestFactory.from_events("darts", [p1, p2], config, live.history)

    assert (
        rehydrated.current_state.config.starting_score
        == live.current_state.config.starting_score
    )
    assert rehydrated.current_state.scores == live.current_state.scores
    assert len(rehydrated.history) == len(live.history)


def test_create_rejects_wrong_contestant_kind() -> None:
    from src.core.contestant.models import Team
    import pytest

    home = Team("Home", "home")
    away = Team("Away", "away")
    with pytest.raises(ValueError, match="IndividualPlayer"):
        ContestFactory.create("darts", [home, away], DartsMatchConfig())


def test_darts_tournament_auto_registers_individual_squad() -> None:
    player = IndividualPlayer("Luke", "luke")
    tournament = Tournament.from_blueprint(
        "Open",
        DARTS_SPORT.id,
        "league",
        match_config=DartsMatchConfig(),
    )
    tournament.open_registration()
    tournament.register_contestant(player)
    assert tournament.state.squads[player.id] == (player.id,)
