import pytest
from unittest.mock import MagicMock, patch
from src.core.contest import Contest
from src.core.contestant import Contestant, IndividualPlayer
from src.core.tournament.phase import (
    TournamentPhase, KnockoutPhase, GroupStagePhase, GroupStanding
)
from src.core.tournament.draw import RandomDrawStrategy


class DummyPhase(TournamentPhase):
    def _apply_result(self, contest: Contest) -> None:
        pass

    def get_qualifiers(self) -> list[Contestant]:
        return []


def test_random_knockout_draw_strategy() -> None:
    strategy = RandomDrawStrategy()
    p1 = IndividualPlayer("P1")
    p2 = IndividualPlayer("P2")
    p3 = IndividualPlayer("P3")
    p4 = IndividualPlayer("P4")

    matchups = strategy.generate_draw([p1, p2, p3, p4])
    assert len(matchups) == 2

    with pytest.raises(ValueError, match="At least two contestants"):
        strategy.validate_contestants([p1])


def test_knockout_draw_handles_odd_numbers() -> None:
    strategy = RandomDrawStrategy()
    p1, p2, p3 = IndividualPlayer("P1"), IndividualPlayer("P2"), IndividualPlayer("P3")
    matchups = strategy.generate_draw([p1, p2, p3])
    assert len(matchups) == 1


def test_tournament_phase_base() -> None:
    phase = DummyPhase("Phase", RandomDrawStrategy())
    
    c = MagicMock()
    c.current_state = MagicMock()
    c.current_state.is_finished = False
    
    phase.add_contest(c)
    assert phase.completed_contests == 0
    assert not phase.check_completion()
    
    c.current_state.is_finished = True
    assert phase.completed_contests == 1
    assert phase.check_completion()
    
    c_unfin = MagicMock()
    c_unfin.current_state = MagicMock()
    c_unfin.current_state.is_finished = False
    phase.add_contest(c_unfin)
    with pytest.raises(ValueError, match="Cannot record result for an incomplete contest."):
        phase.record_match_result(c_unfin)
        
    c_not_in = MagicMock()
    c_not_in.current_state = MagicMock()
    c_not_in.current_state.is_finished = True
    with pytest.raises(ValueError, match="Contest does not belong to this phase."):
        phase.record_match_result(c_not_in)
        
    phase.record_match_result(c)


def test_knockout_phase() -> None:
    phase = KnockoutPhase("KO", RandomDrawStrategy())
    c = MagicMock()
    c.current_state = MagicMock()
    c.get_final_result.side_effect = ValueError
    phase._apply_result(c)
    
    c.get_final_result.side_effect = None
    result = MagicMock()
    c.get_final_result.return_value = result
    
    p1 = IndividualPlayer("P1")
    with patch('src.core.tournament.phase.single_first_place', return_value=p1):
        phase._apply_result(c)
        assert p1 in phase.get_qualifiers()
        # Test duplicate avoidance
        phase._apply_result(c)
        assert len(phase.get_qualifiers()) == 1


def test_group_stage_phase() -> None:
    phase = GroupStagePhase("GS", RandomDrawStrategy())
    p1, p2, p3 = IndividualPlayer("P1"), IndividualPlayer("P2"), IndividualPlayer("P3")
    
    phase.initialize_standings([p1, p2])
    assert p1.id in phase.standings
    assert phase.standings[p1.id].played == 0
    
    c_err = MagicMock()
    c_err.current_state = MagicMock()
    c_err.get_final_result.side_effect = ValueError
    phase._apply_result(c_err)
    
    c_len = MagicMock()
    c_len.current_state = MagicMock()
    c_len.get_final_result.return_value = MagicMock()
    c_len.contestants = [p1]
    phase._apply_result(c_len)
    
    c_notin = MagicMock()
    c_notin.current_state = MagicMock()
    c_notin.get_final_result.return_value = MagicMock()
    c_notin.contestants = [p3, p1]
    phase._apply_result(c_notin)
    
    c_norank = MagicMock()
    c_norank.current_state = MagicMock()
    res = MagicMock()
    res.ranking.return_value = None
    c_norank.get_final_result.return_value = res
    c_norank.contestants = [p1, p2]
    phase._apply_result(c_norank)
    
    c_valid = MagicMock()
    c_valid.current_state = MagicMock()
    res_valid = MagicMock()
    res_valid.ranking.return_value = {p1.id: {"rank": 1}, p2.id: {"rank": 2}}
    c_valid.get_final_result.return_value = res_valid
    c_valid.contestants = [p1, p2]
    
    with patch('src.core.tournament.phase.head_to_head_points', return_value=(3, 0)):
        phase._apply_result(c_valid)
    assert phase.standings[p1.id].wins == 1
    assert phase.standings[p1.id].points == 3
    assert phase.standings[p2.id].losses == 1
    
    with patch('src.core.tournament.phase.head_to_head_points', return_value=(1, 1)):
        phase._apply_result(c_valid)
    assert phase.standings[p1.id].draws == 1
    
    with patch('src.core.tournament.phase.head_to_head_points', return_value=(0, 3)):
        phase._apply_result(c_valid)
    assert phase.standings[p2.id].wins == 1

    quals = phase.get_qualifiers()
    assert len(quals) == 1
    assert quals[0] == p1


def test_group_stage_empty_qualifiers() -> None:
    phase = GroupStagePhase("GS", RandomDrawStrategy())
    assert phase.get_qualifiers() == []