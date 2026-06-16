import pytest
from unittest.mock import MagicMock, patch
from src.sports.football.contest.football_rule_set import FootballRuleSet
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.commands import (
    StartMatch,
    ScoreGoal,
    EndPeriod,
    CommitFoul,
    TakePenaltyKick,
    SubmitLineup,
    SubstitutePlayer,
)
from src.sports.football.contest.football_contest_state import MatchPhase
from src.core.contestant.models import IndividualPlayer, Team as FootballTeam

_HISTORY: list = []


def test_core_rules_rejections() -> None:
    ruleset = FootballRuleSet(FootballMatchConfig())
    state = MagicMock()

    state.is_finished = True
    with pytest.raises(Exception, match="Match is already finished"):
        ruleset.decide_start_match(StartMatch(), state, _HISTORY)

    state.is_finished = False
    state.match_started = True
    with pytest.raises(Exception, match="Match has already started"):
        ruleset.decide_start_match(StartMatch(), state, _HISTORY)

    state.is_finished = True
    with pytest.raises(Exception, match="cannot score a goal"):
        ruleset.decide_score_goal(ScoreGoal(team_index=0, minute=10), state, _HISTORY)

    state.is_finished = False
    state.phase = MatchPhase.PENALTIES
    with pytest.raises(Exception, match="Penalty shootout in progress"):
        ruleset.decide_score_goal(ScoreGoal(team_index=0, minute=10), state, _HISTORY)

    state.phase = MatchPhase.REGULATION
    state.current_period = None
    with pytest.raises(Exception, match="No active period"):
        ruleset.decide_score_goal(ScoreGoal(team_index=0, minute=10), state, _HISTORY)

    state.is_finished = True
    with pytest.raises(Exception, match="Match is finished"):
        ruleset.decide_end_period(EndPeriod(), state, _HISTORY)

    state.is_finished = False
    state.phase = MatchPhase.PENALTIES
    with pytest.raises(Exception, match="Penalty shootout in progress"):
        ruleset.decide_end_period(EndPeriod(), state, _HISTORY)

    state.phase = MatchPhase.REGULATION
    state.current_period = None
    with pytest.raises(Exception, match="No active period to end"):
        ruleset.decide_end_period(EndPeriod(), state, _HISTORY)


def test_discipline_rules_rejections() -> None:
    ruleset = FootballRuleSet(FootballMatchConfig())
    state = MagicMock()

    state.is_finished = True
    with pytest.raises(Exception, match="cannot report a foul"):
        ruleset.decide_commit_foul(
            CommitFoul(team_index=0, offender_id="p1", minute=10, card="yellow"),
            state,
            _HISTORY,
        )

    state.is_finished = False
    state.teams = ["Not a team"]
    with pytest.raises(Exception, match="Invalid team"):
        ruleset.decide_commit_foul(
            CommitFoul(team_index=0, offender_id="p1", minute=10, card="yellow"),
            state,
            _HISTORY,
        )


def test_knockout_rules_rejections() -> None:
    ruleset = FootballRuleSet(FootballMatchConfig())
    state = MagicMock()

    state.is_finished = True
    with pytest.raises(Exception, match="Match is finished"):
        ruleset.decide_take_penalty_kick(
            TakePenaltyKick(team_index=0, scored=True), state, _HISTORY
        )

    state.is_finished = False
    state.phase = MatchPhase.REGULATION
    with pytest.raises(Exception, match="Penalty kicks are only available"):
        ruleset.decide_take_penalty_kick(
            TakePenaltyKick(team_index=0, scored=True), state, _HISTORY
        )


