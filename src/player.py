# players will write a child class of the Player class
# specifically the play_turn method

from src.robot_controller import RobotController
from src.map import Map

class Player:
    def __init__(self, map: Map):
        pass

    def play_turn(self, rc: RobotController):
        raise NotImplementedError()