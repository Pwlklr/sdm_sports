from __future__ import annotations

import uuid
from typing import Any, Dict, Iterable, List, Optional

from src.core.contest import Contest
from src.core.contest.command import Command
from src.core.contestant.models import Contestant, IndividualPlayer, Team
from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.registered_sport import RegisteredSport
from src.core.sport.sport_descriptor import SportDescriptor
from src.core.sport.sport_plugin import SportPlugin
from src.core.tournament import Tournament
from src.core.tournament.command import RecordMatchOutcome
from src.core.tournament.event import FixtureScheduled
from src.core.tournament.tournament_entry import TournamentEntry


class SportsSystemEngine:
    """Central entry point: repositories and command dispatch for the sports library."""

    def __init__(self, sports: Iterable[SportPlugin] = ()) -> None:
        self.global_players: Dict[str, Contestant] = {}
        self.tournaments: Dict[str, Tournament] = {}
        self.active_matches: Dict[str, Contest] = {}
        self.archived_matches: Dict[str, Contest] = {}
        self._sports: Dict[str, RegisteredSport] = {}
        for plugin in sports:
            self.register_plugin(plugin)

    def register_plugin(self, plugin: SportPlugin) -> None:
        self._sports[plugin.descriptor.id] = RegisteredSport(
            plugin.descriptor,
            plugin.adapter,
            plugin.match_metrics_reader,
        )

    def register_sport(
        self,
        descriptor: SportDescriptor,
        adapter: Optional[ConsoleAdapter] = None,
        match_metrics_reader: Any = None,
    ) -> None:
        if adapter is not None and adapter.descriptor != descriptor:
            raise ValueError(
                f"Adapter descriptor '{adapter.descriptor.id}' does not match "
                f"registered sport '{descriptor.id}'."
            )
        self._sports[descriptor.id] = RegisteredSport(
            descriptor, adapter, match_metrics_reader
        )

    def get_available_sports(self) -> List[RegisteredSport]:
        return list(self._sports.values())

    def get_sport(self, sport_id: str) -> Optional[RegisteredSport]:
        return self._sports.get(sport_id)

    def get_adapter(self, sport_id: str) -> Optional[ConsoleAdapter]:
        sport = self._sports.get(sport_id)
        return sport.adapter if sport else None

    def get_match_metrics_reader(self, sport_id: str) -> Any:
        sport = self._sports.get(sport_id)
        return sport.match_metrics_reader if sport else None

    def create_individual_player(
        self, name: str, metadata: Optional[Dict[str, str]] = None
    ) -> IndividualPlayer:
        player = IndividualPlayer(name, metadata=metadata)
        self.global_players[player.id] = player
        return player

    def create_team(self, name: str, metadata: Optional[Dict[str, str]] = None) -> Team:
        team = Team(name, metadata=metadata)
        self.global_players[team.id] = team
        return team

    def create_team_with_roster(
        self,
        name: str,
        player_names: List[str],
        metadata: Optional[Dict[str, str]] = None,
    ) -> Team:
        team = self.create_team(name, metadata=metadata)
        for player_name in player_names:
            team.add_player(IndividualPlayer(player_name))
        return team

    def list_individual_players(self) -> List[IndividualPlayer]:
        return [
            c for c in self.global_players.values() if isinstance(c, IndividualPlayer)
        ]

    def list_teams(self) -> List[Team]:
        return [c for c in self.global_players.values() if isinstance(c, Team)]

    def create_tournament(
        self,
        name: str,
        sport_id: str,
        blueprint_id: str,
        *,
        tournament_id: Optional[str] = None,
        match_config: Any = None,
    ) -> Tournament:
        tournament = Tournament.from_blueprint(
            name,
            sport_id,
            blueprint_id,
            tournament_id=tournament_id or str(uuid.uuid4()),
            match_config=match_config,
        )
        self.tournaments[tournament.id] = tournament
        for contest_id, match in tournament.matches.items():
            self.active_matches[contest_id] = match
        return tournament

    def register_active_match(self, match: Contest) -> None:
        self.active_matches[match.id] = match

    def get_match(self, match_id: str) -> Optional[Contest]:
        return self.active_matches.get(match_id)

    def archive_match(self, match_id: str) -> None:
        if match_id not in self.active_matches:
            raise ValueError(f"Match with ID '{match_id}' not found in active memory.")
        match = self.active_matches.pop(match_id)
        self.archived_matches[match.id] = match

    def dispatch_match_command(self, match_id: str, command: Command) -> None:
        match = self.get_match(match_id)
        if not match:
            raise ValueError(f"Match with ID '{match_id}' not found in active memory.")
        match.handle(command)

    def suspend_match(self, match_id: str) -> None:
        match = self.get_match(match_id)
        if match is None:
            raise ValueError(f"Match with ID '{match_id}' not found in active memory.")
        match.suspend()

    def setup_tournament(
        self,
        tournament: Tournament,
        entries: List[TournamentEntry],
    ) -> List[FixtureScheduled]:
        tournament.open_registration()
        for entry in entries:
            tournament.register_contestant(entry.contestant)
            if entry.player_ids:
                tournament.register_squad(entry.contestant.id, entry.player_ids)
        events = tournament.close_registration()
        for contest_id, match in tournament.matches.items():
            self.active_matches[contest_id] = match
        return [event for event in events if isinstance(event, FixtureScheduled)]

    def sync_match_discipline(self, tournament: Tournament, match: Contest) -> None:
        from src.sports.football.contest.football_contest_state import (
            FootballContestState,
        )

        state = match.current_state
        if isinstance(state, FootballContestState):
            match.current_state = state.with_tournament_context(
                suspended_player_ids=tournament.state.discipline.suspended_ids()
            )

    def complete_tournament_match(self, tournament: Tournament, match_id: str) -> None:
        match = self.get_match(match_id)
        if match is None:
            raise ValueError(f"Match with ID '{match_id}' not found in active memory.")
        if not match.current_state.is_finished:
            raise ValueError("Match is not completed.")
        result = match.get_official_result()
        events = tournament.handle(
            RecordMatchOutcome(contest_id=match_id, result=result)
        )
        for contest_id, contest in tournament.matches.items():
            if contest_id not in self.active_matches:
                self.active_matches[contest_id] = contest
        for event in events:
            if isinstance(event, FixtureScheduled):
                created = tournament.get_match(event.contest_id)
                if created is not None:
                    self.active_matches[event.contest_id] = created
