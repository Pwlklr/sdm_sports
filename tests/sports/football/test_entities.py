import pytest

from src.sports.football.entities import (
    DisciplinaryRecord,
    Goal,
    MatchPeriod,
    PeriodKind,
)


def test_goal_value_object() -> None:
    goal = Goal(team_id="home", minute=23, penalty=True)
    assert goal.points == 1
    assert "pen" in str(goal)
    assert "23'" in str(goal)


def test_goal_rejects_negative_minute() -> None:
    with pytest.raises(ValueError):
        Goal(team_id="home", minute=-1)


def test_match_period_collects_goals() -> None:
    period = MatchPeriod(index=0, length_minutes=45, kind=PeriodKind.REGULAR)
    period.add_goal(Goal(team_id="home"))
    assert len(period.goals) == 1
    assert not period.is_finished


def test_match_period_cannot_add_after_end() -> None:
    period = MatchPeriod(index=0, length_minutes=45)
    period.end()
    assert period.is_finished
    with pytest.raises(ValueError):
        period.add_goal(Goal(team_id="home"))


def test_disciplinary_record_accumulates() -> None:
    record = DisciplinaryRecord(yellows_per_dismissal=2)
    assert record.caution("p1") is False
    assert record.caution("p1") is True
    assert record.is_dismissed("p1")
