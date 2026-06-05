from __future__ import annotations


from src.core.contest import Contest
from src.core.contest_event import ContestEvent
from src.core.contest_state import ContestState
from src.core.ruleset import RuleSet
from src.core.team import Team


class DummyState(ContestState):
    score: int

    def __init__(self) -> None:
        super().__init__()
        self.score = 0


class DummyEvent(ContestEvent):
    pass


class DummyRuleSet(RuleSet):
    handlers = {
        DummyEvent: lambda self, event, state: DummyRuleSet._on_dummy(
            self, event, state
        ),
    }

    def _on_dummy(self, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        if event.team_id == "T1":
            state.score += 1
        return []


def test_contest_event_delegation():
    team = Team(team_id="T1", name="Test Team")
    initial_state = DummyState()
    ruleset = DummyRuleSet()

    contest = Contest(
        contest_id="C1",
        teams=[team],
        initial_state=initial_state,
        ruleset=ruleset,
    )

    event = DummyEvent(team_id="T1")
    contest.process_event(event)

    assert contest.current_state.score == 1
