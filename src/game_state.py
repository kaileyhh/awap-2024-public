from __future__ import annotations
import math

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from src.game_constants import GameConstants, Team, Tile, TowerType
from src.map import Map
from src.debris import Debris

class GameState:
    def __init__(self, map: Map):
        self.map = map
        self.towers = {Team.BLUE: {}, Team.RED: {}}
        self.debris = {Team.BLUE: {}, Team.RED: {}}
        self.time_remaining = {Team.BLUE: GameConstants.INITIAL_TIME_POOL, Team.RED: GameConstants.INITIAL_TIME_POOL}
        self.balance = {Team.BLUE: GameConstants.STARTING_BALANCE, Team.RED: GameConstants.STARTING_BALANCE}
        self.health = {Team.BLUE: GameConstants.STARTING_HEALTH, Team.RED: GameConstants.STARTING_HEALTH}
        self.current_snipes = {Team.BLUE: [], Team.RED: []}
        self.current_bombs = {Team.BLUE: [], Team.RED: []}
        self.turn = 0
        self.has_rendered = False
        self.sent_debris = {Team.BLUE: None, Team.RED: None}

    def start_turn(self):
        self.current_snipes = {Team.BLUE: [], Team.RED: []}
        self.current_bombs = {Team.BLUE: [], Team.RED: []}
        self.turn += 1
    
    def spawn_debris(self, team: Team, cooldown: int, health: int, sent_by_opponent: bool):
        loc = self.map.path[0]
        debris = Debris(team, loc[0], loc[1], cooldown, health, sent_by_opponent)
        self.debris[team][debris.id] = debris

    def is_placeable(self, team: Team, x: int, y: int) -> bool:
        if not self.map.is_space(x, y):
            return False
        for tower in self.towers[team].values():
            if (tower.x, tower.y) == (x, y):
                return False
        return True
    
    def damage_debris(self, debris_id: int, damage: int):
        team = None
        if debris_id in self.debris[Team.BLUE]:
            team = Team.BLUE
        elif debris_id in self.debris[Team.RED]:
            team = Team.RED
        if team is None:
            raise Exception("Bug in game engine. Tried to damage non-existent debris.")
        
        self.debris[team][debris_id].health -= damage
        if self.debris[team][debris_id].health <= 0:
            del self.debris[team][debris_id]
    
    def advance_debris(self):
        for team in Team:
            to_remove = []
            for debris in self.debris[team].values():
                if debris.current_cooldown > 0:
                    continue
                else:
                    debris.current_cooldown = debris.total_cooldown
                    debris.progress += 1
                    if debris.progress == len(self.map.path):
                        to_remove.append(debris.id)
                        self.health[team] -= debris.total_health
                        self.health[team] = max(0, self.health[team])
                    else:
                        debris.x, debris.y = self.map.path[debris.progress]
            for id in to_remove:
                del self.debris[team][id]
    
    def get_tower_cooldown_reduction(self, team: Team, tower_id: int) -> float:
        this_tower = self.towers[team][tower_id]

        num_reinforcers = 0
        for tower in self.towers[team].values():
            if tower.type == TowerType.REINFORCER:
                dist = (tower.x - this_tower.x)**2 + (tower.y - this_tower.y)**2
                if dist <= TowerType.REINFORCER.range:
                    num_reinforcers += 1
        
        return GameConstants.REINFORCER_COOLDOWN_MULTIPLIER**num_reinforcers

    def render(self):
        import pygame
        import pygame.font as font

        if not self.has_rendered:
            self.has_rendered = True
            pygame.init()
            pygame.display.set_caption("GameState visualizer")
            self.tile_size = 20
            self.screen = pygame.display.set_mode((self.map.width*2 * self.tile_size, self.map.height * self.tile_size))
        
        # For performance
        pygame.event.get()

        # Function to get screen coordinates of each map tile in the form ((left, top), (width, height))
        def get_screen_coords(team, x: int, y: int) -> tuple[tuple[int, int], tuple[int, int]]:
            left = x * self.tile_size
            if team == Team.RED: # Red is on the right
                left += self.map.width * self.tile_size
            top = (self.map.height - 1 - y) * self.tile_size
            return ((left, top), (self.tile_size, self.tile_size))
        
        # Draw tiles of each team (space is black, path is purple, asteroids are gray)
        space_color = (50, 50, 50)
        path_color = (128, 0, 128)
        asteroid_color = (128, 128, 128)
        for x in range(self.map.width):
            for y in range(self.map.height):
                if self.map.tiles[x][y] == Tile.SPACE:
                    color = space_color
                elif self.map.tiles[x][y] == Tile.PATH:
                    color = path_color
                else:
                    color = asteroid_color

                # Draw blue team tile
                pygame.draw.rect(self.screen, color, get_screen_coords(Team.BLUE, x, y))

                # Draw red team tile
                pygame.draw.rect(self.screen, color, get_screen_coords(Team.RED, x, y))
        
        # Draw blue and red towers as circles
        for team in [Team.BLUE, Team.RED]:
            for tower in self.towers[team].values():
                team = tower.team
                color = (0, 0, 255) if team == Team.BLUE else (255, 0, 0)
                ((left, top), (width, height)) = get_screen_coords(team, tower.x, tower.y)
                center = (left + width/2, top + height/2)

                if tower.type == TowerType.SOLAR_FARM:
                    innercolor = (255, 255, 0)
                elif tower.type == TowerType.BOMBER:
                    innercolor = (0, 0, 0)
                elif tower.type == TowerType.GUNSHIP:
                    innercolor = (0, 204, 204)
                elif tower.type == TowerType.REINFORCER:
                    innercolor = (0, 204, 0)
                else:
                    innercolor = (255, 51, 153)

                pygame.draw.circle(self.screen, color, center, 6)
                pygame.draw.circle(self.screen, innercolor, center, 4)
                
        
        # Draw debris as text indicating number of debris on that tile
        counts = {}
        counts[Team.BLUE] = [[0 for y in range(self.map.height)] for x in range(self.map.width)]
        counts[Team.RED] = [[0 for y in range(self.map.height)] for x in range(self.map.width)]
        for team in [Team.BLUE, Team.RED]:
            for deb in self.debris[team].values():
                x = deb.x
                y = deb.y
                counts[team][x][y] += 1
        for team in [Team.BLUE, Team.RED]:
            for x in range(self.map.width):
                for y in range(self.map.height):
                    if counts[team][x][y] == 0:
                        continue
                    text = font.SysFont('Comic Sans MS', 10).render(str(counts[team][x][y]), True, (255, 255, 255))
                    ((left, top), (width, height)) = get_screen_coords(team, x, y)
                    center = (left + width/2, top + height/2)
                    text_rect = text.get_rect(center=center)
                    self.screen.blit(text, text_rect)
        
        # Draw line separating blue and red sides
        pygame.draw.line(
            self.screen,
            (255, 255, 255),
            (self.map.width * self.tile_size, 0),
            (self.map.width * self.tile_size, self.map.height * self.tile_size)
        )

        # Draw snipes as line from tower to debris
        for team in [Team.BLUE, Team.RED]:
            for ((tower_x, tower_y), (debris_x, debris_y)) in self.current_snipes[team]:
                tower_coords = get_screen_coords(team, tower_x, tower_y)
                tower_center = (tower_coords[0][0] + tower_coords[1][0] / 2, tower_coords[0][1] + tower_coords[1][1] / 2)
                debris_coords = get_screen_coords(team, debris_x, debris_y)
                debris_center = (debris_coords[0][0] + debris_coords[1][0] / 2, debris_coords[0][1] + debris_coords[1][1] / 2)
                
                pygame.draw.line(
                    self.screen,
                    (0, 0, 255) if team == Team.BLUE else (255, 0, 0),
                    tower_center,
                    debris_center
                )
        
        # Draw sprays as circles
        for team in [Team.BLUE, Team.RED]:
            for (x, y) in self.current_bombs[team]:
                ((left, top), (width, height)) = get_screen_coords(team, x, y)
                center = (left + width/2, top + height/2)

                pygame.draw.circle(
                    self.screen,
                    (0, 0, 0),
                    center,
                    math.sqrt(TowerType.BOMBER.range) * self.tile_size,
                    1 # circle outline width
                )

        # Draw turn number in bottom left
        text = font.SysFont('Comic Sans MS', 10).render(f"Turn: {self.turn}", True, (255, 255, 255))
        self.screen.blit(text, ((2, self.screen.get_height()-20), (self.screen.get_width()//2, 20)))

        # Draw each team's balance
        text = font.SysFont('Comic Sans MS', 10).render(f"Balance: {self.balance[Team.BLUE]}", True, (255, 255, 255))
        self.screen.blit(text, ((2, 0), (self.screen.get_width()//2, 20)))
        text = font.SysFont('Comic Sans MS', 10).render(f"Balance: {self.balance[Team.RED]}", True, (255, 255, 255))
        self.screen.blit(text, ((self.screen.get_width()//2+2, 0), (self.screen.get_width()//2, 20)))

        # Draw each team's health
        text = font.SysFont('Comic Sans MS', 10).render(f"Health: {self.health[Team.BLUE]}", True, (255, 255, 255))
        self.screen.blit(text, ((2, 20), (self.screen.get_width()//2, 40)))
        text = font.SysFont('Comic Sans MS', 10).render(f"Health: {self.health[Team.RED]}", True, (255, 255, 255))
        self.screen.blit(text, ((self.screen.get_width()//2+2, 20), (self.screen.get_width()//2, 40)))

        # Draw each team's time remaining
        text = font.SysFont('Comic Sans MS', 10).render(f"Time: {self.time_remaining[Team.BLUE]: .2f}", True, (255, 255, 255))
        self.screen.blit(text, ((2, 40), (self.screen.get_width()//2, 60)))
        text = font.SysFont('Comic Sans MS', 10).render(f"Time: {self.time_remaining[Team.RED]: .2f}", True, (255, 255, 255))
        self.screen.blit(text, ((self.screen.get_width()//2+2, 40), (self.screen.get_width()//2, 60)))

        pygame.display.update()
