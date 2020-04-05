import random

from .enums.difficulty import Difficulty
from .enums.goal import Goal
from .enums.logic import Logic
from .enums.enemizer import Enemizer
from .enums.start_location import StartLocation
from .enums.sprites import Sprite


class RandomizerData:
    def __init__(self, seed: int = random.randint(0, 999999999),
                 difficulty: Difficulty = Difficulty.NORMAL, goal: Goal = Goal.DARK_GAIA,
                 logic: Logic = Logic.COMPLETABLE, statues: str = "4", enemizer: Enemizer = Enemizer.NONE,
                 start_location: StartLocation = StartLocation.SOUTH_CAPE, firebird: bool = False, ohko: bool = False,
                 red_jewel_madness: bool = False, allow_glitches: bool = False, boss_shuffle: bool = False,
                 open_mode: bool = False, sprite: Sprite = Sprite.WILL, overworld_shuffle: bool = False, dungeon_shuffle: bool = False, race_mode: bool = False):
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
        self.allow_glitches = allow_glitches
        self.boss_shuffle = boss_shuffle
        self.overworld_shuffle = overworld_shuffle
        self.dungeon_shuffle = dungeon_shuffle
        self.open_mode = open_mode
        self.sprite = sprite
        self.race_mode = race_mode

    def hashable_str(self):

        def getSwitch(switch, param):
            if switch:
                return "_" + param
            return ""

        base_str = 'IoGR'
        if self.race_mode:
            base_str += "_Race"
        else:
            base_str += f"_{self.difficulty.name}"

        base_str += f"_{self.goal.name}"
        if self.goal != Goal.RED_JEWEL_HUNT:
            base_str += f"_{self.statues[0]}"
        base_str += f"_{self.logic.name}"
        base_str += f"_{self.start_location.name}"
        base_str += f"_{self.enemizer.name}"
        base_str += getSwitch(self.open_mode, "OPEN")
        base_str += getSwitch(self.boss_shuffle, "BOSS")
        base_str += getSwitch(self.firebird, "FIREBIRD")
        base_str += getSwitch(self.ohko, "OHKO")
        base_str += getSwitch(self.allow_glitches, "GLITCHES")
        base_str += getSwitch(self.red_jewel_madness, "JEWELS")
        base_str += f"_{self.seed}"

        return base_str
