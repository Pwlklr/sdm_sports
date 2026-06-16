"""Tests for WalkoverMixin: in-progress guard + two-path routing."""

import pytest

from src.core.shared import CommandRejected
from src.core.contest.contest_factory import ContestFactory
from src.sports.football.contest.commands import (
    AwardWalkover,
    EndPeriod,
    ScoreGoal,
    StartMatch,
)
from src.sports.football.contest.events import ContestResultOverridden, MatchConcluded
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.descriptor import FOOTBALL_SPORT
from src.core.contestant.models import Team


def _match(home_id: str = "home", away_id: str = "away") -> object:
    home = Team("Home", home_id)
    away = Team("Away", away_id)
    return ContestFactory.create(
        FOOTBALL_SPORT.id, [home, away], FootballMatchConfig(allow_draw=True)
    )


def test_walkover_during_play_is_rejected() -> None:
    match = _match()
    match.handle(StartMatch())
    match.handle(ScoreGoal(team_index=0, minute=10))
    with pytest.raises(CommandRejected, match="in progress"):
        match.handle(AwardWalkover(winner_id="away", reason="forfeit"))


def test_pre_match_walkover_emits_match_concluded() -> None:
    match = _match()
    match.handle(AwardWalkover(winner_id="away", reason="walkover"))
    assert any(isinstance(e, MatchConcluded) for e in match.history)
    assert not any(isinstance(e, ContestResultOverridden) for e in match.history)
    assert match.current_state.is_finished


def test_post_match_walkover_emits_override_not_concluded() -> None:
    match = _match()
    match.handle(StartMatch())
    match.handle(ScoreGoal(team_index=0, minute=5))
    match.handle(EndPeriod())
    match.handle(EndPeriod())
    match.handle(AwardWalkover(winner_id="away", reason="disciplinary"))
    assert any(isinstance(e, ContestResultOverridden) for e in match.history)
