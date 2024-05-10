from enum import Enum


class DarkRooms(Enum):
    ALLCURSED = -4
    MANYCURSED = -3
    SOMECURSED = -2
    FEWCURSED = -1
    NONE = 0
    FEW = 1
    SOME = 2
    MANY = 3
    ALL = 4


class Difficulty(Enum):
    EASY = 0
    NORMAL = 1
    HARD = 2
    EXTREME = 3


class DungeonShuffle(Enum):
    NONE = 0
    BASIC = 1
    CHAOS = 2
    CLUSTERED = 3


class Enemizer(Enum):
    NONE = 0
    LIMITED = 1
    BALANCED = 2
    FULL = 3
    INSANE = 4


class EntranceShuffle(Enum):
    NONE = 0
    COUPLED = 1
    UNCOUPLED = 2


class FluteOpt(Enum):
    START = 0
    SHUFFLE = 1
    FLUTELESS = 2


class Goal(Enum):
    DARK_GAIA = 0
    RED_JEWEL_HUNT = 1
    APO_GAIA = 2
    RANDOM_GAIA = 3


class Level(Enum):
    BEGINNER = 0
    INTERMEDIATE = 1
    ADVANCED = 2
    EXPERT = 3


class Logic(Enum):
    COMPLETABLE = 0
    BEATABLE = 1
    CHAOS = 2


class OrbRando(Enum):
    NONE = 0
    BASIC = 1
    ORBSANITY = 2


class Sprite(Enum):
    WILL = "will"
    BAGU = "bagu"
    INVISIBLE = "invisible"
    FREET = "freet"
    SOLAR = "solar"
    SYE = "sye"


class StartLocation(Enum):
    SOUTH_CAPE = 0
    SAFE = 1
    UNSAFE = 2
    FORCED_UNSAFE = 3


class StatueReq(Enum):
    GAME_CHOICE = 0
    PLAYER_CHOICE = 1
    RANDOM_CHOICE = 2


class PrintLevel(Enum):
    SILENT = -1
    ERROR = 0
    WARN = 1
    INFO = 2
    VERBOSE = 3
