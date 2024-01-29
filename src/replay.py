from dataclasses import dataclass
import compress_json
from src.game_constants import Team, TowerType
from src.game_state import GameState
from src.map import Map
from typing import List

@dataclass
class ReplayTower:
    id: int
    type: str
    x: int
    y: int
    max_cooldown: int
    cooldown: float

@dataclass
class ReplayDebris:
    id: int
    x: int
    y: int
    max_health: int
    health: int
    max_cooldown: int
    cooldown: int
    sent_by_opponent: bool

@dataclass
class ReplayTurn:
    turn_number: int
    blue_balance: int
    red_balance: int
    blue_health: int
    red_health: int
    blue_time_remaining: float
    red_time_remaining: float
    blue_towers: List[dict]
    red_towers: List[dict]
    blue_debris: List[dict]
    red_debris: List[dict]
    blue_snipes: List[tuple] # ((x0, y0), (x1, y1))
    red_snipes: List[tuple]
    blue_bombs: List[tuple] # (x, y)
    red_bombs: List[tuple]

@dataclass
class ReplayMetadata:
    game_name: str
    map_name: str
    map_width: int
    map_height: int
    map_path: List[tuple]
    red_bot: str
    blue_bot: str
    winner: str
    scores: List[float]

class Replay:
    def __init__(
            self,
            game_name: str,
            map: Map,
            blue_bot: str,
            red_bot: str
    ):
        self.metadata = ReplayMetadata(
            game_name=game_name,
            map_name=map.name,
            map_width=map.height,
            map_height=map.height,
            map_path=map.path,
            blue_bot=blue_bot,
            red_bot=red_bot,
            winner="none",
            scores=[0.0, 0.0]
        )
        self.turns = []

    def add_turn(self, gs: GameState):
        turn = ReplayTurn(
            turn_number=gs.turn,
            blue_balance=gs.balance[Team.BLUE],
            red_balance=gs.balance[Team.RED],
            blue_health=gs.health[Team.BLUE],
            red_health=gs.health[Team.RED],
            blue_time_remaining=gs.time_remaining[Team.BLUE],
            red_time_remaining=gs.time_remaining[Team.RED],
            blue_towers=[],
            red_towers=[],
            blue_debris=[],
            red_debris=[],
            blue_snipes=gs.current_snipes[Team.BLUE],
            red_snipes=gs.current_snipes[Team.RED],
            blue_bombs=gs.current_bombs[Team.BLUE],
            red_bombs=gs.current_bombs[Team.RED]
        )
        # Add towers
        for team in [Team.BLUE, Team.RED]:
            for tower in gs.towers[team].values():
                tower_type = None
                if tower.type == TowerType.SOLAR_FARM:
                    tower_type = "solar_farm"
                elif tower.type == TowerType.GUNSHIP:
                    tower_type = "gunship"
                elif tower.type == TowerType.BOMBER:
                    tower_type = "bomber"
                elif tower.type == TowerType.REINFORCER:
                    tower_type = "reinforcer"
                else:
                    raise Exception("Unknown tower type in replay")
                replay_tower = ReplayTower(
                    id=tower.id,
                    type=tower_type,
                    x=tower.x,
                    y=tower.y,
                    max_cooldown=tower.type.cooldown,
                    cooldown=tower.current_cooldown
                )
                if team == Team.BLUE:
                    turn.blue_towers.append(replay_tower.__dict__)
                else:
                    turn.red_towers.append(replay_tower.__dict__)
        # Add debris
        for team in [Team.BLUE, Team.RED]:
            for deb in gs.debris[team].values():
                replay_deb = ReplayDebris(
                    id=deb.id,
                    x=deb.x,
                    y=deb.y,
                    max_health=deb.total_health,
                    health=deb.health,
                    max_cooldown=deb.total_cooldown,
                    cooldown=deb.current_cooldown,
                    sent_by_opponent=deb.sent_by_opponent
                )
                if team == Team.BLUE:
                    turn.blue_debris.append(replay_deb.__dict__)
                else:
                    turn.red_debris.append(replay_deb.__dict__)
        self.turns.append(turn.__dict__)

    def set_winner(self, winner: Team):
        if winner == Team.BLUE:
            self.metadata.winner = "blue"
            self.metadata.scores = [1.0, 0.0]
        else:
            self.metadata.winner = "red"
            self.metadata.scores = [0.0, 1.0]

    def write_json(self):
        res = {
            "metadata": self.metadata.__dict__,
            "turns": self.turns
        }
        compress_json.dump(res, f"replays/{self.metadata.game_name}.awap24r.gz")