def test_squad_rules_rejections() -> None:
    ruleset = FootballRuleSet(FootballMatchConfig())
    state = MagicMock()

    state.is_finished = True
    with pytest.raises(Exception, match="cannot submit a lineup"):
        ruleset.decide_submit_lineup(
            SubmitLineup(team_index=0, starting=("p1",), bench=()), state, _HISTORY
        )

    state.is_finished = False
    state.teams = ["Not a team"]
    with pytest.raises(Exception, match="Invalid team"):
        ruleset.decide_submit_lineup(
            SubmitLineup(team_index=0, starting=("p1",), bench=()), state, _HISTORY
        )

    with pytest.raises(Exception, match="Invalid team"):
        ruleset.decide_substitute_player(
            SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10),
            state,
            _HISTORY,
        )


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

    mock_lineup = MagicMock()
    mock_lineup.is_on_pitch.return_value = True
    state.lineup_for.return_value = mock_lineup

    with pytest.raises(Exception, match="Indicated scorer does not belong"):
        ruleset.decide_score_goal(
            ScoreGoal(team_index=0, minute=10, scorer_id="ghost"), state, _HISTORY
        )

    with pytest.raises(Exception, match="Indicated player does not belong"):
        ruleset.decide_commit_foul(
            CommitFoul(team_index=0, offender_id="ghost", minute=10, card="yellow"),
            state,
            _HISTORY,
        )

    state.lineup_for.return_value = None
    with pytest.raises(Exception, match="Submit this team's lineup first"):
        ruleset.decide_commit_foul(
            CommitFoul(team_index=0, offender_id="p1", minute=10, card="yellow"),
            state,
            _HISTORY,
        )

    state.lineup_for.return_value = mock_lineup
    mock_lineup.is_on_pitch.return_value = False
    with pytest.raises(Exception, match="not on the pitch"):
        ruleset.decide_commit_foul(
            CommitFoul(team_index=0, offender_id="p1", minute=10, card="yellow"),
            state,
            _HISTORY,
        )

    mock_lineup.is_on_pitch.return_value = True
    state.disciplinary.is_dismissed.return_value = True
    with pytest.raises(Exception, match="Player has already been sent off"):
        ruleset.decide_commit_foul(
            CommitFoul(team_index=0, offender_id="p1", minute=10, card="yellow"),
            state,
            _HISTORY,
        )
    state.disciplinary.is_dismissed.return_value = False

    mock_lineup.is_on_pitch.return_value = False
    with pytest.raises(Exception, match="not on the pitch"):
        ruleset.decide_score_goal(
            ScoreGoal(team_index=0, minute=10, scorer_id="p1"), state, _HISTORY
        )

    mock_lineup.is_on_pitch.return_value = True
    state.lineup_for.return_value = None
    with pytest.raises(Exception, match="lineup before assigning a scorer"):
        ruleset.decide_score_goal(
            ScoreGoal(team_index=0, minute=10, scorer_id="p1"), state, _HISTORY
        )

    state.lineup_for.return_value = mock_lineup
    with patch(
        "src.sports.football.contest.football_rule_set._valid_minute",
        return_value=False,
    ):
        with pytest.raises(Exception, match="is outside match time"):
            ruleset.decide_score_goal(
                ScoreGoal(team_index=0, minute=999, scorer_id="p1"), state, _HISTORY
            )
        with pytest.raises(Exception, match="is outside match time"):
            ruleset.decide_commit_foul(
                CommitFoul(team_index=0, offender_id="p1", minute=999, card="yellow"),
                state,
                _HISTORY,
            )


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
    with pytest.raises(Exception, match="Submit this team's lineup first"):
        ruleset.decide_substitute_player(
            SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10),
            state,
            _HISTORY,
        )

    mock_lineup = MagicMock()
    mock_lineup.is_on_pitch.return_value = False
    state.lineup_for.return_value = mock_lineup
    with pytest.raises(Exception, match="The player coming off is not on the pitch"):
        ruleset.decide_substitute_player(
            SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10),
            state,
            _HISTORY,
        )

    mock_lineup.is_on_pitch.return_value = True
    state.disciplinary.is_dismissed.return_value = True
    with pytest.raises(
        Exception, match="Cannot substitute a player who has been sent off"
    ):
        ruleset.decide_substitute_player(
            SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10),
            state,
            _HISTORY,
        )

    state.disciplinary.is_dismissed.return_value = False
    mock_lineup.is_on_bench.return_value = False
    with pytest.raises(Exception, match="The player coming on is not on the bench"):
        ruleset.decide_substitute_player(
            SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10),
            state,
            _HISTORY,
        )

    mock_lineup.is_on_bench.return_value = True
    mock_lineup.subs_made = 3
    with pytest.raises(Exception, match=r"Substitution limit \(3\)"):
        ruleset.decide_substitute_player(
            SubstitutePlayer(team_index=0, player_out="p1", player_in="p2", minute=10),
            state,
            _HISTORY,
        )


@patch(
    "src.sports.football.contest.football_rule_set.player_name_for_id",
    return_value="P1",
)
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

    with pytest.raises(Exception, match="is suspended and cannot be selected"):
        ruleset.decide_submit_lineup(
            SubmitLineup(team_index=0, starting=("p1",), bench=()), state, _HISTORY
        )
