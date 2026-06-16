from __future__ import annotations

from src.core.contest.command import Command
from src.core.contestant.models import Team
from src.sports.football.contest.commands import (
    CommitFoul,
    EndPeriod,
    ScoreGoal,
    StartMatch,
    SubmitLineup,
    SubstitutePlayer,
    TakePenaltyKick,
)
from src.sports.football.contest.roster import (
    match_clock_limit,
    parse_console_minute,
    parse_console_player_number,
    parse_console_team_number,
    resolve_roster_player_by_number,
)
from src.sports.football.contest.roster_status import print_roster_report
from src.sports.football.contest.football_contest_state import FootballContestState, MatchPhase


def parse_football_command(
    user_input: str, state: FootballContestState
) -> Command | None:
    cleaned = user_input.strip().lower()
    parts = cleaned.split()
    if not parts:
        print("❌ Empty command.")
        return None

    verb = parts[0]

    if verb == "start":
        return StartMatch()

    if verb == "end":
        return EndPeriod()

    if verb == "roster":
        team_number = None
        if len(parts) == 2:
            try:
                team_number = int(parts[1])
            except ValueError:
                print("❌ Team must be a number (e.g. roster 1).")
                return None
        elif len(parts) > 2:
            print("❌ Usage: roster [team]")
            return None
        print_roster_report(state, team_number)
        return None

    team_count = len(state.teams)
    clock_limit = match_clock_limit(state)

    def parse_team(token: str) -> tuple[int, Team] | None:
        team_index = parse_console_team_number(token, team_count)
        if team_index is None:
            return None
        team = state.teams[team_index]
        if not isinstance(team, Team):
            print("❌ Invalid team side.")
            return None
        return team_index, team

    def parse_player_id(team: Team, token: str) -> str | None:
        player_number = parse_console_player_number(token, team)
        if player_number is None:
            return None
        return resolve_roster_player_by_number(team, player_number).id

    def parse_reason(tokens: list[str]) -> str:
        if not tokens:
            return "Foul play"
        return " ".join(tokens)

    if verb in {"goal", "og", "pen"} and len(parts) in {3, 4}:
        parsed = parse_team(parts[1])
        if parsed is None:
            return None
        team_index, team = parsed
        minute = parse_console_minute(parts[2], clock_limit)
        if minute is None:
            return None
        scorer_id = None
        if len(parts) == 4:
            scorer_id = parse_player_id(team, parts[3])
            if scorer_id is None:
                return None
        return ScoreGoal(
            team_index=team_index,
            minute=minute,
            scorer_id=scorer_id,
            own_goal=verb == "og",
            penalty=verb == "pen",
        )

    if verb in {"yellow", "red", "foul"} and len(parts) >= 4:
        parsed = parse_team(parts[1])
        if parsed is None:
            return None
        team_index, team = parsed
        offender_id = parse_player_id(team, parts[2])
        if offender_id is None:
            return None
        minute = parse_console_minute(parts[3], clock_limit)
        if minute is None:
            return None
        reason = parse_reason(parts[4:])
        card = None if verb == "foul" else verb
        return CommitFoul(
            team_index=team_index,
            minute=minute,
            card=card,
            offender_id=offender_id,
            reason=reason,
        )

    if verb == "lineup" and len(parts) >= 3:
        parsed = parse_team(parts[1])
        if parsed is None:
            return None
        team_index, team = parsed
        starting_ids: list[str] = []
        for token in parts[2:]:
            player_id = parse_player_id(team, token)
            if player_id is None:
                return None
            starting_ids.append(player_id)
        bench_ids = [
            player.id for player in team.roster if player.id not in starting_ids
        ]
        return SubmitLineup(
            team_index=team_index,
            starting=tuple(starting_ids),
            bench=tuple(bench_ids),
        )

    if verb == "sub" and len(parts) in {4, 5}:
        parsed = parse_team(parts[1])
        if parsed is None:
            return None
        team_index, team = parsed
        out_id = parse_player_id(team, parts[2])
        in_id = parse_player_id(team, parts[3])
        if out_id is None or in_id is None:
            return None
        minute = 0
        if len(parts) == 5:
            parsed_minute = parse_console_minute(parts[4], clock_limit)
            if parsed_minute is None:
                return None
            minute = parsed_minute
        return SubstitutePlayer(
            team_index=team_index,
            player_out=out_id,
            player_in=in_id,
            minute=minute,
        )

    if verb == "pk" and len(parts) == 3:
        if state.phase != MatchPhase.PENALTIES:
            print("❌ Penalty kicks are only available during a shootout.")
            return None
        parsed = parse_team(parts[1])
        if parsed is None:
            return None
        team_index, _team = parsed
        outcome = parts[2]
        if outcome not in {"g", "m"}:
            print("❌ Penalty outcome must be 'g' (goal) or 'm' (miss).")
            return None
        return TakePenaltyKick(team_index=team_index, scored=outcome == "g")

    print(
        "❌ Invalid syntax. Commands: "
        "start | end | roster [team] | goal/og/pen <team> <min> [player] | "
        "yellow/red/foul <team> <player> <min> [reason] | pk <team> g|m | "
        "lineup <team> <players...> | sub <team> <out> <in> [min]"
    )
    return None
