from src.sports.football.contest.entities import DisciplinaryRecord


def test_record_yellow() -> None:
    record = DisciplinaryRecord()
    record.record_yellow("p9")
    assert record.yellows_for("p9") == 1


def test_dismiss() -> None:
    record = DisciplinaryRecord()
    record.dismiss("p4")
    assert record.is_dismissed("p4")
