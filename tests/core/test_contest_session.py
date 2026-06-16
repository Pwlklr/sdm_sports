"""Tests for contest session lifecycle (suspend / resume)."""

import pytest

from src.core.contest.contest_session import ContestSessionStatus
from src.core.contestant.models import IndividualPlayer
from src.core.contest import ContestFactory
from src.sports.darts.contest.commands import StartMatch
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.descriptor import DARTS_SPORT


def _started_darts_match():
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    match = ContestFactory.create(DARTS_SPORT.id, players, DartsMatchConfig())
    match.handle(StartMatch())
    return match


def test_session_status_not_started() -> None:
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    match = ContestFactory.create(DARTS_SPORT.id, players, DartsMatchConfig())
    assert match.session_status is ContestSessionStatus.NOT_STARTED
    assert not match.is_suspended


def test_suspend_marks_contest_suspended() -> None:
    match = _started_darts_match()
    assert match.session_status is ContestSessionStatus.IN_PROGRESS

    match.suspend()

    assert match.is_suspended
    assert match.session_status is ContestSessionStatus.SUSPENDED


def test_resume_clears_suspended_flag() -> None:
    match = _started_darts_match()
    match.suspend()
    match.resume()

    assert not match.is_suspended
    assert match.session_status is ContestSessionStatus.IN_PROGRESS


def test_cannot_suspend_before_start() -> None:
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    match = ContestFactory.create(DARTS_SPORT.id, players, DartsMatchConfig())
    with pytest.raises(ValueError, match="not started"):
        match.suspend()


def test_cannot_resume_when_not_suspended() -> None:
    match = _started_darts_match()
    with pytest.raises(ValueError, match="not suspended"):
        match.resume()


def test_engine_suspend_match() -> None:
    from src.core.system.sports_system_engine import SportsSystemEngine
    from src.sports.darts.plugin import DARTS_PLUGIN

    engine = SportsSystemEngine(sports=[DARTS_PLUGIN])
    match = _started_darts_match()
    engine.register_active_match(match)

    engine.suspend_match(match.id)

    assert match.is_suspended
