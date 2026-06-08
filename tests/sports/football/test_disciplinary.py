from src.core.contestant import Team
from src.core.disciplinary import Penalty
from src.sports.football.disciplinary import (
    CautionPenalty,
    DismissalPenalty,
    FoulViolation,
)
from src.sports.football.entities import DisciplinaryRecord


def test_caution_pipeline() -> None:
    team = Team("Home", "home")
    record = DisciplinaryRecord(yellows_per_dismissal=2)
    violation = FoulViolation(team, "Reckless tackle")

    penalty = CautionPenalty(violation, "p9")
    assert isinstance(penalty, Penalty)

    penalty.apply(record)
    assert record.yellow_cards["p9"] == 1
    assert penalty.triggers_dismissal is False


def test_second_caution_triggers_dismissal() -> None:
    team = Team("Home", "home")
    record = DisciplinaryRecord(yellows_per_dismissal=2)
    violation = FoulViolation(team)

    CautionPenalty(violation, "p9").apply(record)
    second = CautionPenalty(violation, "p9")
    second.apply(record)

    assert second.triggers_dismissal is True
    assert record.is_dismissed("p9")


def test_dismissal_pipeline() -> None:
    team = Team("Home", "home")
    record = DisciplinaryRecord()
    violation = FoulViolation(team, "Violent conduct")

    DismissalPenalty(violation, "p4").apply(record)

    assert record.is_dismissed("p4")
