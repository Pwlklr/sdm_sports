from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.contestant_stats import ContestantStats
from src.core.contestant.models import Team


@dataclass(frozen=True, kw_only=True)
class FootballPlayerStats(ContestantStats):
    player_id: str
    goals: int = 0
    yellow_cards: int = 0
    dismissed: bool = False

    @property
    def subject_id(self) -> str:
        return self.player_id

    def with_goal(self) -> FootballPlayerStats:
        return FootballPlayerStats(
            player_id=self.player_id,
            goals=self.goals + 1,
            yellow_cards=self.yellow_cards,
            dismissed=self.dismissed,
        )

    def with_goal_removed(self) -> FootballPlayerStats:
        return FootballPlayerStats(
            player_id=self.player_id,
            goals=max(self.goals - 1, 0),
            yellow_cards=self.yellow_cards,
            dismissed=self.dismissed,
        )

    def with_yellow(self) -> FootballPlayerStats:
        return FootballPlayerStats(
            player_id=self.player_id,
            goals=self.goals,
            yellow_cards=self.yellow_cards + 1,
            dismissed=self.dismissed,
        )

    def with_dismissed(self) -> FootballPlayerStats:
        return FootballPlayerStats(
            player_id=self.player_id,
            goals=self.goals,
            yellow_cards=self.yellow_cards,
            dismissed=True,
        )


def init_player_stats_for_teams(
    teams: tuple[Team, Team],
) -> dict[str, FootballPlayerStats]:
    stats: dict[str, FootballPlayerStats] = {}
    for team in teams:
        for player in team.roster:
            stats[player.id] = FootballPlayerStats(player_id=player.id)
    return stats
