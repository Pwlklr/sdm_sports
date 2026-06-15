import pytest
from unittest.mock import MagicMock, patch
from src.sports.football.contest.football_rule_set import FootballRuleSet
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.commands import (
    StartMatch, ScoreGoal, EndPeriod, CommitFoul, TakePenaltyKick, SubmitLineup, SubstitutePlayer
)
from src.sports.football.contest.state import MatchPhase
from src.sports.football.contestant.football_team import FootballTeam
from src.core.contestant.models import IndividualPlayer

def test_core_rules_rejections() -> None:
    ruleset = FootballRuleSet(FootballMatchConfig())
    state = MagicMock()
    
    state.is_finished = True
    with pytest.raises(Exception, match="Mecz jest juz zakonczony"):
        ruleset.decide_start_match(StartMatch(), state)
        
    state.is_finished = False
    state.match_started = True
    with pytest.raises(Exception, match="Mecz zostal juz rozpoczety"):
        ruleset.decide_start_match(StartMatch(), state)

    state.is_finished = True
    with pytest.raises(Exception, match="nie mozna strzelic gola"):
        ruleset.decide_score_goal(ScoreGoal(team_index=0, minute=10), state)
        
    state.is_finished = False
    state.phase = MatchPhase.PENALTIES
    with pytest.raises(Exception, match="Trwa seria rzutow karnych"):
        ruleset.decide_score_goal(ScoreGoal(team_index=0, minute=10), state)
        
    state.phase = MatchPhase.REGULATION
    state.current_period = None
    with pytest.raises(Exception, match="Brak aktywnego okresu gry"):
        ruleset.decide_score_goal(ScoreGoal(team_index=0, minute=10), state)

    state.is_finished = True
    with pytest.raises(Exception, match="Mecz jest zakonczony"):
        ruleset.decide_end_period(EndPeriod(), state)
        
    state.is_finished = False
    state.phase = MatchPhase.PENALTIES
    with pytest.raises(Exception, match="Trwa seria rzutow karnych"):
        ruleset.decide_end_period(EndPeriod(), state)
        
    state.phase = MatchPhase.REGULATION
    state.current_period = None
    with pytest.raises(Exception, match="Brak aktywnego okresu do zakonczenia"):
        ruleset.decide_end_period(EndPeriod(), state)

def test_discipline_rules_rejections() -> None:
    ruleset = FootballRuleSet(FootballMatchConfig())
    state = MagicMock()
    
    state.is_finished = True
    with pytest.raises(Exception, match="nie mozna zglosic przewinienia"):
        ruleset.decide_commit_foul(CommitFoul(team_index=0, offender_id="p1", minute=10, card="yellow"), state)
        
    state.is_finished = False
    state.teams = ["Not a team"]
    with pytest.raises(Exception, match="Nieprawidlowa druzyna"):
        ruleset.decide_commit_foul(CommitFoul(team_index=0, offender_id="p1", minute=10, card="yellow"), state)

def test_knockout_rules_rejections() -> None:
    ruleset = FootballRuleSet(FootballMatchConfig())
    state = MagicMock()
    
    state.is_finished = True
    with pytest.raises(Exception, match="Mecz jest zakonczony"):
        ruleset.decide_take_penalty_kick(TakePenaltyKick(team_index=0, scored=True), state)
        
    state.is_finished = False
    state.phase = MatchPhase.REGULATION
    with pytest.raises(Exception, match="Rzuty karne dostepne tylko"):
        ruleset.decide_take_penalty_kick(TakePenaltyKick(team_index=0, scored=True), state)

def test_squad_rules_rejections() -> None:
    ruleset = FootballRuleSet(FootballMatchConfig())
    state = MagicMock()
    
    state.is_finished = True
    with pytest.raises(Exception, match="nie mozna zglosic skladu"):
        ruleset.decide_submit_lineup(SubmitLineup(team_index=0, starting=("p1",), bench=()), state)
        
    state.is_finished = False
    state.teams = ["Not a team"]
    with pytest.raises(Exception, match="Nieprawidlowa druzyna"):
        ruleset.decide_submit_lineup(SubmitLineup(team_index=0, starting=("p1",), bench=()), state)
        
    with pytest.raises(Exception, match="Nieprawidlowa druzyna"):
        ruleset.decide_substitute_player(SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10), state)

