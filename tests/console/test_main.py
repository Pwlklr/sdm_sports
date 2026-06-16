import pytest
from unittest.mock import patch, MagicMock
from src.console.main import (
    main,
    print_menu,
    sport_id_for_match,
    select_sport,
    match_loop,
    setup_demo_roster,
    select_players,
    select_teams,
    select_contestants,
    play_tournament_match,
    _apply_suspension_context,
    _carry_over_discipline,
    run_tournament_matches,
)
from src.core.system.sports_system_engine import SportsSystemEngine
from src.sports.darts.plugin import DARTS_PLUGIN
from src.sports.football.plugin import FOOTBALL_PLUGIN
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.football.contest.state import FootballContestState
from src.core.contest import Contest
from src.core.contestant import IndividualPlayer, Team
from src.core.shared.command_rejected import CommandRejected


def test_sport_id_for_match() -> None:
    match = MagicMock()
    match.current_state = MagicMock(spec=DartsContestState)
    assert sport_id_for_match(match) == DARTS_PLUGIN.descriptor.id

    match.current_state = MagicMock(spec=FootballContestState)
    assert sport_id_for_match(match) == FOOTBALL_PLUGIN.descriptor.id

    match.current_state = MagicMock()
    with pytest.raises(ValueError):
        sport_id_for_match(match)


def test_select_sport_no_sports() -> None:
    engine = MagicMock()
    engine.get_available_sports.return_value = []
    with pytest.raises(SystemExit):
        select_sport(engine)


def test_select_sport_valid_choice() -> None:
    engine = MagicMock()
    engine.get_available_sports.return_value = [DARTS_PLUGIN, FOOTBALL_PLUGIN]
    with patch("builtins.input", side_effect=["2"]):
        assert select_sport(engine) == FOOTBALL_PLUGIN


def test_select_sport_invalid_choice() -> None:
    engine = MagicMock()
    engine.get_available_sports.return_value = [DARTS_PLUGIN, FOOTBALL_PLUGIN]
    with patch("builtins.input", side_effect=["invalid"]):
        assert select_sport(engine) == DARTS_PLUGIN


def test_match_loop(capsys: pytest.CaptureFixture[str]) -> None:
    engine = MagicMock()
    adapter = MagicMock()

    # Test 1: Match not found
    engine.get_match.return_value = None
    match_loop(engine, "123", adapter)
    assert "Match not found" in capsys.readouterr().out

    # Test 2: Match completes immediately
    match = MagicMock()
    match.current_state = MagicMock()
    match.current_state.is_finished = True
    engine.get_match.return_value = match
    match_loop(engine, "123", adapter)
    assert "Match Complete" in capsys.readouterr().out

    # Test 3: Suspend and Commands
    match.current_state.is_finished = False
    adapter.get_input_prompt.return_value = "prompt"
    with patch("builtins.input", side_effect=["suspend"]):
        match_loop(engine, "123", adapter)
        assert "Match Suspended" in capsys.readouterr().out

    adapter.parse_command.return_value = MagicMock()

    def dispatch_side_effect(m_id: str, cmd: object) -> None:
        if dispatch_side_effect.call_count == 0:
            dispatch_side_effect.call_count += 1
            raise CommandRejected("Nope")
        elif dispatch_side_effect.call_count == 1:
            dispatch_side_effect.call_count += 1
            raise ValueError("System Error")
        else:
            match.current_state.is_finished = True

    dispatch_side_effect.call_count = 0
    engine.dispatch_match_command.side_effect = dispatch_side_effect

    with patch("builtins.input", side_effect=["cmd1", "cmd2", "cmd3"]):
        match_loop(engine, "123", adapter)
        out = capsys.readouterr().out
        assert "Odrzucono: Nope" in out
        assert "System Error" in out
        assert "Match Complete" in out


def test_setup_demo_roster() -> None:
    engine = MagicMock()
    setup_demo_roster(engine)
    assert engine.create_individual_player.call_count == 4
    assert engine.create_team_with_roster.call_count == 4


def test_select_players() -> None:
    engine = MagicMock()

    # Brak graczy
    engine.list_individual_players.return_value = []
    assert select_players(engine) == []

    p1 = IndividualPlayer("P1")
    p2 = IndividualPlayer("P2")
    engine.list_individual_players.return_value = [p1, p2]

    # Poprawny wybór
    with patch("builtins.input", side_effect=["2", "0", "1"]):
        assert select_players(engine) == [p1, p2]

    # Błędy w trakcie wyboru a potem poprawny
    with patch("builtins.input", side_effect=["2", "99", "-1", "0", "0", "1"]):
        assert select_players(engine) == [p1, p2]

    # Błędna liczba graczy (ValueError)
    with patch("builtins.input", side_effect=["invalid"]):
        assert select_players(engine) == []


