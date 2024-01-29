from src.game_constants import Tile
import os
import src.map_processor as map_processor
import ast

class Map:
    def __init__(self, fname: str):
        self.name = os.path.basename(fname).split('.')[0]
        with open(fname, 'r') as f:
            arrAsStr = f.readline()

        self.arr = ast.literal_eval(arrAsStr)
        self.height = len(self.arr)
        self.width = len(self.arr[0])

        self.path = map_processor.get_path(fname)
        for i in range(len(self.path)):
            self.path[i] = (self.path[i][1], self.height-1-self.path[i][0]) # swap xs and ys

        self.path_length = len(self.path)
        
        self.tiles = [[Tile.SPACE for y in range(self.height)] for x in range(self.width)]
        for i in range(self.path_length):
            x, y = self.path[i]
            self.tiles[x][y] = Tile.PATH

        for x in range(self.width):
            for y in range(self.height):
                if self.arr[y][x][0] == 'R':
                    self.tiles[x][self.height-1-y] = Tile.ASTEROID
    
    def is_in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_space(self, x: int, y: int) -> bool:
        if not self.is_in_bounds(x, y):
            return False
        return self.tiles[x][y] == Tile.SPACE
    
    def is_asteroid(self, x: int, y: int) -> bool:
        if not self.is_in_bounds(x, y):
            return False
        return self.tiles[x][y] == Tile.ASTEROID
    
    def is_path(self, x: int, y: int) -> bool:
        if not self.is_in_bounds(x, y):
            return False
        return self.tiles[x][y] == Tile.PATH
 