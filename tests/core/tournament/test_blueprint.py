"""Tests for TournamentBlueprint, PhaseDefinition helpers, and TournamentBlueprintFactory."""

import pytest

from src.core.tournament.blueprint import (
    PhaseDefinition,
    QualificationMode,
    TournamentBlueprint,
)
from src.core.tournament.blueprint_factory import TournamentBlueprintFactory
from src.core.tournament.phase_format import PhaseFormat
from src.core.tournament.scheduling_mode import SchedulingMode

# ── PhaseDefinition helpers ─────────────────────────────────────────────────


def test_round_robin_factory_sets_correct_format() -> None:
    phase = PhaseDefinition.round_robin("group", qualifies=2)
    assert phase.format == PhaseFormat.ROUND_ROBIN
    assert phase.scheduling_mode == SchedulingMode.FIXED
    assert phase.qualification.mode == QualificationMode.TOP_N
    assert phase.qualification.n == 2


def test_knockout_factory_single_elim() -> None:
    phase = PhaseDefinition.knockout("final")
    assert phase.format == PhaseFormat.SINGLE_ELIMINATION
    assert phase.qualification.mode == QualificationMode.CHAMPION


def test_knockout_factory_double_elim() -> None:
    phase = PhaseDefinition.knockout("bracket", double_elimination=True)
    assert phase.format == PhaseFormat.DOUBLE_ELIMINATION


def test_phase_definition_requires_chain() -> None:
    group = PhaseDefinition.round_robin("group")
    playoff = PhaseDefinition.knockout("playoff", requires="group")
    assert playoff.requires == group.id


# ── TournamentBlueprint validation ──────────────────────────────────────────


def test_blueprint_validate_passes_for_valid_requires() -> None:
    bp = TournamentBlueprint(
        id="valid",
        name="Valid",
        phases=(
            PhaseDefinition.round_robin("group"),
            PhaseDefinition.knockout("knockout", requires="group"),
        ),
    )
    assert bp.validate() == []


def test_blueprint_validate_fails_for_unknown_requires() -> None:
    bp = TournamentBlueprint(
        id="broken",
        name="Broken",
        phases=(PhaseDefinition.knockout("knockout", requires="nonexistent"),),
    )
    errors = bp.validate()
    assert len(errors) == 1
    assert "nonexistent" in errors[0]


def test_blueprint_register_rejects_invalid() -> None:
    bp = TournamentBlueprint(
        id="bad_bp",
        name="Bad",
        phases=(PhaseDefinition.knockout("k", requires="missing"),),
    )
    with pytest.raises(ValueError, match="missing"):
        TournamentBlueprintFactory.register(bp)


# ── TournamentBlueprint helpers ─────────────────────────────────────────────


def test_phases_requiring() -> None:
    bp = TournamentBlueprint(
        id="multi",
        name="Multi",
        phases=(
            PhaseDefinition.round_robin("group"),
            PhaseDefinition.knockout("quarter", requires="group"),
            PhaseDefinition.knockout("semi", requires="quarter"),
        ),
    )
    assert len(bp.phases_requiring("group")) == 1
    assert bp.phases_requiring("group")[0].id == "quarter"
    assert len(bp.phases_requiring("quarter")) == 1
    assert len(bp.phases_requiring("semi")) == 0


def test_next_phase_after_uses_requires_chain() -> None:
    bp = TournamentBlueprint(
        id="seq",
        name="Seq",
        phases=(
            PhaseDefinition.round_robin("a"),
            PhaseDefinition.knockout("b", requires="a"),
            PhaseDefinition.knockout("c", requires="b"),
        ),
    )
    assert bp.next_phase_after("a") is not None
    assert bp.next_phase_after("a").id == "b"
    assert bp.next_phase_after("b").id == "c"
    assert bp.next_phase_after("c") is None


# ── @blueprint decorator ─────────────────────────────────────────────────────


def test_blueprint_decorator_registers() -> None:
    @TournamentBlueprintFactory.blueprint()
    def _mini_league() -> TournamentBlueprint:
        return TournamentBlueprint(
            id="_test_mini_league",
            name="Mini League",
            phases=(PhaseDefinition.round_robin("group"),),
        )

    bp = TournamentBlueprintFactory.get("_test_mini_league")
    assert bp.name == "Mini League"
    assert "_test_mini_league" in TournamentBlueprintFactory.list_ids()
