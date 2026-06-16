from __future__ import annotations

from typing import ClassVar

from src.core.contest.command import Command
from src.core.contest.event import Event, EventReversed, OfficialOverrideEvent
from src.core.contestant.models import Contestant, Team
from src.core.contest.reversal_chain import ReversalHandler
from src.core.contest.rule_set import Handler, RuleSet
from src.core.contest.walkover_mixin import WalkoverMixin
from src.core.contest.contest_state import ContestState
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
from src.sports.football.contest.football_contest_state import (
    FootballContestState,
    MatchPhase,
)


class FootballCoreRules:
    """Invariant football rules: kickoff, scoring, period progression."""

    def decide_start_match(
        self, command: StartMatch, state: FootballContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Match is already finished.")
        if state.match_started:
            reject("Match has already started.")
        eligible_map = state.eligible_player_ids
        if isinstance(eligible_map, dict) and eligible_map:
            for team in state.teams:
                if state.lineup_for(team.id) is None:
                    reject(f"Submit match squad for {team.name} before starting.")
        return [
            MatchStarted(),
            PeriodStarted(kind=PeriodKind.REGULAR, index=0),
        ]

    def decide_score_goal(
        self, command: ScoreGoal, state: FootballContestState, history: list[Event]
    ) -> list[Event]:
        if state.is_finished:
            reject("Match is finished - cannot score a goal.")
        if state.phase == MatchPhase.PENALTIES:
            reject("Penalty shootout in progress - use 'pk'.")
        period = state.current_period
        if period is None or period.is_finished:
            reject("No active period - start a period.")

        team = state.teams[command.team_index]
        if not isinstance(team, Team):
            reject("Invalid team.")
        if command.scorer_id is not None and not player_on_team(
            team, command.scorer_id
        ):
            reject("Indicated scorer does not belong to this team.")
        if command.scorer_id is not None:
            lineup = state.lineup_for(team.id)
            if lineup is None:
                reject("Submit this team's lineup before assigning a scorer.")
            if not lineup.is_on_pitch(command.scorer_id):
                reject("Indicated scorer is not on the pitch.")
            if state.disciplinary.is_dismissed(command.scorer_id):
                reject("Dismissed player cannot score.")
        if not _valid_minute(command.minute, state):
            reject(f"Minute {command.minute} is outside match time.")
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
            reject("Match is finished.")
        if state.phase == MatchPhase.PENALTIES:
            reject("Penalty shootout in progress - periods cannot be ended.")
        period = state.current_period
        if period is None or period.is_finished:
            reject("No active period to end.")
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
            if (
                state.count_periods(PeriodKind.EXTRA_TIME)
                < state.config.extra_time_halves
            ):
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
            reject("Match is finished - cannot report a foul.")

        team = state.teams[command.team_index]
        if not isinstance(team, Team):
            reject("Invalid team.")

        if command.card in {"yellow", "red"}:
            if command.offender_id is None:
                reject("No player indicated for the card.")
            if not player_on_team(team, command.offender_id):
                reject("Indicated player does not belong to this team.")
            lineup = state.lineup_for(team.id)
            if lineup is None:
                reject("Submit this team's lineup first.")
            if not lineup.is_on_pitch(command.offender_id):
                reject("Indicated player is not on the pitch.")
            if state.disciplinary.is_dismissed(command.offender_id):
                reject("Player has already been sent off.")
            if not _valid_minute(command.minute, state):
                reject(f"Minute {command.minute} is outside match time.")
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
        self,
        command: TakePenaltyKick,
        state: FootballContestState,
        history: list[Event],
    ) -> list[Event]:
        if state.is_finished:
            reject("Match is finished.")
        if state.phase != MatchPhase.PENALTIES:
            reject("Penalty kicks are only available during the shootout.")
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
            reject("Match is finished - cannot submit a lineup.")

        team = state.teams[command.team_index]
        if not isinstance(team, Team):
            reject("Invalid team.")

        starting = list(command.starting)
        bench = list(command.bench)

        if not starting:
            reject("Starting lineup cannot be empty.")
        if len(set(starting)) != len(starting) or len(set(bench)) != len(bench):
            reject("Duplicate player in the submitted lineup.")
        if set(starting) & set(bench):
            reject("A player cannot be both in the lineup and on the bench.")
        if len(starting) > state.config.players_on_pitch:
            reject(
                "Starting lineup may contain at most "
                f"{state.config.players_on_pitch} players."
            )
        if len(starting) < state.config.players_on_pitch:
            reject(
                "Starting lineup must contain at least "
                f"{state.config.players_on_pitch} players "
                f"(currently {len(starting)})."
            )
        for player_id in starting + bench:
            if not player_on_team(team, player_id):
                name = player_name_for_id(state, player_id) or player_id
                reject(f"Player {name} does not belong to team {team.name}.")
            if state.is_suspended(player_id):
                name = player_name_for_id(state, player_id) or player_id
                reject(f"Player {name} is suspended and cannot be selected.")
            eligible_map = state.eligible_player_ids
            if isinstance(eligible_map, dict) and team.id in eligible_map:
                if player_id not in eligible_map[team.id]:
                    name = player_name_for_id(state, player_id) or player_id
                    reject(
                        f"Player {name} is not on the tournament squad for {team.name}."
                    )

        return [
            LineupSubmitted(
                team_id=team.id,
                starting=tuple(starting),
                bench=tuple(bench),
            )
        ]

    def decide_substitute_player(
        self,
        command: SubstitutePlayer,
        state: FootballContestState,
        history: list[Event],
    ) -> list[Event]:
        if state.is_finished:
            reject("Match is finished - cannot make a substitution.")

        team = state.teams[command.team_index]
        if not isinstance(team, Team):
            reject("Invalid team.")

        lineup = state.lineup_for(team.id)
        if lineup is None:
            reject("Submit this team's lineup first.")
        if not lineup.is_on_pitch(command.player_out):
            reject("The player coming off is not on the pitch.")
        if state.disciplinary.is_dismissed(command.player_out):
            reject("Cannot substitute a player who has been sent off.")
        if not lineup.is_on_bench(command.player_in):
            reject("The player coming on is not on the bench.")
        if lineup.subs_made >= state.config.max_substitutions:
            reject(
                f"Substitution limit ({state.config.max_substitutions}) "
                "has been reached."
            )

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


