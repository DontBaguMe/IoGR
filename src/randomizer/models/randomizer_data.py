import random

from models.enums.difficulty import Difficulty
from models.enums.goal import Goal
from models.enums.logic import Logic
from models.enums.enemizer import Enemizer
from models.enums.start_location import StartLocation
from models.enums.entrance_shuffle import EntranceShuffle

class RandomizerData:
    def __init__(self, seed = random.randrange(0, 999999999), 
                        difficulty = Difficulty.NORMAL, goal = Goal.DARK_GAIA, 
                        logic = Logic.COMPLETABLE, statues = "4", enemizer = Enemizer.NONE, 
                        start_location = StartLocation.SOUTH_CAPE, firebird = False):
        self.seed = seed
        self.difficulty = difficulty
        self.start_location = start_location
        self.goal = goal
        self.logic = logic
        self.statues = statues
        self.enemizer = enemizer
        self.firebird = firebird