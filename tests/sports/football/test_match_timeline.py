from unittest.mock import MagicMock, patch
from src.core.contest import Contest
from src.core.contest.event import EventReversed
from src.sports.football.contest.state import FootballContestState
from src.sports.football.contest.events import (
    PeriodStarted, GoalScored, PlayerCautioned, PlayerDismissed,
    PlayerSubstituted, PeriodEnded, PenaltyShootoutStarted,
    PenaltyKickTaken, MatchConcluded
)
from src.sports.football.console.match_timeline import (
    build_match_timeline, print_match_timeline, active_goals
)

def test_build_match_timeline_invalid_state() -> None:
    contest = MagicMock(spec=Contest)
    contest.current_state = MagicMock() 
    assert build_match_timeline(contest) == []
    assert active_goals(contest) == []

@patch('src.sports.football.console.match_timeline.player_name_for_id', return_value="P1")
def test_match_timeline_full_match(mock_player_name, capsys) -> None:
    contest = MagicMock(spec=Contest)
    state = MagicMock(spec=FootballContestState)
    
    mock_team = MagicMock()
    mock_team.name = "Team A"
    state.team_by_id.return_value = mock_team
    
    contest.current_state = state
    
    mock_kind = MagicMock()
    mock_kind.value = "1. polowa"
    
    # EXACT MATCH TO events.py kwargs
    contest.history = [
        PeriodStarted(event_id="e1", index=0, kind=mock_kind),
        GoalScored(event_id="e2", team_id="t1", minute=10, scorer_id="p1"),
        GoalScored(event_id="e2b", team_id="t1", minute=15, own_goal=True),
        GoalScored(event_id="e2c", team_id="t1", minute=20, penalty=True),
        PlayerCautioned(event_id="e3", team_id="t1", offender_id="p1", minute=30),
        PlayerDismissed(event_id="e4", team_id="t1", offender_id="p1", minute=40),
        PlayerSubstituted(event_id="e5", team_id="t1", player_out="p1", player_in="p2", minute=45),
        PeriodEnded(event_id="e6", kind=mock_kind),
        PenaltyShootoutStarted(event_id="e7"),
        PenaltyKickTaken(event_id="e8", team_id="t1", scored=True),
        PenaltyKickTaken(event_id="e9", team_id="t1", scored=False),
        MatchConcluded(event_id="e10", decided_by="REGULATION_TIME"),
        EventReversed(event_id="e11", target_event_id="e2", reason="VAR SPALONY")
    ]
    
    lines = build_match_timeline(contest)
    assert len(lines) == 13
    assert "rozpoczety" in lines[0]
    assert "[ANULOWANY]" in lines[1] and "GOL" in lines[1]
    assert "samobojczy" in lines[2]
    assert "karny" in lines[3]
    assert "zolta kartka P1" in lines[4]
    assert "czerwona kartka P1" in lines[5]
    assert "zmiana: P1 -> P1" in lines[6]
    assert "koniec okresu" in lines[7]
    assert "seria rzutow karnych" in lines[8]
    assert "trafiony" in lines[9]
    assert "obroniony/niecelny" in lines[10]
    assert "REGULATION TIME" in lines[11]
    assert "(VAR) wycofano zdarzenie" in lines[12]
    
    # Test active_goals (e2 is reversed, so only e2b and e2c should remain)
    goals = active_goals(contest)
    assert len(goals) == 2
    assert goals[0][0] == 1  # 1-indexed
    assert goals[0][1].event_id == "e2b"
    
    # Test Printing behavior
    print_match_timeline(contest)
    out = capsys.readouterr().out
    assert "PRZEBIEG MECZU" in out
    assert "samobojczy" in out
    
    # Test Empty Printing behavior
    contest.history = []
    print_match_timeline(contest)
    out_empty = capsys.readouterr().out
    assert "(brak zdarzen)" in out_empty

def test_match_timeline_unknown_entities() -> None:
    contest = MagicMock(spec=Contest)
    state = MagicMock(spec=FootballContestState)
    state.team_by_id.return_value = None  # Unknown team fallback
    contest.current_state = state
    
    # Scorer is None by default in event
    contest.history = [GoalScored(event_id="e1", team_id="t1", minute=10)]
    
    lines = build_match_timeline(contest)
    assert "?" in lines[0] # Asserts team fallback logic