class FootballAdminRules(WalkoverMixin):
    """Post-match corrections and administrative walkover / result override."""

    def _walkover_conclusion(
        self, winner_id: str, reason: str, **kwargs: object
    ) -> list[Event]:
        draw = bool(kwargs.get("draw", False))
        return [MatchConcluded(winner_id=winner_id, draw=draw, decided_by=reason)]

    def _walkover_override(
        self, winner_id: str, reason: str, **kwargs: object
    ) -> list[OfficialOverrideEvent]:
        ws = kwargs.get("winner_score", 3)
        ls = kwargs.get("loser_score", 0)
        return [
            ContestResultOverridden(
                winner_id=winner_id,
                reason=reason,
                winner_score=ws if isinstance(ws, int) else 3,
                loser_score=ls if isinstance(ls, int) else 0,
            )
        ]

    def decide_award_walkover(
        self, command: AwardWalkover, state: ContestState, history: list[Event]
    ) -> list[Event]:
        winner = state.team_by_id(command.winner_id)  # type: ignore[attr-defined]
        if winner is None:
            reject("Invalid winning team.")
        return self._resolve_walkover(
            winner.id,
            command.reason,
            state,
            winner_score=command.winner_score,
            loser_score=command.loser_score,
        )

    def decide_correct_goal_scorer(
        self,
        command: CorrectGoalScorer,
        state: FootballContestState,
        history: list[Event],
    ) -> list[Event]:
        if not state.is_finished:
            reject("Match is not finished - scorer correction unavailable.")

        target = _active_goal_scored(history, command.goal_event_id)
        if target is None:
            reject("No active goal found to correct.")

        team = state.team_by_id(target.team_id)
        if team is None:
            reject("Invalid team in the goal event.")
        if not player_on_team(team, command.new_scorer_id):
            reject("New scorer does not belong to the team that scored.")

        previous = target.scorer_id or ""
        if previous == command.new_scorer_id:
            reject("Scorer is already correctly assigned.")

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
        reversal_chain: ReversalHandler | None = None,
    ) -> None:
        super().__init__(reversal_chain=reversal_chain)


def _valid_minute(minute: int, state: FootballContestState) -> bool:
    return 0 <= minute <= match_clock_limit(state)


def _withdrawn_event_ids(history: list[Event]) -> set[str]:
    withdrawn: set[str] = {
        event.target_event_id for event in history if isinstance(event, EventReversed)
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