def test_select_teams() -> None:
    engine = MagicMock()

    # Brak drużyn
    engine.list_teams.return_value = []
    assert select_teams(engine) == []

    t1 = Team("T1")
    t2 = Team("T2")
    engine.list_teams.return_value = [t1, t2]

    # Poprawny wybór
    with patch("builtins.input", side_effect=["0", "1"]):
        assert select_teams(engine) == [t1, t2]

    # Wybór out of bounds, already selected
    with patch("builtins.input", side_effect=["99", "-1", "0", "0", "1"]):
        assert select_teams(engine) == [t1, t2]

    # Błędne wejście
    with patch("builtins.input", side_effect=["invalid_team"]):
        assert select_teams(engine) == []


def test_select_contestants() -> None:
    engine = MagicMock()
    engine.list_individual_players.return_value = [
        IndividualPlayer("P1"),
        IndividualPlayer("P2"),
        IndividualPlayer("P3"),
    ]
    engine.list_teams.return_value = [Team("T1"), Team("T2"), Team("T3")]

    with patch("builtins.input", side_effect=["2", "0", "1"]):
        res = select_contestants(engine, DARTS_PLUGIN, for_tournament=False)
        assert len(res) == 2

    with patch("builtins.input", side_effect=["0", "1"]):
        res = select_contestants(engine, FOOTBALL_PLUGIN, for_tournament=False)
        assert len(res) == 2


def test_play_tournament_match() -> None:
    engine = MagicMock()
    tournament = MagicMock()
    adapter = MagicMock()

    match = MagicMock()
    match.current_state = MagicMock()
    match.contestants = [IndividualPlayer("P1"), IndividualPlayer("P2")]

    # Match completes immediately
    match.current_state.is_finished = True
    with patch("builtins.input", side_effect=[""]):
        with patch("src.console.main.match_loop"):
            play_tournament_match(engine, tournament, match, adapter)
            engine.complete_tournament_match.assert_called()
            engine.archive_match.assert_called()

    # Match suspended
    match.current_state.is_finished = False
    with patch("builtins.input", side_effect=[""]):
        with patch("src.console.main.match_loop"):
            play_tournament_match(engine, tournament, match, adapter)


def test_apply_suspension_context() -> None:
    tournament = MagicMock()
    tournament.disciplinary_board.suspended_ids.return_value = ["1"]
    match = MagicMock()
    state = MagicMock(spec=FootballContestState)
    match.current_state = state
    _apply_suspension_context(tournament, match)
    state.with_tournament_context.assert_called_with(
        suspended_player_ids=frozenset(["1"])
    )


def test_carry_over_discipline() -> None:
    tournament = MagicMock()
    match = MagicMock()
    match.current_state = MagicMock()
    match.current_state.is_finished = True
    match.get_final_result.return_value = "Result"
    with patch("src.console.main.accrue_suspensions") as mock_accrue:
        _carry_over_discipline(tournament, match)
        mock_accrue.assert_called_with(tournament.disciplinary_board, "Result")


def test_run_tournament_matches(capsys: pytest.CaptureFixture[str]) -> None:
    tournament = MagicMock()
    tournament.is_completed = False
    tournament.current_phase = None
    run_tournament_matches(MagicMock(), tournament, MagicMock())
    assert "no active phase" in capsys.readouterr().out

    phase = MagicMock()
    tournament.current_phase = phase

    with patch(
        "src.console.main.active_matches",
        side_effect=[[], [], [], [], [MagicMock(spec=Contest)], []],
    ):
        with patch("src.console.main.standings_table", return_value=["row"]):
            with patch("src.console.main.schedule_view", return_value=["sch"]):
                with patch("src.console.main.play_tournament_match") as mock_play:
                    with patch(
                        "builtins.input",
                        side_effect=["invalid", "2", "3", "1", "1", "0", "4"],
                    ):
                        run_tournament_matches(MagicMock(), tournament, MagicMock())
                        out = capsys.readouterr().out
                        assert "Nieprawidlowy wybor" in out
                        assert "row" in out
                        assert "sch" in out
                        assert "Wszystkie mecze tej fazy rozegrane" in out
                        mock_play.assert_called_once()


