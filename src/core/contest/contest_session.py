from __future__ import annotations

from enum import Enum


class ContestSessionStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUSPENDED = "suspended"
    FINISHED = "finished"


def session_status_label(status: ContestSessionStatus) -> str:
    return {
        ContestSessionStatus.NOT_STARTED: "not started",
        ContestSessionStatus.IN_PROGRESS: "in progress",
        ContestSessionStatus.SUSPENDED: "suspended",
        ContestSessionStatus.FINISHED: "finished",
    }[status]
