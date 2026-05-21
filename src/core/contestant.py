from __future__ import annotations


class Contestant:
    contestant_id: str
    name: str

    def __init__(self, contestant_id: str, name: str) -> None:
        self.contestant_id = contestant_id
        self.name = name
