import random

#from .enums.difficulty import Difficulty
#from .enums.goal import Goal
#from .enums.statue_req import StatueReq
#from .enums.logic import Logic
#from .enums.dungeon_shuffle import DungeonShuffle
#from .enums.orb_rando import OrbRando
#from .enums.darkrooms import DarkRooms
#from .enums.enemizer import Enemizer
#from .enums.start_location import StartLocation
#from .enums.flute import FluteOpt
#from .enums.sprites import Sprite
from .enums import *

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
                 dungeon_shuffle: bool = False,
                 overworld_shuffle: bool = False,
                 orb_rando: bool = False,
                 darkrooms: DarkRooms = DarkRooms.NONE,
                 firebird: bool = False, 
                 ohko: bool = False,
                 red_jewel_madness: bool = False, 
                 allow_glitches: bool = False, 
                 boss_shuffle: bool = False,
                 open_mode: bool = False, 
                 z3: bool = False, 
                 race_mode: bool = False, 
                 flute: FluteOpt = FluteOpt.START,
                 sprite: Sprite = Sprite.WILL,
                 printlevel: PrintLevel = PrintLevel.SILENT,
                 break_on_error: bool = False,
                 break_on_init: bool = False,
                 ingame_debug: bool = False,
                 infinite_inventory: bool = False
                 ):
        self.seed = seed
        self.difficulty = difficulty
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
        self.flute = flute
        self.sprite = sprite
        self.printlevel = printlevel
        self.break_on_error = break_on_error
        self.break_on_init = break_on_init
        self.ingame_debug = ingame_debug
        self.infinite_inventory = infinite_inventory
        
        
        
        
        