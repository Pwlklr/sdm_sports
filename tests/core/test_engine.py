import pytest
from src.core.engine import SportsSystemEngine
from src.core.contest import Contest
from src.core.contest_state import ContestState
from src.core.ruleset import RuleSet
from src.core.contest_event import ContestEvent
from src.core.commands import MatchCommand

# Dummy implementations to satisfy the strict core requirements
class DummyState(ContestState): pass
class DummyEvent(ContestEvent): pass

def dummy_handler(ruleset: RuleSet, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
    return []

class DummyRuleSet(RuleSet):
    handlers = {DummyEvent: dummy_handler}
    def evaluate(self, event: ContestEvent, state: ContestState) -> list[ContestEvent]:
        return []

class DummyCommand(MatchCommand):
    def execute(self, match: Contest) -> None:
        match.process_event(DummyEvent())

def test_engine_player_management() -> None:
    engine = SportsSystemEngine()
    
    p1 = engine.create_individual_player("Phil Taylor", metadata={"nickname": "The Power"})
    team = engine.create_team("FC Python")
    
    assert p1.id in engine.global_players
    assert team.id in engine.global_players
    assert engine.global_players[p1.id].name == "Phil Taylor"
    assert engine.global_players[p1.id].metadata["nickname"] == "The Power"
    assert engine.global_players[team.id].name == "FC Python"

def test_engine_tournament_management() -> None:
    engine = SportsSystemEngine()
    t1 = engine.create_tournament("World Championship")
    
    assert t1.id in engine.tournaments
    assert engine.tournaments[t1.id].name == "World Championship"
    
    # Verify sub-aggregates are ready
    assert t1.registration is not None
    assert t1.scheduler is not None

def test_engine_match_dispatch() -> None:
    engine = SportsSystemEngine()
    match = Contest([], DummyState(), DummyRuleSet())
    engine.register_active_match(match)
    
    cmd = DummyCommand()
    
    # Dispatching command should route successfully
    engine.dispatch_match_command(match.id, cmd)
    
    # Dispatching to an unknown match should fail securely
    with pytest.raises(ValueError, match="not found in active memory"):
        engine.dispatch_match_command("invalid_match_id", cmd)

def test_engine_archiving() -> None:
    engine = SportsSystemEngine()
    match = Contest([], DummyState(), DummyRuleSet())
    engine.register_active_match(match)
    
    engine.archive_match(match.id)
    
    assert match.id not in engine.active_matches
    assert match.id in engine.archived_matches
    
    with pytest.raises(ValueError):
        engine.archive_match("invalid_id")