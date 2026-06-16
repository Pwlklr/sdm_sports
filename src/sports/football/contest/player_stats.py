from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class FootballPlayerStats:
    player_id: str
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    dismissed: bool = False

    @property
    def subject_id(self) -> str:
        return self.player_id

    def with_goal(self) -> FootballPlayerStats:
        return FootballPlayerStats(
            player_id=self.player_id,
            goals=self.goals + 1,
            assists=self.assists,
            yellow_cards=self.yellow_cards,
            dismissed=self.dismissed,
        )

    def with_goal_removed(self) -> FootballPlayerStats:
        return FootballPlayerStats(
            player_id=self.player_id,
            goals=max(self.goals - 1, 0),
            assists=self.assists,
            yellow_cards=self.yellow_cards,
            dismissed=self.dismissed,
        )

    def with_yellow(self) -> FootballPlayerStats:
        return FootballPlayerStats(
            player_id=self.player_id,
            goals=self.goals,
            assists=self.assists,
            yellow_cards=self.yellow_cards + 1,
            dismissed=self.dismissed,
        )

    def with_dismissed(self) -> FootballPlayerStats:
        return FootballPlayerStats(
            player_id=self.player_id,
            goals=self.goals,
            assists=self.assists,
            yellow_cards=self.yellow_cards,
            dismissed=True,
        )


def init_player_stats_for_teams(
    teams: tuple,
) -> dict[str, FootballPlayerStats]:
    stats: dict[str, FootballPlayerStats] = {}
    for team in teams:
        for player in team.roster:
            stats[player.id] = FootballPlayerStats(player_id=player.id)
    return stats
