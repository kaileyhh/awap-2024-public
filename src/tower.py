from src.game_constants import Team, TowerType

class Tower:
    id_counter = 0

    def __init__(self, team: Team, type: TowerType, x: int, y: int):
        self.id = self.increment()
        self.team = team
        self.type = type
        self.x = x
        self.y = y
        self.current_cooldown = 1.0
    
    @staticmethod
    def increment() -> int:
        res = Tower.id_counter
        Tower.id_counter += 1
        return res
    