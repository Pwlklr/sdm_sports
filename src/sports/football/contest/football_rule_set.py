from __future__ import annotations

from typing import ClassVar

from src.core.contest.command import Command
from src.core.contest.event import Event, EventReversed
from src.core.contestant.models import Contestant, Team
from src.core.contest.rule_set import Handler, RuleSet
from src.core.shared.command_rejected import reject
from src.sports.football.contest.commands import (
    AwardWalkover,
    CommitFoul,
    CorrectGoalScorer,
    EndPeriod,
    ScoreGoal,
    StartMatch,
    SubmitLineup,
    SubstitutePlayer,
    TakePenaltyKick,
)
from src.sports.football.contest.entities import PeriodKind
from src.sports.football.contest.events import (
    ContestResultOverridden,
    ExtraTimeStarted,
    GoalScored,
    GoalScorerCorrected,
    LineupSubmitted,
    MatchConcluded,
    MatchStarted,
    PenaltyKickTaken,
    PenaltyShootoutStarted,
    PeriodEnded,
    PeriodStarted,
    PlayerCautioned,
    PlayerDismissed,
    PlayerSubstituted,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.roster import (
    match_clock_limit,
    player_name_for_id,
    player_on_team,
)
from src.sports.football.contest.football_contest_state import FootballContestState, MatchPhase


class FootballCoreRules:
    """Invariant football rules: kickoff, scoring, period progression."""

    def decide_start_match(
        self, command: StartMatch, state: FootballContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Mecz jest juz zakonczony.")
        if state.match_started:
            reject("Mecz zostal juz rozpoczety.")
        return [
            MatchStarted(),
            PeriodStarted(kind=PeriodKind.REGULAR, index=0),
        ]

    def decide_score_goal(
        self, command: ScoreGoal, state: FootballContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Mecz jest zakonczony - nie mozna strzelic gola.")
        if state.phase == MatchPhase.PENALTIES:
            reject("Trwa seria rzutow karnych - uzyj 'pk'.")
        period = state.current_period
        if period is None or period.is_finished:
            reject("Brak aktywnego okresu gry - rozpocznij okres.")

        team = state.teams[command.team_index]
        if not isinstance(team, Team):
            reject("Nieprawidlowa druzyna.")
        if command.scorer_id is not None and not player_on_team(
            team, command.scorer_id
        ):
            reject("Wskazany strzelec nie nalezy do tej druzyny.")
        if not _valid_minute(command.minute, state):
            reject(f"Minuta {command.minute} jest poza czasem gry.")
        credited = state.opponent_of(team) if command.own_goal else team
        return [
            GoalScored(
                team_id=credited.id,
                scorer_id=command.scorer_id,
                minute=command.minute,
                own_goal=command.own_goal,
                penalty=command.penalty,
            )
        ]

    def decide_end_period(
        self, command: EndPeriod, state: FootballContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Mecz jest zakonczony.")
        if state.phase == MatchPhase.PENALTIES:
            reject("Trwa seria rzutow karnych - nie konczy sie okresow.")
        period = state.current_period
        if period is None or period.is_finished:
            reject("Brak aktywnego okresu do zakonczenia.")
        return [PeriodEnded(kind=period.kind)]

    def react_period_ended(
        self, fact: PeriodEnded, state: FootballContestState
    ) -> list[Event]:
        if state.phase == MatchPhase.REGULATION:
            if state.count_periods(PeriodKind.REGULAR) < state.config.number_of_halves:
                return [
                    PeriodStarted(
                        kind=PeriodKind.REGULAR,
                        index=state.count_periods(PeriodKind.REGULAR),
                    )
                ]
            return _after_regulation(state)

        if state.phase == MatchPhase.EXTRA_TIME:
            if state.count_periods(PeriodKind.EXTRA_TIME) < state.config.extra_time_halves:
                return [
                    PeriodStarted(
                        kind=PeriodKind.EXTRA_TIME,
                        index=state.count_periods(PeriodKind.EXTRA_TIME),
                    )
                ]
            return _after_extra_time(state)

        return []

    _own_command_handlers: ClassVar[dict[type[Command], Handler]] = {
        StartMatch: decide_start_match,
        ScoreGoal: decide_score_goal,
        EndPeriod: decide_end_period,
    }
    _own_reaction_handlers: ClassVar[dict[type[Event], Handler]] = {
        PeriodEnded: react_period_ended,
    }


class FootballDisciplineRules:
    """Cards and dismissals."""

    def decide_commit_foul(
        self, command: CommitFoul, state: FootballContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Mecz jest zakonczony - nie mozna zglosic przewinienia.")

        team = state.teams[command.team_index]
        if not isinstance(team, Team):
            reject("Nieprawidlowa druzyna.")

        if command.card in {"yellow", "red"}:
            if command.offender_id is None:
                reject("Brak wskazanego zawodnika dla kartki.")
            if not player_on_team(team, command.offender_id):
                reject("Wskazany zawodnik nie nalezy do tej druzyny.")
            if state.disciplinary.is_dismissed(command.offender_id):
                reject("Zawodnik zostal juz wykluczony z gry.")
            if not _valid_minute(command.minute, state):
                reject(f"Minuta {command.minute} jest poza czasem gry.")
            if command.card == "red":
                return [
                    PlayerDismissed(
                        team_id=team.id,
                        offender_id=command.offender_id,
                        minute=command.minute,
                    )
                ]
            return [
                PlayerCautioned(
                    team_id=team.id,
                    offender_id=command.offender_id,
                    minute=command.minute,
                )
            ]
        return []

    def react_player_cautioned(
        self, fact: PlayerCautioned, state: FootballContestState
    ) -> list[Event]:
        if state.disciplinary.is_dismissed(fact.offender_id):
            return []
        if (
            state.disciplinary.yellows_for(fact.offender_id)
            >= state.config.yellows_per_dismissal
        ):
            return [
                PlayerDismissed(
                    team_id=fact.team_id,
                    offender_id=fact.offender_id,
                    minute=fact.minute,
                )
            ]
        return []

    def react_player_dismissed(
        self, fact: PlayerDismissed, state: FootballContestState
    ) -> list[Event]:
        if state.is_finished:
            return []
        remaining = state.active_players_on_pitch(fact.team_id)
        if remaining >= state.config.min_players_on_pitch:
            return []
        team = state.team_by_id(fact.team_id)
        if team is None:
            return []
        opponent = state.opponent_of(team)
        return [
            MatchConcluded(
                winner_id=opponent.id,
                draw=False,
                decided_by="walkover_insufficient_players",
            )
        ]

    _own_command_handlers: ClassVar[dict[type[Command], Handler]] = {
        CommitFoul: decide_commit_foul,
    }
    _own_reaction_handlers: ClassVar[dict[type[Event], Handler]] = {
        PlayerCautioned: react_player_cautioned,
        PlayerDismissed: react_player_dismissed,
    }


class FootballKnockoutRules:
    """Extra time, golden goal and penalty shootout."""

    def decide_take_penalty_kick(
        self, command: TakePenaltyKick, state: FootballContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Mecz jest zakonczony.")
        if state.phase != MatchPhase.PENALTIES:
            reject("Rzuty karne dostepne tylko w serii rzutow karnych.")
        team = state.teams[command.team_index]
        return [PenaltyKickTaken(team_id=team.id, scored=command.scored)]

    def react_goal_scored(
        self, fact: GoalScored, state: FootballContestState
    ) -> list[Event]:
        if state.phase != MatchPhase.EXTRA_TIME or not state.config.golden_goal:
            return []
        leader = state.leading_team()
        if leader is None:
            return []
        return [
            MatchConcluded(
                winner_id=leader.id,
                draw=False,
                decided_by="golden_goal",
            )
        ]

    def react_penalty_kick_taken(
        self, fact: PenaltyKickTaken, state: FootballContestState
    ) -> list[Event]:
        winner = _shootout_winner(state)
        if winner is None:
            return []
        return [
            MatchConcluded(
                winner_id=winner.id,
                draw=False,
                decided_by="penalties",
            )
        ]

    _own_command_handlers: ClassVar[dict[type[Command], Handler]] = {
        TakePenaltyKick: decide_take_penalty_kick,
    }
    _own_reaction_handlers: ClassVar[dict[type[Event], Handler]] = {
        GoalScored: react_goal_scored,
        PenaltyKickTaken: react_penalty_kick_taken,
    }


class FootballSquadRules:
    """Lineups, bench and substitutions, including tournament suspension checks."""

    def decide_submit_lineup(
        self, command: SubmitLineup, state: FootballContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Mecz jest zakonczony - nie mozna zglosic skladu.")

        team = state.teams[command.team_index]
        if not isinstance(team, Team):
            reject("Nieprawidlowa druzyna.")

        starting = list(command.starting)
        bench = list(command.bench)

        if not starting:
            reject("Sklad podstawowy nie moze byc pusty.")
        if len(set(starting)) != len(starting) or len(set(bench)) != len(bench):
            reject("Powtorzony zawodnik w zgloszonym skladzie.")
        if set(starting) & set(bench):
            reject("Zawodnik nie moze byc jednoczesnie w skladzie i na lawce.")
        if len(starting) > state.config.players_on_pitch:
            reject(
                f"Sklad podstawowy moze liczyc maksymalnie {state.config.players_on_pitch} zawodnikow."
            )
        if len(starting) < state.config.players_on_pitch:
            reject(
                f"Sklad podstawowy musi liczyc co najmniej {state.config.players_on_pitch} zawodnikow "
                f"(obecnie {len(starting)})."
            )
        for player_id in starting + bench:
            if not player_on_team(team, player_id):
                name = player_name_for_id(state, player_id) or player_id
                reject(f"Zawodnik {name} nie nalezy do druzyny {team.name}.")
            if state.is_suspended(player_id):
                name = player_name_for_id(state, player_id) or player_id
                reject(f"Zawodnik {name} jest zawieszony i nie moze byc zgloszony.")

        return [
            LineupSubmitted(
                team_id=team.id,
                starting=tuple(starting),
                bench=tuple(bench),
            )
        ]

    def decide_substitute_player(
        self, command: SubstitutePlayer, state: FootballContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Mecz jest zakonczony - nie mozna dokonac zmiany.")

        team = state.teams[command.team_index]
        if not isinstance(team, Team):
            reject("Nieprawidlowa druzyna.")

        lineup = state.lineup_for(team.id)
        if lineup is None:
            reject("Najpierw zglos sklad tej druzyny.")
        if not lineup.is_on_pitch(command.player_out):
            reject("Zawodnik schodzacy nie znajduje sie na boisku.")
        if state.disciplinary.is_dismissed(command.player_out):
            reject("Nie mozna zmienic zawodnika, ktory zostal wykluczony.")
        if not lineup.is_on_bench(command.player_in):
            reject("Zawodnik wchodzacy nie znajduje sie na lawce rezerwowych.")
        if lineup.subs_made >= state.config.max_substitutions:
            reject(f"Limit zmian ({state.config.max_substitutions}) zostal osiagniety.")

        return [
            PlayerSubstituted(
                team_id=team.id,
                player_out=command.player_out,
                player_in=command.player_in,
                minute=command.minute,
            )
        ]

    _own_command_handlers: ClassVar[dict[type[Command], Handler]] = {
        SubmitLineup: decide_submit_lineup,
        SubstitutePlayer: decide_substitute_player,
    }


class FootballAdminRules:
    """Post-match corrections and administrative walkover / result override."""

    def decide_award_walkover(
        self, command: AwardWalkover, state: FootballContestState, history: list[Event]
    ) -> list[Event]:
        winner = state.team_by_id(command.winner_id)
        if winner is None:
            reject("Nieprawidlowa druzyna zwycieska.")

        if state.match_started and not state.is_finished:
            reject("Mecz trwa - walkover administracyjny niedostepny w trakcie gry.")

        if not state.is_finished:
            return [
                MatchConcluded(
                    winner_id=winner.id,
                    draw=False,
                    decided_by=command.reason,
                )
            ]

        return [
            ContestResultOverridden(
                winner_id=winner.id,
                reason=command.reason,
                winner_score=command.winner_score,
                loser_score=command.loser_score,
            )
        ]

    def decide_correct_goal_scorer(
        self, command: CorrectGoalScorer, state: FootballContestState, history: list[Event]
    ) -> list[Event]:
        if not state.is_finished:
            reject("Mecz nie jest zakonczony - korekta strzelca niedostepna.")

        target = _active_goal_scored(history, command.goal_event_id)
        if target is None:
            reject("Nie znaleziono aktywnego gola do korekty.")

        team = state.team_by_id(target.team_id)
        if team is None:
            reject("Nieprawidlowa druzyna w evencie gola.")
        if not player_on_team(team, command.new_scorer_id):
            reject("Nowy strzelec nie nalezy do druzyny strzelajacej gola.")

        previous = target.scorer_id or ""
        if previous == command.new_scorer_id:
            reject("Strzelec jest juz poprawnie przypisany.")

        return [
            GoalScorerCorrected(
                goal_event_id=command.goal_event_id,
                team_id=target.team_id,
                minute=target.minute,
                previous_scorer_id=previous,
                new_scorer_id=command.new_scorer_id,
            )
        ]

    _own_command_handlers: ClassVar[dict[type[Command], Handler]] = {
        AwardWalkover: decide_award_walkover,
        CorrectGoalScorer: decide_correct_goal_scorer,
    }


class FootballRuleSet(
    FootballCoreRules,
    FootballDisciplineRules,
    FootballKnockoutRules,
    FootballSquadRules,
    FootballAdminRules,
    RuleSet,
):
    def __init__(
        self,
        config: FootballMatchConfig,
        reversal_chain=None,
    ) -> None:
        super().__init__(reversal_chain=reversal_chain)
        self._config = config


def _valid_minute(minute: int, state: FootballContestState) -> bool:
    return 0 <= minute <= match_clock_limit(state)


def _withdrawn_event_ids(history: list[Event]) -> set[str]:
    withdrawn: set[str] = {
        event.target_event_id
        for event in history
        if isinstance(event, EventReversed)
    }
    changed = True
    while changed:
        changed = False
        for event in history:
            if event.caused_by in withdrawn and event.event_id not in withdrawn:
                withdrawn.add(event.event_id)
                changed = True
    return withdrawn


def _active_goal_scored(history: list[Event], goal_event_id: str) -> GoalScored | None:
    withdrawn = _withdrawn_event_ids(history)
    for event in history:
        if isinstance(event, GoalScored) and event.event_id == goal_event_id:
            if event.event_id not in withdrawn:
                return event
    return None


def _after_regulation(state: FootballContestState) -> list[Event]:
    if not state.is_draw or state.config.allow_draw:
        winner = state.leading_team()
        return [
            MatchConcluded(
                winner_id=winner.id if winner else None,
                draw=winner is None,
                decided_by="regulation",
            )
        ]

    if state.config.extra_time_halves > 0:
        return [
            ExtraTimeStarted(),
            PeriodStarted(kind=PeriodKind.EXTRA_TIME, index=0),
        ]

    return [PenaltyShootoutStarted()]


def _after_extra_time(state: FootballContestState) -> list[Event]:
    if not state.is_draw:
        winner = state.leading_team()
        assert winner is not None
        return [
            MatchConcluded(
                winner_id=winner.id,
                draw=False,
                decided_by="extra_time",
            )
        ]

    return [PenaltyShootoutStarted()]


def _shootout_winner(state: FootballContestState) -> Contestant | None:
    first, second = state.teams[0], state.teams[1]
    attempts_a = state.penalty_attempts[first.id]
    attempts_b = state.penalty_attempts[second.id]
    score_a = state.penalty_scores[first.id]
    score_b = state.penalty_scores[second.id]
    rounds = state.config.penalty_shootout_rounds

    if attempts_a <= rounds and attempts_b <= rounds:
        remaining_a = max(rounds - attempts_a, 0)
        remaining_b = max(rounds - attempts_b, 0)
        if score_a - score_b > remaining_b:
            return first
        if score_b - score_a > remaining_a:
            return second

    if attempts_a == attempts_b and attempts_a >= rounds and score_a != score_b:
        return first if score_a > score_b else second

    return None
