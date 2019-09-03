import random

from src.randomizer.models.enums.difficulty import Difficulty
from src.randomizer.models.enums.goal import Goal
from src.randomizer.models.enums.logic import Logic
from src.randomizer.models.enums.enemizer import Enemizer
from src.randomizer.models.enums.start_location import StartLocation
from src.randomizer.models.enums.entrance_shuffle import EntranceShuffle


class RandomizerData:
    def __init__(self, seed: int = random.randrange(0, 999999999),
                 difficulty: Difficulty = Difficulty.NORMAL, goal: Goal = Goal.DARK_GAIA,
                 logic: Logic = Logic.COMPLETABLE, statues: str = "4", enemizer: Enemizer = Enemizer.NONE,
                 start_location: StartLocation = StartLocation.SOUTH_CAPE, firebird: bool = False, ohko: bool = False,
                 red_jewel_madness: bool = False, allow_glitches: bool = False, boss_shuffle: bool = False,
                 overworld_shuffle: bool = False, dungeon_shuffle: bool = False):
        self.seed = seed
        self.difficulty = difficulty
        self.start_location = start_location
        self.goal = goal
        self.logic = logic
        self.statues = statues
        self.enemizer = enemizer
        self.firebird = firebird
        self.ohko = ohko
        self.red_jewel_madness = red_jewel_madness
        self.allow_glitchs = allow_glitches
        self.boss_shuffle = boss_shuffle
        self.overworld_shuffle = overworld_shuffle
        self.dungeon_shuffle = dungeon_shuffle
