from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower
 

def ceil(n):
    return int(-1 * n // 1 * -1)


class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.height = map.height
        self.width = map.width
        self.path = map.path

        self.distances = self.calculate_distance()
        self.bomber_list = self.calculate_bomber()
        self.sniper_list = self.calculate_sniper()
        self.solar_list = self.calculate_solar()
        self.asteroids = self.calculate_asteroids()
        self.blanks = self.calculate_blanks()

        self.bomber_count = 0
        self.sniper_count = 0
        self.solar_count = 0
        self.reinforcer_count = 0

        self.team = None
        self.enemy_team = None

        self.enemy_hp = 2500
        self.enemy_hp_prev = [2500] * 201
        self.hp = 2500
        self.hp_prev = [2500] * 201

        self.h = 101
        self.c = 4

        self.prev_wealth = 1500
        self.curr_wealth = self.prev_wealth
        self.post_rush_spaces = []

        self.should_rush_prev = 0
        self.boostdebris = 0
        self.rebuilding = False
        self.rushing = False
        self.almostboss = False

    
    # ---- init functions ---- #
    def calculate_distance(self):
        distances = []
        for i in range(self.width):
            distances.append([])
            for j in range(self.height):
                curmin = 10000
                for (x,y) in self.map.path:
                    curmin = min((abs(i-x)**2 + abs(j-y)**2)**(1/2), curmin) 
                distances[i].append(curmin)
        return distances

    
    def calculate_bomber(self):
        bomber_list = []
        self.bomber_arr = []
        for i in range(self.width):
            self.bomber_arr.append([])
            for j in range(self.height):
                if self.map.is_space(i, j):
                    tmpCount = 0

                    for k in range(7):
                        for l in range(7):
                            newX = i - 3 + k
                            newY = j - 3 + l 
                            if (newX - i) * (newX - i) + (newY - j) * (newY - j) < 10:
                                if self.map.is_path(newX, newY):
                                    tmpCount += 1

                    bomber_list.append((tmpCount, i, j))
                    self.bomber_arr[i].append(tmpCount)
                else:
                    self.bomber_arr[i].append(0)

        bomber_list.sort(key=lambda x: x[0], reverse=True)

        return bomber_list

    
    def calculate_sniper(self):
        sniper_list = []
        self.sniper_arr = []
        for i in range(self.width):
            self.sniper_arr.append([])
            for j in range(self.height):
                if self.map.is_space(i, j):
                    tmpCount = 0

                    for k in range(15):
                        for l in range(15):
                            newX = i - 7 + k
                            newY = j - 7 + l 
                            if (newX - i) * (newX - i) + (newY - j) * (newY - j) < 60:

                                if self.map.is_path(newX, newY):
                                    tmpCount += 1
                    sniper_list.append((tmpCount, i, j))
                    self.sniper_arr[i].append(tmpCount)
                else:
                    self.sniper_arr[i].append(0)

        sniper_list.sort(key=lambda x: x[0], reverse=True)

        return sniper_list
    
    def calculate_solar(self):
        solar_list = []
        for i in self.calculate_sniper():
            solar_list.append(i)
        return solar_list

    def calculate_asteroids(self):
        asteroid = []
        for i in range(self.width):
            for j in range(self.height):
                if (self.map.is_asteroid(i, j)):
                    asteroid.append([i, j])
        return asteroid
    
    def calculate_blanks(self):
        space = []
        for i in range(self.width):
            for j in range(self.height):
                if (self.map.is_space(i, j)):
                    space.append([i, j])
        return space
    
    # ---- init functions ---- #

    # ---- turn ---- #

    def play_turn(self, rc: RobotController):
        self.update_vals(rc)

        # try to rush:
        rusherc = self.should_rush(rc)
        if rusherc != 0:
            self.rush(rc,rusherc)
            # print("Rushing ", rusherc, " with health ", self.black_magic(rc, rusherc))
            # self.rush(rc,rusherc)
            self.towers_attack(rc)
            return
        
       
        if (self.should_rush(rc) != 0):
            # print("Rushing")
            if (len(self.post_rush_spaces) == 0):
                self.post_rush_spaces = self.sell_all_farms(rc)
            self.rush(rc,self.should_rush_prev)
            # self.rushing = True
            # self.should_rush_prev = True

        else:
            # print("Defending")
            # play as if safe, develop economy
            # print(self.is_safe(rc))
            if self.should_farm(rc):
                self.build_solar(rc)
            elif (self.bomb_is_desirable(rc) and len(self.bomber_list) > 0):
                self.build_bomber(rc)
            elif (len(self.sniper_list) > 0):
                self.build_sniper(rc)
            elif (len(self.bomber_list) > 0):
                self.build_bomber(rc)
            else:
                print("board should be full")

        self.towers_attack(rc)

    def update_vals(self, rc):
        # update the values used elsewhere, to track self and enemy state
        if self.team == None:
            self.team = rc.get_ally_team()
        if self.enemy_team == None:
            self.enemy_team = rc.get_enemy_team()
        
        
        self.prev_wealth = self.curr_wealth
        self.curr_wealth = rc.get_balance(self.team)

        self.hp_prev.pop(0)
        self.hp_prev.append(self.hp)
        self.enemy_hp_prev.pop(0)
        self.enemy_hp_prev.append(self.enemy_hp)

        self.hp = rc.get_health(self.team)
        self.enemy_hp = rc.get_health(self.enemy_team)

        turn = rc.get_turn()

        # Sync up with the calculated boss cycles of Nature
        if((1500 < turn and turn < 1550) or (3000 < turn and turn < 3050)
           or (turn > 3750 & turn%200 <= 100)):
            self.almostboss = True

    # Unused, theoretically can repopulate towers that go from farm to gunship after a rush doesn't work
    def rebuild(self, rc):
        if (len (self.post_rush_spaces) == 0):
            self.rebuilding = False
            return
        tile = self.post_rush_spaces[0]
        while len (self.post_rush_spaces) > 0:
            if (rc.can_build_tower(TowerType.SOLAR_FARM, tile[0], tile[1])):
                rc.build_tower(TowerType.SOLAR_FARM, tile[0], tile[1])
                if (len (self.post_rush_spaces) > 1):
                    tile = self.post_rush_spaces[1]
                self.post_rush_spaces.pop(0)
        
        if (len (self.post_rush_spaces) == 0):
            self.rebuilding = False
    
    # def opponent_rushing(self, rc):
    #     debris = rc.get_debris(self.team)
    #     for d in debris:
    #         if d.sent_by_opponent:
    #             return True
    #     return False


    def should_rush(self, rc): # returns a positive int cooldown if should rush, otherwise returns 0
        if (rc.get_turn() < 150):
            self.should_rush_prev = 0
            return 0
        
        # print("bomber list: ", len(self.bomber_list), " and sniper list: ", len(self.sniper_list), " and blanks: ", len(self.blanks))
        if (rc.get_turn() % 100 == 0):
            # self.should_rush_prev = 0
            if (self.rushing == True and self.enemy_hp == self.enemy_hp_prev[-200]): # REPLACE WITH 2*50*c
                print("rush limiter")
                self.boostdebris += 10
                self.rushing = False
                self.should_rush_prev = 0

            elif (len(self.map.path) <= 30):
                print("path rushing")
                self.rushing = True
                self.should_rush_prev = 4

            elif self.almostboss and len(self.bomber_list) + len(self.sniper_list) <= len(self.blanks):
                print("full rushing")
                self.rushing = True
                self.should_rush_prev = 4
        
        
        # if they rush sand we have worse defense, build defense?

        # if they rush and we have stronger defenses and stronger economy, build defense to match their economy then rush?
        if self.opponent_rushing(rc) and self.stronger(rc)[0] and self.stronger(rc)[1] and not self.rushing:
            print("retaliation rushing")
            self.rushing = True
            self.should_rush_prev = 1
            # return self.should_rush_prev
        
        
        return self.should_rush_prev


    def stronger(self, rc): 
        # return a pair of booleans (stronger economy, stronger defense) for APPROXIMATE enemy defense and economy (ignores reinforcers)
        enemy_defense = rc.get_towers(self.enemy_team)
        numbombers = 0
        numsnipers = 0
        numfarms = 0
        for t in enemy_defense:
            if t.type == TowerType.BOMBER:
                numbombers += 1
            elif t.type == TowerType.GUNSHIP:
                numsnipers += 1
            elif t.type == TowerType.SOLAR_FARM:
                numfarms += 1
        stronger_defense = self.defense_dpt_heuristic(rc) >= numbombers * TowerType.BOMBER.damage * 5 + numsnipers * TowerType.GUNSHIP.damage * 3
        stronger_income = 10 + 2 * self.solar_count >= 10 + 2 * numfarms
        return (stronger_income, stronger_defense)
        
    def get_total_offensive(self):
        return self.bomber_count + self.sniper_count
    
    def bomb_is_desirable(self, rc):
        return self.is_safe(rc)

    
    def debris_damage_needed(self, rc: RobotController):
        debris = rc.get_debris(rc.get_ally_team())
        hp = 0
        numballoons = 0
        for d in debris:
            hp = hp + d.health**2
            numballoons = numballoons + 1
        if (numballoons == 0):
            return 0
        hp = hp // numballoons
        return hp
    
    def defense_dpt_heuristic(self,rc):
        return self.bomber_count * TowerType.BOMBER.damage * 5 + self.sniper_count * TowerType.GUNSHIP.damage * 3

    def is_safe(self, rc):
        avg = self.debris_damage_needed(rc) ** (1/2)
        return avg <= self.defense_dpt_heuristic(rc)
    
    def should_farm(self, rc):
        # print("farm: ", self.is_safe(rc) and self.get_total_offensive() > int(0.2 * self.solar_count))
        return self.is_safe(rc) and self.bomber_count > int(0.2 * self.solar_count) and len(self.sniper_list) > 0

    # ---- turn ---- #
            
    # ---- build functions ---- #
    
    def build_bomber(self, rc):
        if (len(self.bomber_list) < 1):
            return False
        
        top = self.bomber_list[0]
        while (not rc.is_placeable(self.team, top[1], top[2]) or top[0] == 0):
            self.bomber_list.pop(0)
            if (len(self.bomber_list) == 0):
                return False
            top = self.bomber_list[0]
        
        if (rc.can_build_tower(TowerType.BOMBER, top[1], top[2])):
            self.bomber_list.pop(0)
            rc.build_tower(TowerType.BOMBER, top[1], top[2])
            self.bomber_count += 1
            return True
        
        return False
    
    def build_sniper(self, rc):
        if (len(self.sniper_list) < 1):
            return False
        
        top = self.sniper_list[0]
        while (not rc.is_placeable(self.team, top[1], top[2]) or top[0] == 0):
            self.sniper_list.pop(0)
            if (len(self.sniper_list) == 0):
                return False
            top = self.sniper_list[0]
        
        if (rc.can_build_tower(TowerType.GUNSHIP, top[1], top[2])):
            density = rc.sense_towers_within_radius_squared(self.team, top[1], top[2], 5)
            sniper_density = [i for i in density if i.type == TowerType.GUNSHIP]
            reinforcer_density = [i for i in density if i.type == TowerType.REINFORCER]

            if len(sniper_density) >= 3 and (len(reinforcer_density) == 0) and (self.reinforcer_count * 6 < self.sniper_count):
                if (rc.can_build_tower(TowerType.BOMBER, top[1], top[2])):
                    self.sniper_list.pop(0)
                    rc.build_tower(TowerType.GUNSHIP, top[1], top[2])
                    self.sniper_count += 1
                    return True
            else:
                self.sniper_list.pop(0)
                rc.build_tower(TowerType.GUNSHIP, top[1], top[2])
                self.sniper_count += 1

        return False
    
    def build_solar(self, rc): 
        if (len(self.solar_list) < 1):
            return False 
        top = self.solar_list[-1]
        while (not rc.is_placeable(self.team, top[1], top[2])):
            self.solar_list.pop()
            if (len(self.solar_list) == 0):
                return False
            top = self.solar_list[-1]
        
        if (rc.can_build_tower(TowerType.SOLAR_FARM, top[1], top[2])):                

            density = rc.sense_towers_within_radius_squared(self.team, top[1], top[2], 5)
            solar_density = [i for i in density if i.type == TowerType.SOLAR_FARM]
            reinforcer_density = [i for i in density if i.type == TowerType.REINFORCER]

            if len(solar_density) >= 3 and len(reinforcer_density) == 0 and self.reinforcer_count * 6 < self.solar_count and self.solar_count >= 10:
                if rc.can_build_tower(TowerType.REINFORCER, top[1], top[2]):
                    rc.build_tower(TowerType.REINFORCER, top[1], top[2])
                    self.solar_list.pop()
                    self.reinforcer_count += 1 
            else:
                self.solar_list.pop()
                rc.build_tower(TowerType.SOLAR_FARM, top[1], top[2])
                self.solar_count += 1
                return True

    # ---- build functions ---- #

    # ---- attack functions ---- #

    def towers_attack(self, rc):
        towers = rc.get_towers(self.team)

        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)

    # ---- attack functions ---- #

    # ---- rushing ---- #

    def rush(self, rc, c):
        self.c = c
        # (self.h, turnsNeeded) = self.black_magic(rc, c)
        
        # if turnsNeeded > 800:
        #     return

        if rc.can_send_debris(4,101): # calculated best value + 1 so that it takes a whole other attack to kill
            rc.send_debris(4,101)
        # if rc.can_send_debris(self.c,self.h + self.boostdebris):
        #     rc.send_debris(self.c,self.h + self.boostdebris)
        # else:
        #     print("nooooooo too poor rip debris")


    def opponent_rushing(self, rc):
        debris = rc.get_debris(self.team)
        return len([d for d in debris if d.sent_by_opponent]) > 0

    def cost(self, c, h):
        if h/c <= 30:
            return max(ceil((h**2/c)/12),200)
        elif h/c <= 80:
            return max(ceil(h**2/(12*c)),200)
        elif h/c <= 120:
            return max(ceil(h**1.9/(8*c)),200)
        return max(ceil(h**1.8/(4.6*c)),200)

    def black_magic(self, rc, c):
        res = 5000 # panic magic number
        best_hp = 601 # 1 mod 25, also magic number
        for hp in range(25*int(self.compute_damage(rc, c)/25)+1, 601, 25): # some magic
            seconds = max(1, int(self.cost(c, hp)/(self.solar_count * 2 + 10))) * ceil( ( self.enemy_hp - int(self.curr_wealth) * hp )/hp) + 50 * c
            if seconds < res and self.cost(c,hp) <= 8*(2*self.solar_count+10):
                res = seconds
                best_hp = hp
        
        return (best_hp, res)

    def compute_damage(self, rc, cooldown):
        dmg = 0

        for tower in rc.get_towers(self.enemy_team):
            bombTiles = self.bomber_arr[tower.x][tower.y]
            sniperTiles = self.sniper_arr[tower.x][tower.y]

            if tower.type == TowerType.BOMBER:
                dmg += 6 * ceil(bombTiles * cooldown / 15)
            elif tower.type == TowerType.GUNSHIP:
                dmg += 25 * ceil(sniperTiles * cooldown / 20) / 3
        
        return dmg

    def compute_optimal_dps(self, rc):
        result = -1
        result_hp = -1
        result_cd = -1

        for cd in range(1, 5):
            best = 0
            for hp in range(26, 801, 25):
                if self.cost(cd, hp) < self.curr_wealth:
                    best = hp
                else:
                    break
            if self.cost(cd, best) > result:
                result = self.cost(cd,best)
                result_hp = best
                result_cd = cd
        

        return (result_cd, result_hp)
            

    def sell_all_farms(self, rc): # Sells not all the farms
        towers = rc.get_towers(rc.get_ally_team())
        temp = []
        for tower in towers:
            temp.append(tower)

        spaces = []
        
        for tower in temp:
            if (tower.type == TowerType.SOLAR_FARM):
                x = tower.x 
                y = tower.y
                print(self.distances[x][y])
                if (self.distances[x][y] < 8):
                    rc.sell_tower(tower.id)
                    rc.build_tower(TowerType.GUNSHIP, x, y) 
                    self.sniper_count += 1  
                else:
                    spaces.append([x, y])

            elif (tower.type == TowerType.REINFORCER):
                x = tower.x 
                y = tower.y
                if (self.distances[x][y] >= 8):
                    rc.sell_tower(tower.id)   
                    spaces.append([x, y])    

        return spaces
