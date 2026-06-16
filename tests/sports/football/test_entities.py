import pytest

from src.sports.football.contest.entities import (
    DisciplinaryRecord,
    Goal,
    MatchPeriod,
    PeriodKind,
)


def test_goal_value_object() -> None:
    goal = Goal(team_id="home", minute=23, penalty=True)
    assert goal.points == 1


def test_goal_rejects_negative_minute() -> None:
    with pytest.raises(ValueError):
        Goal(team_id="home", minute=-1)


def test_match_period_collects_goals() -> None:
    period = MatchPeriod(index=0, length_minutes=45, kind=PeriodKind.REGULAR)
    period = period.with_goal(Goal(team_id="home"))
    assert len(period.goals) == 1
    assert not period.is_finished


def test_disciplinary_record_accumulates() -> None:
    record = DisciplinaryRecord()
    record = record.with_yellow("p1")
    record = record.with_yellow("p1")
    assert record.yellows_for("p1") == 2


def test_team_str_and_id() -> None:
    from src.core.contestant.models import Team

    team = Team(name="Real Madrid", contestant_id="team_1")
    assert str(team) == "Real Madrid"
    assert team.id == "team_1"