def test_main_choice_1() -> None:
    with patch("builtins.input", side_effect=["1", "TestPlayer", "Nick", "7"]):
        with pytest.raises(SystemExit):
            main()


@patch("src.console.main.select_sport")
@patch("src.console.main.select_contestants")
@patch("src.console.main.create_console_contest")
@patch("src.console.main.match_loop")
def test_main_choice_2(
    mock_match_loop, mock_create, mock_select_c, mock_select_s
) -> None:
    mock_sport = MagicMock()
    mock_select_s.return_value = mock_sport
    mock_select_c.return_value = [MagicMock(), MagicMock()]
    mock_match = MagicMock()
    mock_create.return_value = mock_match

    with patch("builtins.input", side_effect=["2", "7"]):
        with pytest.raises(SystemExit):
            main()


@patch("src.console.main.select_sport")
@patch("src.console.main.select_contestants")
@patch("src.console.main.create_console_contest")
def test_main_choice_2_invalid_config(
    mock_create, mock_select_c, mock_select_s
) -> None:
    mock_sport = MagicMock()
    mock_select_s.return_value = mock_sport
    mock_select_c.return_value = [MagicMock(), MagicMock()]
    mock_create.side_effect = ValueError("Bad config")

    with patch("builtins.input", side_effect=["2", "7"]):
        with pytest.raises(SystemExit):
            main()


@patch("src.console.main.SportsSystemEngine.setup_tournament")
@patch("src.console.main.select_sport")
@patch("src.console.main.select_contestants")
@patch("src.console.main.run_tournament_matches")
def test_main_choice_3(mock_run, mock_select_c, mock_select_s, mock_setup) -> None:
    mock_sport = MagicMock()
    mock_sport.adapter.collect_config.return_value = MagicMock()
    mock_select_s.return_value = mock_sport
    mock_select_c.return_value = [MagicMock(), MagicMock(), MagicMock()]
    mock_setup.return_value = []

    with patch("builtins.input", side_effect=["3", "T Name", "1", "7"]):
        with pytest.raises(SystemExit):
            main()


@patch("src.console.main.select_sport")
@patch("src.console.main.select_contestants")
def test_main_choice_3_invalid_config(mock_select_c, mock_select_s) -> None:
    mock_sport = MagicMock()
    mock_sport.adapter.collect_config.side_effect = ValueError
    mock_select_s.return_value = mock_sport
    mock_select_c.return_value = [MagicMock(), MagicMock()]

    with patch("builtins.input", side_effect=["3", "T Name", "1", "7"]):
        with pytest.raises(SystemExit):
            main()


@patch("src.console.main.SportsSystemEngine.setup_tournament")
@patch("src.console.main.select_sport")
@patch("src.console.main.select_contestants")
@patch("src.console.main.run_tournament_matches")
@patch("src.console.main.SportsSystemEngine.create_tournament")
def test_main_choice_3_group_complete(
    mock_create_tour, mock_run, mock_select_c, mock_select_s, mock_setup
) -> None:
    mock_sport = MagicMock()
    mock_sport.adapter.collect_config.return_value = MagicMock()
    mock_select_s.return_value = mock_sport
    mock_select_c.return_value = [MagicMock(), MagicMock(), MagicMock()]
    mock_setup.return_value = []

    mock_tour = MagicMock()
    mock_tour.is_completed = True
    mock_phase = MagicMock()
    mock_phase.get_qualifiers.return_value = [IndividualPlayer("Q1")]
    mock_tour.phases = [mock_phase]
    mock_create_tour.return_value = mock_tour

    with patch("builtins.input", side_effect=["3", "T Name", "1", "7"]):
        with pytest.raises(SystemExit):
            main()


def test_main_choice_4() -> None:
    # No matches suspended
    with patch("src.console.main.SportsSystemEngine") as MockEngine:
        engine = MockEngine.return_value
        engine.active_matches = {}
        with patch("builtins.input", side_effect=["4", "7"]):
            with pytest.raises(SystemExit):
                main()

    # Resume match
    with patch("src.console.main.SportsSystemEngine") as MockEngine:
        engine = MockEngine.return_value
        mock_match = MagicMock()
        mock_match.contestants = [IndividualPlayer("P1"), IndividualPlayer("P2")]
        engine.active_matches = {"m1": mock_match}
        engine.get_match.return_value = mock_match

        with patch("src.console.main.match_loop"):
            with patch("builtins.input", side_effect=["4", "0", "7"]):
                with pytest.raises(SystemExit):
                    main()


