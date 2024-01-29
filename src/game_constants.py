from __future__ import annotations
from enum import Enum

class TowerType(Enum):
    def __init__(self, cost, range, cooldown, damage):
        self.cost = cost
        self.range = range
        self.cooldown = cooldown
        self.damage = damage

    SOLAR_FARM = (2000, 0, 10, 0)
    GUNSHIP = (1000, 60, 20, 25)
    BOMBER = (1750, 10, 15, 6)
    REINFORCER = (3000, 5, 0, 0)

class Team(Enum):
    BLUE = 0
    RED = 1

class Tile(Enum):
    PATH = 0
    SPACE = 1
    ASTEROID = 2

class GameConstants:
    STARTING_HEALTH = 2500
    STARTING_BALANCE = 1500
    PASSIVE_INCOME = 10
    REFUND_RATIO = 0.8
    FARM_INCOME = 20
    REINFORCER_COOLDOWN_MULTIPLIER = 1.2
    INITIAL_TIME_POOL = 10 # in seconds
    ADDITIONAL_TIME_PER_TURN = 0.01

class SnipePriority(Enum):
    FIRST = 0
    LAST = 1
    CLOSE = 2
    WEAK = 3
    STRONG = 4

def get_debris_schedule(turn_num: int):
    '''
    Returns the balloon to be spawned this turn as (cooldown, health)
    '''
    if turn_num < 200: # group of low health debris
        if turn_num % 20 == 19:
            return (20, 10)
    elif turn_num < 250: # small break
        return None
    elif turn_num < 500: # sparse medium health debris
        if turn_num % 30 == 29:
            return (14, 30)
    elif turn_num < 550: # small break
        return None
    elif turn_num < 750: # groups of debris
        if turn_num % 60 < 20:
            return (14, 16)
    elif turn_num < 800: # small break
        return None
    elif turn_num < 1200: # large debris in middle of constant stream of small ones
        if turn_num % 50 == 45:
            return (10, 80)
        elif turn_num % 3 == 1:
            return (10, 15)
    elif turn_num < 1250: # small break
        return None
    elif turn_num < 1500: # speed mixup
        if turn_num % 7 == 6:
            return (6, 25)
        elif turn_num % 13 == 12:
            return (8, 30)
        elif turn_num % 17 == 16:
            return (12, 45)
        elif turn_num % 23 == 22:
            return (16, 60)
        elif turn_num % 41 == 40:
            return (40, 300)
        elif turn_num % 101 == 100:
            return (60, 1500)
    elif turn_num < 1550: # small break
        return None
    elif turn_num == 1551: # boss
        return (100, 4500)
    elif turn_num < 2400: # break to kill the boss
        return None
    elif turn_num < 2700: # stream of weak balloons with strong ones in between
        if turn_num % 30 == 25:
            return (8, 200)
        else:
            return (5, 50)
    elif turn_num < 2750: # small break
        return None
    elif turn_num < 3000: # really fast ones
        if turn_num % 2 == 1:
            return (2, 60)
    elif turn_num < 3050: # small break
        return None
    elif turn_num == 3051: # another boss
        return (100, 4500)
    elif turn_num < 3200: # small break to kill the boss
        return None
    elif turn_num < 3700: # spaced regular balloons
        if turn_num % 20 == 1:
            return (5, 300)
    else: # end game: exponentially harder balloons
        strength = (turn_num - 3700) / 100
        if turn_num % 200 < 100: # big group
            if turn_num % 20 == 19:
                return (5, int(300*(1.15**strength)))
        elif turn_num % 200 == 101: # boss
            return (100, 4500*(1.15**strength))
    return None
