from src.sports.football.contest.entities import DisciplinaryRecord


def test_record_yellow() -> None:
    record = DisciplinaryRecord().with_yellow("p9")
    assert record.yellows_for("p9") == 1


def test_dismiss() -> None:
    record = DisciplinaryRecord().with_dismissal("p4")
    assert record.is_dismissed("p4")
