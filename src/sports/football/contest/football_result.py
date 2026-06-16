from __future__ import annotations

from dataclasses import dataclass

from src.core.contest.contest_result import ContestResult, RankedEntry
from src.core.contest.metrics import SideMetrics


@dataclass(frozen=True, kw_only=True)
class FootballPlayerMatchStats:
    """Player-level snapshot nested under a team side."""

    player_id: str
    goals: int
    yellow_cards: int
    dismissed: bool


@dataclass(frozen=True, kw_only=True)
class FootballTeamSideMetrics:
    team_id: str
    score: int
    penalty_score: int
    players: dict[str, FootballPlayerMatchStats]


@dataclass(frozen=True, kw_only=True)
class FootballSideMetrics(SideMetrics):
    by_team_id: dict[str, FootballTeamSideMetrics]
    decided_by: str = "regulation"

    @property
    def scores(self) -> dict[str, int]:
        return {team_id: team.score for team_id, team in self.by_team_id.items()}

    @property
    def penalty_scores(self) -> dict[str, int]:
        return {
            team_id: team.penalty_score for team_id, team in self.by_team_id.items()
        }

    def all_players(self) -> dict[str, FootballPlayerMatchStats]:
        merged: dict[str, FootballPlayerMatchStats] = {}
        for team in self.by_team_id.values():
            merged.update(team.players)
        return merged


@dataclass(frozen=True, kw_only=True)
class FootballResult(ContestResult):
    ranking_entries: tuple[RankedEntry, ...]
    side: FootballSideMetrics

    def is_finished(self) -> bool:
        return bool(self.ranking_entries)

    def ranking(self) -> tuple[RankedEntry, ...]:
        return self.ranking_entries

    def side_metrics(self) -> SideMetrics:
        return self.side

    @property
    def decided_by(self) -> str:
        return self.side.decided_by

    @property
    def scores(self) -> dict[str, int]:
        return self.side.scores