def test_advanced_scoring_and_foul_rejections() -> None:
    """Covers deep validation branches for scoring and fouls using Real objects."""
    ruleset = FootballRuleSet(FootballMatchConfig())
    state = MagicMock()
    state.is_finished = False
    state.phase = MatchPhase.REGULATION
    state.current_period.is_finished = False
    state.disciplinary.is_dismissed.return_value = False 
    
    team_a = FootballTeam(contestant_id="t1", name="Team A")
    team_a.add_player(IndividualPlayer(contestant_id="p1", name="P1"))
    state.teams = [team_a]
    
    with pytest.raises(Exception, match="Wskazany strzelec nie nalezy do tej druzyny"):
        ruleset.decide_score_goal(ScoreGoal(team_index=0, minute=10, scorer_id="ghost"), state)
        
    with pytest.raises(Exception, match="Wskazany zawodnik nie nalezy do tej druzyny"):
        ruleset.decide_commit_foul(CommitFoul(team_index=0, offender_id="ghost", minute=10, card="yellow"), state)
        
    state.disciplinary.is_dismissed.return_value = True
    with pytest.raises(Exception, match="Zawodnik zostal juz wykluczony z gry"):
        ruleset.decide_commit_foul(CommitFoul(team_index=0, offender_id="p1", minute=10, card="yellow"), state)
    state.disciplinary.is_dismissed.return_value = False
        
    with patch('src.sports.football.contest.football_rule_set._valid_minute', return_value=False):
        with pytest.raises(Exception, match="jest poza czasem gry"):
            ruleset.decide_score_goal(ScoreGoal(team_index=0, minute=999, scorer_id="p1"), state)
        with pytest.raises(Exception, match="jest poza czasem gry"):
            ruleset.decide_commit_foul(CommitFoul(team_index=0, offender_id="p1", minute=999, card="yellow"), state)

def test_advanced_substitution_rejections() -> None:
    """Covers all branches of substitution validation."""
    config = FootballMatchConfig(max_substitutions=3)
    ruleset = FootballRuleSet(config)
    
    state = MagicMock()
    state.config = config  # THE FIX: Provides the config so math comparisons succeed
    state.is_finished = False
    
    team_a = FootballTeam(contestant_id="t1", name="Team A")
    team_a.add_player(IndividualPlayer(contestant_id="p1", name="P1"))
    team_a.add_player(IndividualPlayer(contestant_id="p2", name="P2"))
    state.teams = [team_a]
    
    state.lineup_for.return_value = None
    with pytest.raises(Exception, match="Najpierw zglos sklad tej druzyny"):
        ruleset.decide_substitute_player(SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10), state)
        
    mock_lineup = MagicMock()
    mock_lineup.is_on_pitch.return_value = False
    state.lineup_for.return_value = mock_lineup
    with pytest.raises(Exception, match="Zawodnik schodzacy nie znajduje sie na boisku"):
        ruleset.decide_substitute_player(SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10), state)
        
    mock_lineup.is_on_pitch.return_value = True
    state.disciplinary.is_dismissed.return_value = True
    with pytest.raises(Exception, match="Nie mozna zmienic zawodnika, ktory zostal wykluczony"):
        ruleset.decide_substitute_player(SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10), state)
        
    state.disciplinary.is_dismissed.return_value = False
    mock_lineup.is_on_bench.return_value = False
    with pytest.raises(Exception, match="Zawodnik wchodzacy nie znajduje sie na lawce rezerwowych"):
        ruleset.decide_substitute_player(SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10), state)
        
    mock_lineup.is_on_bench.return_value = True
    mock_lineup.subs_made = 3
    with pytest.raises(Exception, match=r"Limit zmian \(3\) zostal osiagniety"):
        ruleset.decide_substitute_player(SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10), state)

@patch('src.sports.football.contest.football_rule_set.player_name_for_id', return_value="P1")
def test_lineup_suspension_rejection(mock_player_name) -> None:
    """Covers the tournament suspension check during lineup submission."""
    config = FootballMatchConfig(players_on_pitch=1)
    ruleset = FootballRuleSet(config)
    
    state = MagicMock()
    state.config = config  # THE FIX: Provides the config so math comparisons succeed
    state.is_finished = False
    
    team_a = FootballTeam(contestant_id="t1", name="Team A")
    team_a.add_player(IndividualPlayer(contestant_id="p1", name="P1"))
    state.teams = [team_a]
    
    state.is_suspended.return_value = True
    
    with pytest.raises(Exception, match="jest zawieszony i nie moze byc zgloszony"):
        ruleset.decide_submit_lineup(SubmitLineup(team_index=0, starting=("p1",), bench=()), state)