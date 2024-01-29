# Execute the actual game, starts the game and keep tracks of everything
# Import all other classes

import copy
import importlib.util
import random
import sys
import os
from src.game_state import GameState
from src.robot_controller import RobotController
from src.game_constants import Team, GameConstants, TowerType, get_debris_schedule
from src.player import Player
from src.map import Map
from src.replay import Replay
from threading import Thread
import time

def import_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module

class Game:
    def __init__(self, blue_path: str, red_path: str, map_path: str, output_replay=False, render=False):
        self.output_replay = output_replay
        self.render = render

        # initialize map
        self.map = Map(map_path)

        # initialize game_state
        self.gs = GameState(self.map)

        # initialize players
        self.blue_failed_init = False
        try:
            blue_bot_name = os.path.basename(blue_path).split(".")[0]
            self.blue_player: Player = import_file(blue_bot_name, blue_path).BotPlayer(copy.deepcopy(self.map))
        except:
            blue_bot_name = "blue"
            self.blue_failed_init = True

        self.red_failed_init = False
        try:
            red_bot_name = os.path.basename(red_path).split(".")[0]
            self.red_player: Player = import_file(red_bot_name, red_path).BotPlayer(copy.deepcopy(self.map))
        except:
            red_bot_name = "red"
            self.red_failed_init = True

        # initialize replay
        self.game_name = f"{blue_bot_name}-{red_bot_name}-{self.map.name}"
        self.replay = Replay(
            self.game_name,
            self.map,
            blue_bot_name,
            red_bot_name
        )

        # initialize controllers
        self.blue_controller = RobotController(Team.BLUE, self.gs)
        self.red_controller = RobotController(Team.RED, self.gs)
        
    def run_turn(self):
        self.gs.start_turn()

        # Spawn natural debris
        debris = get_debris_schedule(self.gs.turn)
        if debris is not None:
            cooldown, health = debris
            self.gs.spawn_debris(Team.BLUE, cooldown, health, False)
            self.gs.spawn_debris(Team.RED, cooldown, health, False)

        # Spawn debris sent by players in previous turn
        if self.gs.sent_debris[Team.BLUE] is not None:
            cooldown, health = self.gs.sent_debris[Team.BLUE]
            self.gs.spawn_debris(Team.RED, cooldown, health, True)
            self.gs.sent_debris[Team.BLUE] = None
        if self.gs.sent_debris[Team.RED] is not None:
            cooldown, health = self.gs.sent_debris[Team.RED]
            self.gs.spawn_debris(Team.BLUE, cooldown, health, True)
            self.gs.sent_debris[Team.RED] = None

        # Generate passive income for each player
        self.gs.balance[Team.BLUE] += GameConstants.PASSIVE_INCOME
        self.gs.balance[Team.RED] += GameConstants.PASSIVE_INCOME

        # Decrement all debris/tower cooldowns
        all_debris = list(self.gs.debris[Team.BLUE].values()) + list(self.gs.debris[Team.RED].values())
        for debris in all_debris:
            debris.current_cooldown = max(0, debris.current_cooldown - 1)
        all_towers = list(self.gs.towers[Team.BLUE].values()) + list(self.gs.towers[Team.RED].values())
        for tower in all_towers:
            reduction = self.gs.get_tower_cooldown_reduction(tower.team, tower.id)
            tower.current_cooldown = max(0, tower.current_cooldown - reduction)

        # Advance all debris
        self.gs.advance_debris()

        # Check if game is over
        if self.gs.health[Team.BLUE] == 0 or self.gs.health[Team.RED] == 0:
            return self.calculate_winner()
        
        # Add time to each player
        self.gs.time_remaining[Team.BLUE] += GameConstants.ADDITIONAL_TIME_PER_TURN
        self.gs.time_remaining[Team.RED] += GameConstants.ADDITIONAL_TIME_PER_TURN

        # Farms generate income
        for team in [Team.BLUE, Team.RED]:
            for tower in self.gs.towers[team].values():
                if tower.type == TowerType.SOLAR_FARM:
                    if tower.current_cooldown == 0:
                        self.gs.balance[team] += GameConstants.FARM_INCOME
                        tower.current_cooldown = TowerType.SOLAR_FARM.cooldown

        # Call each player's play_turn
        blue_success = self.call_player_code(Team.BLUE)
        red_success = self.call_player_code(Team.RED)

        if not blue_success and not blue_success:  # Both failed
            return self.calculate_winner()
        if not blue_success:
            return Team.RED
        if not red_success:
            return Team.BLUE

        return None
    
    def call_player_code(self, team: Team):
        player = self.blue_player if team == Team.BLUE else self.red_player
        controller = self.blue_controller if team == Team.BLUE else self.red_controller

        # Create a thread that runs player.play_turn.
        # This function might not exist if the player code is broken, so we need to handle that.
        try:
            thread = Thread(target=player.play_turn, args=[controller], daemon=True)
        except:
            print(f"Failed to call player code for {team}. Are you inheriting the Player class?")
            return False

        # Run in separate thread with time limit
        funcTime = time.time()
        thread.start()
        thread.join(self.gs.time_remaining[team])
        funcTime = time.time() - funcTime

        # Check if thread timed out
        if thread.is_alive() or funcTime > self.gs.time_remaining[team]:
            self.gs.time_remaining[team] = 0
            return False
        
        self.gs.time_remaining[team] -= funcTime
        return True
    
    def calculate_winner(self):
        # Check if one team has more health than the other
        if self.gs.health[Team.BLUE] != self.gs.health[Team.RED]:
            if self.gs.health[Team.BLUE] < self.gs.health[Team.RED]:  # more health wins
                return Team.RED
            else:
                return Team.BLUE

        # Break ties by total balance + tower costs
        values = {Team.BLUE: self.gs.balance[Team.BLUE], Team.RED: self.gs.balance[Team.RED]}
        for team in Team:
            for tower in self.gs.towers[team].values():
                values[team] += tower.type.cost
        if values[Team.BLUE] != values[Team.RED]:
            if values[Team.BLUE] < values[Team.RED]:
                return Team.RED
            else:
                return Team.BLUE
        
        # Winner is decided by coin flip
        return random.choice([Team.BLUE, Team.RED])
    
    def run_game(self):
        # Check if we initialized successfully
        if self.blue_failed_init:
            print("Blue failed to initialize. Red wins.")
            return Team.RED
        elif self.red_failed_init:
            print("Red failed to initialize. Blue wins.")
            return Team.BLUE

        # Both players initialized successfully; we can start the game
        while(True):
            if self.render:
                self.gs.render()
            winner = self.run_turn()
            self.replay.add_turn(self.gs)
            if winner is not None:
                self.replay.set_winner(winner)
                self.replay.write_json()
                return winner
