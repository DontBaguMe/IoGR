import random

from .enums.difficulty import Difficulty
from .enums.goal import Goal
from .enums.logic import Logic
from .enums.entrance_shuffle import EntranceShuffle
from .enums.enemizer import Enemizer
from .enums.start_location import StartLocation
#from .enums.level import Level


class RandomizerData:
    def __init__(self, seed: int = random.randint(0, 999999999),
                 difficulty: Difficulty = Difficulty.NORMAL, goal: Goal = Goal.DARK_GAIA,
                 logic: Logic = Logic.COMPLETABLE, statues: str = "4", enemizer: Enemizer = Enemizer.NONE,
                 start_location: StartLocation = StartLocation.SOUTH_CAPE, firebird: bool = False, ohko: bool = False,
                 red_jewel_madness: bool = False, allow_glitches: bool = False, boss_shuffle: bool = False,
                 open_mode: bool = False, z3: bool = False, overworld_shuffle: bool = False, entrance_shuffle: EntranceShuffle = EntranceShuffle.NONE,
                 dungeon_shuffle: bool = False):
        self.seed = seed
        self.difficulty = difficulty
#        self.level = level
        self.start_location = start_location
        self.goal = goal
        self.logic = logic
        self.statues = statues
        self.enemizer = enemizer
        self.firebird = firebird
        self.ohko = ohko
        self.red_jewel_madness = red_jewel_madness
        self.allow_glitches = allow_glitches
        self.boss_shuffle = boss_shuffle
        self.overworld_shuffle = overworld_shuffle
        self.dungeon_shuffle = dungeon_shuffle
        self.open_mode = open_mode
        self.z3 = z3
        self.overworld_shuffle = overworld_shuffle
        self.entrance_shuffle = entrance_shuffle
