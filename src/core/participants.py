from typing import List

class Contestant:
    def __init__(self, contestant_id: str, name: str):
        self.contestant_id = contestant_id
        self.name = name

class Team:
    def __init__(self, team_id: str, name: str):
        self.team_id = team_id
        self.name = name
        self.members: List[Contestant] = []

    def add_member(self, contestant: Contestant) -> None:
        self.members.append(contestant)
        
    def remove_member(self, contestant: Contestant) -> None:
        if contestant in self.members:
            self.members.remove(contestant)