from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.disciplinary import Penalty, Violation

if TYPE_CHECKING:
    from src.core.contestant import Contestant
    from src.sports.football.entities import DisciplinaryRecord


class FoulViolation(Violation):
    """Detects an infringement of the laws of the game by a side."""

    def __init__(self, violator: Contestant, reason: str = "Foul play") -> None:
        super().__init__(violator, reason)


class CautionPenalty(Penalty):
    """Books an offender (yellow card); a second caution forces a dismissal."""

    def __init__(self, violation: Violation, offender_id: str) -> None:
        super().__init__(violation)
        self.offender_id = offender_id
        self.triggers_dismissal: bool = False

    def apply(self, state: DisciplinaryRecord) -> None:
        self.triggers_dismissal = state.caution(self.offender_id)


class DismissalPenalty(Penalty):
    """Sends an offender off (red card), removing them from the match."""

    def __init__(self, violation: Violation, offender_id: str) -> None:
        super().__init__(violation)
        self.offender_id = offender_id

    def apply(self, state: DisciplinaryRecord) -> None:
        state.dismiss(self.offender_id)
