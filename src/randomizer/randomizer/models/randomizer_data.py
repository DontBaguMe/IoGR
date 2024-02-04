import random

from .enums.difficulty import Difficulty
from .enums.goal import Goal
from .enums.statue_req import StatueReq
from .enums.logic import Logic
from .enums.dungeon_shuffle import DungeonShuffle
from .enums.orb_rando import OrbRando
from .enums.darkrooms import DarkRooms
from .enums.enemizer import Enemizer
from .enums.start_location import StartLocation
from .enums.sprites import Sprite


class RandomizerData:
    def __init__(self, 
                 seed: int = random.randint(0, 999999999),
                 difficulty: Difficulty = Difficulty.NORMAL, 
                 goal: Goal = Goal.DARK_GAIA, 
                 logic: Logic = Logic.COMPLETABLE,
                 statues: str = "4", 
                 statue_req: StatueReq = StatueReq.GAME_CHOICE, 
                 start_location: StartLocation = StartLocation.SOUTH_CAPE, 
                 enemizer: Enemizer = Enemizer.NONE,
                 coupled_exits : bool = False,
                 town_shuffle : bool = False,
                 dungeon_shuffle: DungeonShuffle = DungeonShuffle.NONE,
                 overworld_shuffle: bool = False,
                 orb_rando: OrbRando = OrbRando.NONE,
                 darkrooms: DarkRooms = DarkRooms.NONE,
                 firebird: bool = False, 
                 ohko: bool = False,
                 red_jewel_madness: bool = False, 
                 allow_glitches: bool = False, 
                 boss_shuffle: bool = False,
                 open_mode: bool = False, 
                 z3: bool = False, 
                 race_mode: bool = False, 
                 fluteless: bool = False,
                 sprite: Sprite = Sprite.WILL
                 ):
        self.seed = seed
        self.difficulty = difficulty
#        self.level = level
        self.start_location = start_location
        self.goal = goal
        self.statue_req = statue_req
        self.logic = logic
        self.statues = statues
        self.enemizer = enemizer
        self.firebird = firebird
        self.ohko = ohko
        self.red_jewel_madness = red_jewel_madness
        self.allow_glitches = allow_glitches
        self.boss_shuffle = boss_shuffle
        self.coupled_exits = coupled_exits
        self.town_shuffle = town_shuffle
        self.overworld_shuffle = overworld_shuffle
        self.dungeon_shuffle = dungeon_shuffle
        self.orb_rando = orb_rando
        self.darkrooms = darkrooms
        self.open_mode = open_mode
        self.z3 = z3
        self.race_mode = race_mode
        self.fluteless = fluteless
        self.sprite = sprite
