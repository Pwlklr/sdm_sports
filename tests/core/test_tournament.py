from __future__ import annotations

from src.core.contest import Contest
from src.core.contest_event import ContestEvent
from src.core.contest_state import ContestState
from src.core.ruleset import RuleSet
from src.core.contestant import Contestant
from src.core.tournament_phase import TournamentPhase, DrawStrategy


class DummyContestant(Contestant):
    def __init__(self, name: str, contestant_id: str) -> None:
        self._name = name
        self._id = contestant_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return self._id

    @property
    def display_name(self) -> str:
        return self._name


class DummyState(ContestState):
    pass


class DummyEvent(ContestEvent):
    action_type: str

    def __init__(self, action_type: str) -> None:
        super().__init__()
        self.action_type = action_type


class DummyRuleSet(RuleSet):
    handlers = {
        DummyEvent: lambda self, event, state: DummyRuleSet._on_dummy(
            self, event, state
        ),
    }

    def _on_dummy(self, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        if getattr(event, "action_type", "") == "END":
            state.is_final = True
        return []


class DummyDrawStrategy(DrawStrategy):
    def generate_draw(self, contestants: list[Contestant]) -> list[tuple[Contestant, Contestant]]:
        return []


class DummyPhase(TournamentPhase):
    pass


def test_tournament_phase_observes_contest_completion() -> None:
    team_a = DummyContestant(name="Team A", contestant_id="T1")
    team_b = DummyContestant(name="Team B", contestant_id="T2")

    contest = Contest([team_a, team_b], DummyState(), DummyRuleSet(), contest_id="C1")
    phase = DummyPhase("Phase-1", DummyDrawStrategy())

    phase.add_contest(contest)

    assert phase.completed_contests == 0

    contest.process_event(DummyEvent("END"))

    assert phase.completed_contests == 1