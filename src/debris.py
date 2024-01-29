from __future__ import annotations
from src.game_constants import Team

class Debris:
    id_counter = 0

    def __init__(
            self,
            team: Team,
            x: int,
            y: int,
            cooldown: int,
            health: int,
            sent_by_opponent: bool
    ) -> None:
        self.id = self.increment()
        self.team = team
        self.progress = 0
        self.x = x
        self.y = y
        self.total_cooldown = cooldown
        self.current_cooldown = cooldown
        self.total_health = health
        self.health = health
        self.sent_by_opponent = sent_by_opponent
    
    @staticmethod
    def increment() -> int:
        res = Debris.id_counter
        Debris.id_counter += 1
        return res