def test_main_choice_5() -> None:
    with patch("src.console.main.SportsSystemEngine") as MockEngine:
        engine = MockEngine.return_value
        engine.list_individual_players.return_value = [
            IndividualPlayer("P1", metadata={"nickname": "N1"})
        ]
        engine.list_teams.return_value = [Team("T1")]
        with patch("builtins.input", side_effect=["5", "7"]):
            with pytest.raises(SystemExit):
                main()


@patch("src.core.tournament.ranking.describe_two_way_result")
@patch("src.core.tournament.ranking.single_first_place")
def test_main_choice_6(mock_sfp, mock_d2w) -> None:
    with patch("src.console.main.SportsSystemEngine") as MockEngine:
        engine = MockEngine.return_value

        p1 = IndividualPlayer("P1")
        p2 = IndividualPlayer("P2")
        darts = MagicMock()
        darts.current_state = MagicMock(spec=DartsContestState)
        darts.current_state.config = MagicMock()
        darts.current_state.config.starting_score = 501
        darts.current_state.config.sets_to_win_match = 3
        darts.current_state.players = [p1, p2]
        darts.current_state.sets_won = {p1.id: 3, p2.id: 0}
        darts.current_state.legs_won = {p1.id: 9, p2.id: 0}

        t1 = Team("T1")
        t2 = Team("T2")

        # Match 2: Football normal win
        fb1 = MagicMock()
        fb1.current_state = MagicMock(spec=FootballContestState)
        fb1.current_state.teams = [t1, t2]
        fb1.current_state.decided_by = "REGULAR_TIME"
        fb1.current_state.was_draw = False
        fb1.current_state.winner = t1
        fb1.current_state.scores = {t1.id: 2, t2.id: 1}
        fb1.result.is_overridden = False

        # Match 3: Football override remis
        fb2 = MagicMock()
        fb2.current_state = MagicMock(spec=FootballContestState)
        fb2.current_state.teams = [t1, t2]
        fb2.current_state.decided_by = "PENALTIES"
        fb2.current_state.was_draw = True
        fb2.current_state.scores = {t1.id: 1, t2.id: 1}
        fb2.result.is_overridden = True
        off2 = MagicMock()
        fb2.result.effective_result = off2
        fb2.result.override_reason = "Admin"

        # Match 4: Football override wygral
        fb3 = MagicMock()
        fb3.current_state = MagicMock(spec=FootballContestState)
        fb3.current_state.teams = [t1, t2]
        fb3.current_state.decided_by = "PENALTIES"
        fb3.current_state.was_draw = True
        fb3.current_state.scores = {t1.id: 1, t2.id: 1}
        fb3.result.is_overridden = True
        off3 = MagicMock()
        fb3.result.effective_result = off3
        fb3.result.override_reason = "Admin"

        # Match 5: Football override other
        fb4 = MagicMock()
        fb4.current_state = MagicMock(spec=FootballContestState)
        fb4.current_state.teams = [t1, t2]
        fb4.current_state.decided_by = "PENALTIES"
        fb4.current_state.was_draw = True
        fb4.current_state.scores = {t1.id: 1, t2.id: 1}
        fb4.result.is_overridden = True
        off4 = MagicMock()
        fb4.result.effective_result = off4
        fb4.result.override_reason = "Admin"

        # Match 6: Football override effective None
        fb5 = MagicMock()
        fb5.current_state = MagicMock(spec=FootballContestState)
        fb5.current_state.teams = [t1, t2]
        fb5.current_state.decided_by = "REGULAR_TIME"
        fb5.current_state.was_draw = False
        fb5.current_state.scores = {t1.id: 1, t2.id: 1}
        fb5.result.is_overridden = True
        fb5.result.effective_result = None
        fb5.result.override_reason = "Admin"

        gen = MagicMock()
        gen.current_state = MagicMock()
        gen.contestants = [t1, t2]

        engine.archived_matches = {
            "m1": darts,
            "m2": fb1,
            "m3": fb2,
            "m4": fb3,
            "m5": fb4,
            "m6": fb5,
            "m7": gen,
        }

        mock_d2w.side_effect = ["remis", "wygral T1", "other"]
        mock_sfp.return_value = t2

        with patch("builtins.input", side_effect=["6", "7"]):
            with pytest.raises(SystemExit):
                main()
