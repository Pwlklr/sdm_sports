from unittest.mock import MagicMock
from src.core.contest import Contest
from src.core.contest.event import EventReversed
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.darts.contest.events import (
    MatchStarted,
    DartScored,
    Busted,
    TurnEnded,
    LegWon,
    SetWon,
    LegStarted,
    MatchConcluded,
)
from src.sports.darts.console.darts_timeline import (
    build_darts_timeline,
    print_darts_timeline,
)


def test_build_darts_timeline_invalid_state() -> None:
    contest = MagicMock(spec=Contest)
    contest.current_state = MagicMock()  # Not a DartsContestState
    assert build_darts_timeline(contest) == []


def test_darts_timeline_full_match(capsys) -> None:
    contest = MagicMock(spec=Contest)
    state = MagicMock(spec=DartsContestState)

    # Mock player lookup
    mock_player = MagicMock()
    mock_player.name = "Luke Littler"
    state.player_by_id.return_value = mock_player

    contest.current_state = state

    # Feed the exact history needed to hit every 'elif' branch
    contest.history = [
        MatchStarted(event_id="e1"),
        LegStarted(event_id="e2", starting_player_id="p1"),
        DartScored(event_id="e3", player_id="p1", sector=20, multiplier=3, points=60),
        Busted(event_id="e4", player_id="p1"),
        TurnEnded(event_id="e5", player_id="p1"),
        LegWon(event_id="e6", player_id="p1", caused_by="e3"),
        SetWon(event_id="e7", player_id="p1"),
        MatchConcluded(event_id="e8", winner_id="p1"),
        EventReversed(event_id="e9", target_event_id="e4", reason="Oche Fault"),
    ]

    lines = build_darts_timeline(contest)
    assert len(lines) == 9
    assert "-- match started" in lines[0]
    assert "-- new leg" in lines[1]
    assert "Luke Littler: 20 x3 = 60 pts" in lines[2]
    assert "Luke Littler: BUST" in lines[3]
    assert "-- end of turn" in lines[4]
    assert "** leg to Luke Littler" in lines[5]
    assert "*** set to Luke Littler" in lines[6]
    assert "== match ended" in lines[7]
    assert "(event reversed - reason: Oche Fault)" in lines[8]

    # Test printing behavior
    print_darts_timeline(contest)
    out = capsys.readouterr().out
    assert "MATCH TIMELINE" in out
    assert "Luke Littler: BUST" in out

    # Test printing behavior when empty
    contest.history = []
    print_darts_timeline(contest)
    out_empty = capsys.readouterr().out
    assert "(no events)" in out_empty


def test_darts_timeline_unknown_player() -> None:
    contest = MagicMock(spec=Contest)
    state = MagicMock(spec=DartsContestState)
    state.player_by_id.return_value = None  # Simulate unfound player
    contest.current_state = state
    contest.history = [TurnEnded(event_id="e1", player_id="ghost")]

    lines = build_darts_timeline(contest)
    assert "?" in lines[0]
