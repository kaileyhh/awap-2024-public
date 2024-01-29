import copy
from typing import List
import math

from src.debris import Debris
from src.game_exception import GameException
from src.game_constants import SnipePriority, Team, TowerType, GameConstants
from src.game_state import GameState
from src.tower import Tower

class RobotController:
    def __init__(self, team: Team, game_state: GameState):
        self.__team = team
        self.__gs = game_state
    
    def get_ally_team(self) -> Team:
        return self.__team
    
    def get_enemy_team(self) -> Team:
        if self.__team == Team.BLUE:
            return Team.RED
        else:
            return Team.BLUE
    
    def get_map(self) -> list:
        return copy.deepcopy(self.__gs.map)
    
    def get_towers(self, team: Team) -> List[Tower]:
        return copy.deepcopy(list(self.__gs.towers[team].values()))
    
    def get_debris(self, team: Team) -> List[Debris]:
        return copy.deepcopy(list(self.__gs.debris[team].values()))

    def sense_debris_within_radius_squared(self, team: Team, x: int, y: int, r2: int) -> List[Debris]:
        inRange: List[Debris] = []
        for deb in self.__gs.debris[team].values():
            if (deb.x - x)**2 + (deb.y - y)**2 <= r2:
                inRange.append(copy.deepcopy(deb))

        return inRange

    def sense_debris_in_range_of_tower(self, team: Team, tower_id: int) -> List[Debris]:
        if tower_id not in self.__gs.towers[team]:
            raise GameException(f"Tried to sense debris in range of non-existent tower: {tower_id}")
        tower = self.__gs.towers[team][tower_id]
        return self.sense_debris_within_radius_squared(team, tower.x, tower.y, tower.type.range)

    def sense_towers_within_radius_squared(self, team: Team, x: int, y: int, r2: int) -> List[Tower]:
        inRange: List[Tower] = []
        for tower in self.__gs.towers[team].values():
            if (tower.x - x)**2 + (tower.y - y)**2 <= r2:
                inRange.append(copy.deepcopy(tower))

        return inRange

    def sense_towers_in_range_of_tower(self, team: Team, tower_id: int) -> List[Tower]:
        if tower_id not in self.__gs.towers[team]:
            raise GameException(f"Tried to sense towers in range of non-existent tower: {tower_id}")
        tower = self.__gs.towers[team][tower_id]
        return self.sense_towers_within_radius_squared(team, tower.x, tower.y, tower.type.range)
    
    def get_balance(self, team: Team) -> int:
        return self.__gs.balance[team]
    
    def get_health(self, team: Team) -> int:
        return self.__gs.health[team]
    
    def get_turn(self) -> int:
        return self.__gs.turn
    
    def get_debris_cost(self, cooldown: int, health: int) -> int:
        power = health/cooldown
        v1 = math.ceil(1/12 * health**2 / cooldown)
        v2 = math.ceil(1/8 * health**1.9 / cooldown)
        v3 = math.ceil(1/4.6 * health**1.8 / cooldown)
        v4 = math.ceil(1/2 * health**1.6 / cooldown)

        if power <= 30:
            res = v1
        elif power <= 80:
            res = max(v1, v2)
        elif power <= 120:
            res = max(v2, v3)
        else:
            res = max(v3, v4)
        return max(res, 200)
    
    def can_send_debris(self, cooldown: int, health: int) -> bool:
        if self.__gs.sent_debris[self.__team] is not None:
            return False
        if self.__gs.balance[self.__team] < self.get_debris_cost(cooldown, health):
            return False
        if type(cooldown) != int or type(health) != int:
            return False
        if cooldown <= 0 or health <= 0:
            return False
        return True
    
    def send_debris(self, cooldown: int, health: int):
        if not self.can_send_debris(cooldown, health):
            raise GameException("send_debris() called but can_send_debris() returned False")
        self.__gs.balance[self.__team] -= self.get_debris_cost(cooldown, health)
        self.__gs.sent_debris[self.__team] = (cooldown, health)
    
    def is_placeable(self, team: Team, x: int, y: int) -> bool:
        if type(x) != int or type(y) != int:
            raise GameException("x and y must be integers (and can't be numpy.int64)")
        return self.__gs.is_placeable(team, x, y)
    
    def can_build_tower(self, tower_type: TowerType, x: int, y: int) -> bool:
        if self.__gs.balance[self.__team] < tower_type.cost:
            return False
        if type(x) != int or type(y) != int:
            raise GameException("x and y must be integers (and can't be numpy.int64)")
        return self.is_placeable(self.__team, x, y)
    
    def build_tower(self, tower_type: TowerType, x: int, y: int):
        if not self.can_build_tower(tower_type, x, y):
            raise GameException("build_tower() called but can_build_tower() returned False")
        tower = Tower(self.__team, tower_type, x, y)
        self.__gs.towers[self.__team][tower.id] = tower
        self.__gs.balance[self.__team] -= tower_type.cost

    def sell_tower(self, tower_id: int):
        my_towers = self.__gs.towers[self.__team]
        if tower_id not in my_towers:
            raise GameException("Cannot sell tower that doesn't exist")
        cost = my_towers[tower_id].type.cost
        self.__gs.balance[self.__team] += cost * GameConstants.REFUND_RATIO
        del self.__gs.towers[self.__team][tower_id]
    
    def get_time_remaining_at_start_of_turn(self, team: Team) -> float:
        return self.__gs.time_remaining[team]
    
    def can_snipe(self, tower_id: int, debris_id: int) -> bool:
        my_towers = self.__gs.towers[self.__team]
        my_debris = self.__gs.debris[self.__team]
        
        # Are the ids valid?
        if tower_id not in my_towers:
            raise GameException("can_snipe(): Invalid tower id")
        if debris_id not in my_debris:
            raise GameException("can_snipe(): Invalid debris id")
        
        tower = my_towers[tower_id]
        debris = my_debris[debris_id]

        # Is the tower a gunship?
        if tower.type != TowerType.GUNSHIP:
            raise GameException("can_snipe(): Tower is not a gunship")

        # Is the cooldown over?
        if tower.current_cooldown > 0:
            return False
        
        # Is the debris in range?
        dx = debris.x - tower.x
        dy = debris.y - tower.y
        if dx**2 + dy**2 > TowerType.GUNSHIP.range:
            return False
        
        return True
    
    def snipe(self, tower_id: int, debris_id: int):
        if not self.can_snipe(tower_id, debris_id):
            raise GameException("snipe() called but can_snipe() returned False")

        tower = self.__gs.towers[self.__team][tower_id]
        debris = self.__gs.debris[self.__team][debris_id]

        tower.current_cooldown = TowerType.GUNSHIP.cooldown

        self.__gs.current_snipes[self.__team].append(((tower.x, tower.y), (debris.x, debris.y)))
        self.__gs.damage_debris(debris_id, TowerType.GUNSHIP.damage)
    
    def auto_snipe(self, tower_id: int, priority: SnipePriority):
        if tower_id not in self.__gs.towers[self.__team]:
            raise GameException("auto_snipe(): Invalid tower id")
        tower = self.__gs.towers[self.__team][tower_id]
        if tower.type != TowerType.GUNSHIP:
            raise GameException("Auto sniping only works on Gunships")

        # Get list of snipeable debris
        debris = []
        for deb in self.__gs.debris[self.__team].values():
            if self.can_snipe(tower_id, deb.id):
                debris.append(deb)
        
        if len(debris) == 0:
            return
        
        if priority == SnipePriority.FIRST:
            get_priority = lambda debris: debris.progress
        elif priority == SnipePriority.LAST:
            get_priority = lambda debris: -debris.progress
        elif priority == SnipePriority.CLOSE:
            get_priority = lambda debris: -(debris.x - tower.x)**2 - (debris.y - tower.y)**2
        elif priority == SnipePriority.WEAK:
            get_priority = lambda debris: -debris.total_health
        elif priority == SnipePriority.STRONG:
            get_priority = lambda debris: debris.total_health
        else:
            raise GameException("Invalid priority passed to auto_snipe")
        highest_priority = max(debris, key=get_priority)
        self.snipe(tower_id, highest_priority.id)
    
    def can_bomb(self, tower_id: int):
        my_towers = self.__gs.towers[self.__team]

        if tower_id not in my_towers:
            raise GameException("Invalid tower id")
        tower = my_towers[tower_id]
        if tower.type != TowerType.BOMBER:
            raise GameException("Tower is not a bomber")

        if tower.current_cooldown > 0:
            return False
        return True
    
    def bomb(self, tower_id: int):
        if not self.can_bomb(tower_id):
            raise GameException("Cannot bomb")
        
        tower = self.__gs.towers[self.__team][tower_id]

        tower.current_cooldown = TowerType.BOMBER.cooldown

        self.__gs.current_bombs[self.__team].append((tower.x, tower.y))
        ids_in_range = []
        for deb in self.__gs.debris[self.__team].values():
            distance = (tower.x - deb.x)**2 + (tower.y - deb.y)**2
            if distance <= TowerType.BOMBER.range:
                ids_in_range.append(deb.id)
        for deb_id in ids_in_range:
            self.__gs.damage_debris(deb_id, TowerType.BOMBER.damage)
    
    def auto_bomb(self, tower_id: int):
        if tower_id not in self.__gs.towers[self.__team]:
            raise GameException("Invalid tower id")
        tower = self.__gs.towers[self.__team][tower_id]

        if not self.can_bomb(tower_id):
            return
        
        nearby_debris = self.sense_debris_in_range_of_tower(self.__team, tower_id)
        if len(nearby_debris) == 0:
            return
        
        self.bomb(tower_id)
