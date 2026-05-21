from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.contest import Contest
    from src.core.ruleset import RuleSet


class TournamentPhase:
    """
    Represents a specific stage of the tournament that organizes matches
    according to assigned rules.
    """
    phase_id: str
    ruleset: RuleSet
    contests: list[Contest]

    def __init__(
        self,
        phase_id: str,
        ruleset: RuleSet,
        contests: list[Contest] | None = None,
    ) -> None:
        self.phase_id = phase_id
        self.ruleset = ruleset
        self.contests = contests if contests is not None else []
