"""Tests for the full suspension lifecycle: issue → serve → lift."""

import pytest

from src.core.shared import CommandRejected
from src.core.tournament.command import IssueSuspension, LiftSuspension
from src.core.tournament.event import (
    SuspensionIssued,
    SuspensionLifted,
    SuspensionServed,
)
from src.core.tournament.tournament_state import DisciplineState, DefaultTournamentState
from src.core.tournament.tournament_policy import DefaultTournamentPolicy
from src.core.tournament.blueprint import TournamentBlueprint
from src.core.tournament.sport_tournament_profile import SportTournamentProfile
from src.core.tournament.default_phase_outcome_interpreter import (
    DefaultPhaseOutcomeInterpreter,
)
from src.core.tournament.sport_tournament_profile import StandingsTiebreaker
from src.core.tournament.squad_policy import PermissiveSquadPolicy


class _IdentityTiebreaker(StandingsTiebreaker):
    def order(self, contestant_ids: list[str], phase_state: object) -> list[str]:
        return list(contestant_ids)


def _policy() -> DefaultTournamentPolicy:
    return DefaultTournamentPolicy()


def _empty_state(sport_id: str = "test") -> DefaultTournamentState:
    return DefaultTournamentState(sport_id=sport_id, blueprint_id="bp")


def _profile() -> SportTournamentProfile:
    return SportTournamentProfile(
        outcome_interpreter=DefaultPhaseOutcomeInterpreter(),
        tiebreaker=_IdentityTiebreaker(),
        squad_policy=PermissiveSquadPolicy(),
    )


def _blueprint() -> TournamentBlueprint:
    return TournamentBlueprint(id="bp", name="Test", phases=())


# ── DisciplineState unit tests ──────────────────────────────────────────────


def test_issue_adds_suspension() -> None:
    ds = DisciplineState()
    ds = ds.apply(SuspensionIssued(player_id="p1", matches=2))
    assert ds.suspensions["p1"] == 2
    assert "p1" in ds.suspended_ids()


def test_served_decrements_suspension() -> None:
    ds = DisciplineState()
    ds = ds.apply(SuspensionIssued(player_id="p1", matches=2))
    ds = ds.apply(SuspensionServed(player_id="p1"))
    assert ds.suspensions["p1"] == 1
    assert "p1" in ds.suspended_ids()


def test_served_removes_when_reaches_zero() -> None:
    ds = DisciplineState()
    ds = ds.apply(SuspensionIssued(player_id="p1", matches=1))
    ds = ds.apply(SuspensionServed(player_id="p1"))
    assert "p1" not in ds.suspensions
    assert "p1" not in ds.suspended_ids()


def test_served_is_no_op_when_no_suspension() -> None:
    ds = DisciplineState()
    ds2 = ds.apply(SuspensionServed(player_id="unknown"))
    assert ds2 is ds


def test_lifted_removes_suspension() -> None:
    ds = DisciplineState()
    ds = ds.apply(SuspensionIssued(player_id="p1", matches=3))
    ds = ds.apply(SuspensionLifted(player_id="p1"))
    assert "p1" not in ds.suspensions


def test_lifted_is_no_op_for_no_suspension() -> None:
    ds = DisciplineState()
    ds2 = ds.apply(SuspensionLifted(player_id="nobody"))
    assert ds2 is ds


def test_issue_takes_max_when_existing() -> None:
    ds = DisciplineState()
    ds = ds.apply(SuspensionIssued(player_id="p1", matches=1))
    ds = ds.apply(SuspensionIssued(player_id="p1", matches=3))
    assert ds.suspensions["p1"] == 3


# ── Policy command handler tests ────────────────────────────────────────────


def test_policy_issue_suspension_command() -> None:
    policy = _policy()
    state = _empty_state()
    blueprint = _blueprint()
    profile = _profile()

    events = policy.decide(
        IssueSuspension(player_id="p1", matches=2),
        state,
        [],
        blueprint=blueprint,
        profile=profile,
    )
    assert len(events) == 1
    ev = events[0]
    assert isinstance(ev, SuspensionIssued)
    assert ev.player_id == "p1"
    assert ev.matches == 2


def test_policy_issue_zero_matches_rejected() -> None:
    policy = _policy()
    state = _empty_state()
    blueprint = _blueprint()
    profile = _profile()

    with pytest.raises(CommandRejected):
        policy.decide(
            IssueSuspension(player_id="p1", matches=0),
            state,
            [],
            blueprint=blueprint,
            profile=profile,
        )


def test_policy_lift_suspension_command() -> None:
    policy = _policy()
    state = _empty_state()
    state = state.apply(SuspensionIssued(player_id="p1", matches=2))
    blueprint = _blueprint()
    profile = _profile()

    events = policy.decide(
        LiftSuspension(player_id="p1"),
        state,
        [],
        blueprint=blueprint,
        profile=profile,
    )
    assert len(events) == 1
    assert isinstance(events[0], SuspensionLifted)


def test_policy_lift_nonexistent_suspension_rejected() -> None:
    policy = _policy()
    state = _empty_state()
    blueprint = _blueprint()
    profile = _profile()

    with pytest.raises(CommandRejected):
        policy.decide(
            LiftSuspension(player_id="nobody"),
            state,
            [],
            blueprint=blueprint,
            profile=profile,
        )
