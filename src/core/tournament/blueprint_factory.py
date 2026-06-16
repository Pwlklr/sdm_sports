from __future__ import annotations

from typing import Any

from src.core.tournament.blueprint import (
    PhaseDefinition,
    QualificationMode,
    QualificationRule,
    TournamentBlueprint,
)
from src.core.tournament.phase_format import PhaseFormat
from src.core.tournament.scheduling_mode import SchedulingMode


class TournamentBlueprintFactory:
    _blueprints: dict[str, TournamentBlueprint] = {}

    @classmethod
    def register(cls, blueprint: TournamentBlueprint) -> None:
        cls._blueprints[blueprint.id] = blueprint

    @classmethod
    def get(cls, blueprint_id: str) -> TournamentBlueprint:
        bp = cls._blueprints.get(blueprint_id)
        if bp is None:
            raise ValueError(f"Unknown tournament blueprint '{blueprint_id}'")
        return bp

    @classmethod
    def create_phases(
        cls, blueprint_id: str, match_configs: dict[str, Any] | None = None
    ) -> tuple[PhaseDefinition, ...]:
        bp = cls.get(blueprint_id)
        configs = match_configs or {}
        result: list[PhaseDefinition] = []
        for phase in bp.phases:
            result.append(
                PhaseDefinition(
                    id=phase.id,
                    name=phase.name,
                    format=phase.format,
                    scheduling_mode=phase.scheduling_mode,
                    match_config=configs.get(phase.id, phase.match_config),
                    qualification=phase.qualification,
                    requires=phase.requires,
                    group_count=phase.group_count,
                )
            )
        return tuple(result)


def _register_defaults() -> None:
    TournamentBlueprintFactory.register(
        TournamentBlueprint(
            id="league",
            name="League",
            phases=(
                PhaseDefinition(
                    id="group",
                    name="League Stage",
                    format=PhaseFormat.ROUND_ROBIN,
                    scheduling_mode=SchedulingMode.FIXED,
                    match_config=None,
                    qualification=QualificationRule(
                        mode=QualificationMode.TOP_N, n=1
                    ),
                ),
            ),
        )
    )
    TournamentBlueprintFactory.register(
        TournamentBlueprint(
            id="knockout_8",
            name="Knockout 8",
            phases=(
                PhaseDefinition(
                    id="knockout",
                    name="Knockout",
                    format=PhaseFormat.SINGLE_ELIMINATION,
                    scheduling_mode=SchedulingMode.PROGRESSIVE,
                    match_config=None,
                    qualification=QualificationRule(
                        mode=QualificationMode.CHAMPION
                    ),
                ),
            ),
        )
    )
    TournamentBlueprintFactory.register(
        TournamentBlueprint(
            id="double_elim_8",
            name="Double Elimination 8",
            phases=(
                PhaseDefinition(
                    id="double_elim",
                    name="Double Elimination",
                    format=PhaseFormat.DOUBLE_ELIMINATION,
                    scheduling_mode=SchedulingMode.PROGRESSIVE,
                    match_config=None,
                    qualification=QualificationRule(
                        mode=QualificationMode.CHAMPION
                    ),
                ),
            ),
        )
    )
    TournamentBlueprintFactory.register(
        TournamentBlueprint(
            id="world_cup",
            name="World Cup",
            phases=(
                PhaseDefinition(
                    id="group",
                    name="Group Stage",
                    format=PhaseFormat.ROUND_ROBIN,
                    scheduling_mode=SchedulingMode.FIXED,
                    match_config=None,
                    qualification=QualificationRule(
                        mode=QualificationMode.TOP_N_PER_GROUP, n=2
                    ),
                    group_count=2,
                ),
                PhaseDefinition(
                    id="knockout",
                    name="Knockout Bracket",
                    format=PhaseFormat.SINGLE_ELIMINATION,
                    scheduling_mode=SchedulingMode.PROGRESSIVE,
                    match_config=None,
                    qualification=QualificationRule(
                        mode=QualificationMode.CHAMPION
                    ),
                    requires="group",
                ),
            ),
        )
    )


_register_defaults()
