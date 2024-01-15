import binascii, hashlib, logging, os, random, tempfile, json, copy, graphviz
from typing import BinaryIO

from .patch import Patch
from .classes import World
from .quintet_comp import compress as qt_compress
from .quintet_text import encode as qt_encode
from .errors import FileNotFoundError, OffsetError
from .models.randomizer_data import RandomizerData
from .models.enums.difficulty import Difficulty
from .models.enums.goal import Goal
from .models.enums.statue_req import StatueReq
from .models.enums.logic import Logic
from .models.enums.entrance_shuffle import EntranceShuffle
from .models.enums.dungeon_shuffle import DungeonShuffle
from .models.enums.orb_rando import OrbRando
from .models.enums.darkrooms import DarkRooms
from .models.enums.enemizer import Enemizer
from .models.enums.start_location import StartLocation

from . import asar

VERSION = "4.7.0"

MAX_RANDO_RETRIES = 100
PRINT_LOG = -1

KARA_EDWARDS = 1
KARA_MINE = 2
KARA_ANGEL = 3
KARA_KRESS = 4
KARA_ANKORWAT = 5

GEMS_EASY = 35
GEMS_NORMAL = 40
GEMS_HARD = 45
GEMS_EXTREME = 50

GEMS_Z3_EASY = 24
GEMS_Z3_NORMAL = 28
GEMS_Z3_HARD = 31
GEMS_Z3_EXTREME = 34

OUTPUT_FOLDER: str = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + ".." + os.path.sep + ".." + os.path.sep + "data" + os.path.sep + "output" + os.path.sep
BIN_PATH: str = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "bin" + os.path.sep
AG_PLUGIN_PATH: str = BIN_PATH + "plugins" + os.path.sep + "AG" + os.path.sep

os.add_dll_directory(os.getcwd()+"/src/randomizer/randomizer")    # So python can find asar.dll.


def __get_data_file__(data_filename: str) -> BinaryIO:
    path = BIN_PATH + data_filename
    return open(path, "rb")


def generate_filename(settings: RandomizerData, extension: str):
    def getDifficulty(difficulty):
        if difficulty.value == Difficulty.EASY.value:
            return "_easy"
        if difficulty.value == Difficulty.NORMAL.value:
            return "_normal"
        if difficulty.value == Difficulty.HARD.value:
            return "_hard"
        if difficulty.value == Difficulty.EXTREME.value:
            return "_extreme"

    def getGoal(goal, statues, statue_req):
        if goal.value is Goal.DARK_GAIA.value:
            return "_DG" + statues[0] + getStatueReq(statue_req)
        if goal.value is Goal.APO_GAIA.value:
            return "_AG" + statues[0] + getStatueReq(statue_req)
        if goal.value is Goal.RANDOM_GAIA.value:
            return "_RG" + statues[0] + getStatueReq(statue_req)
        if goal.value is Goal.RED_JEWEL_HUNT.value:
            return "_RJ"

    def getStatueReq(statue_req):
        if statue_req.value == StatueReq.PLAYER_CHOICE.value:
            return "p"
        if statue_req.value == StatueReq.RANDOM_CHOICE.value:
            return "r"
        else:
            return ""

    def getLogic(logic):
        if logic.value == Logic.COMPLETABLE.value:
            return ""
        if logic.value == Logic.BEATABLE.value:
            return "_L(b)"
        if logic.value == Logic.CHAOS.value:
            return "_L(x)"

    def getEntranceShuffle(entrance_shuffle):
        if entrance_shuffle.value == EntranceShuffle.COUPLED.value:
            return "_ER"
        if entrance_shuffle.value == EntranceShuffle.UNCOUPLED.value:
            return "_ER(x)"
        if entrance_shuffle.value == EntranceShuffle.NONE.value:
            return ""
 
    def getDungeonShuffle(dungeon_shuffle):
        if dungeon_shuffle.value == DungeonShuffle.BASIC.value:
            return "_dsb"
        if dungeon_shuffle.value == DungeonShuffle.CHAOS.value:
            return "_dsx"
        if dungeon_shuffle.value == DungeonShuffle.NONE.value:
            return ""
        if dungeon_shuffle.value == DungeonShuffle.CLUSTERED.value:
            return "_dsc"
    
    def getOrbRando(orb_rando):
        if orb_rando.value == OrbRando.BASIC.value:
            return "_ob"
        if orb_rando.value == OrbRando.ORBSANITY.value:
            return "_ox"
        return ""
    
    def getDarkRooms(darkrooms):
        if abs(darkrooms.value) == DarkRooms.NONE.value:
            return ""
        if abs(darkrooms.value) == DarkRooms.FEW.value:
            affix = "_drf"
        if abs(darkrooms.value) == DarkRooms.SOME.value:
            affix = "_drs"
        if abs(darkrooms.value) == DarkRooms.MANY.value:
            affix = "_drm"
        if abs(darkrooms.value) == DarkRooms.ALL.value:
            affix = "_dra"
        if darkrooms.value < 0:
            affix += "c"
        return affix

    def getStartingLocation(start_location):
        if start_location.value == StartLocation.SOUTH_CAPE.value:
            return ""
        if start_location.value == StartLocation.SAFE.value:
            return "_S(s)"
        if start_location.value == StartLocation.UNSAFE.value:
            return "_S(u)"
        if start_location.value == StartLocation.FORCED_UNSAFE.value:
            return "_S(f)"

    def getEnemizer(enemizer):
        if enemizer.value == Enemizer.NONE.value:
            return ""
        if enemizer.value == Enemizer.BALANCED.value:
            return "_E(b)"
        if enemizer.value == Enemizer.LIMITED.value:
            return "_E(l)"
        if enemizer.value == Enemizer.FULL.value:
            return "_E(f)"
        if enemizer.value == Enemizer.INSANE.value:
            return "_E(i)"

    def getSwitch(switch, param):
        if switch:
            return "_" + param
        return ""

    filename = "IoGR_v" + VERSION
    filename += getDifficulty(settings.difficulty)
    filename += getGoal(settings.goal, settings.statues, settings.statue_req)
    filename += getLogic(settings.logic)
    filename += getEntranceShuffle(settings.entrance_shuffle)
    filename += getStartingLocation(settings.start_location)
    filename += getEnemizer(settings.enemizer)
    filename += getSwitch(settings.open_mode, "o")
    filename += getSwitch(settings.overworld_shuffle, "w")
    filename += getSwitch(settings.boss_shuffle, "b")
    filename += getSwitch(settings.firebird, "f")
    filename += getSwitch(settings.ohko, "ohko")
    filename += getSwitch(settings.z3, "z3")
    filename += getDungeonShuffle(settings.dungeon_shuffle)
    filename += getOrbRando(settings.orb_rando)
    filename += getDarkRooms(settings.darkrooms)
    filename += getSwitch(settings.allow_glitches, "g")
    filename += getSwitch(settings.fluteless, "fl")
    filename += getSwitch(settings.red_jewel_madness, "rjm")
    filename += "_" + str(settings.seed)
    filename += getSwitch(settings.race_mode, "R")
    filename += "."
    filename += extension

    return filename


class Randomizer:
    offset: int = 0
    statues_required = 0
    current_position = 0

    def __init__(self, rom_path: str):
        self.rom_path = rom_path
        self.output_folder = os.path.dirname(rom_path) + os.path.sep + "iogr" + os.path.sep

        data_file = open(self.rom_path, "rb")
        self.original_rom_data = data_file.read()
        data_file.close()

        log_file_path = os.path.dirname(rom_path) + os.path.sep + "iogr" + os.path.sep + "logs" + os.path.sep + "app.log"
        if not os.path.exists(os.path.dirname(log_file_path)):
            os.makedirs(os.path.dirname(log_file_path))

        logging.basicConfig(filename=log_file_path, filemode='w', format='%(message)s', level=logging.DEBUG)
        self.logger = logging.getLogger("IOGR")

    def generate_rom(self, filename: str, settings: RandomizerData):
        self.asar_defines = { "DummyRandomizerDefine": "DummyRandomizerDefine" }

        random.seed(settings.seed)
        if settings.race_mode:
            for i in range(random.randint(100, 1000)):
                _ = random.randint(0,10000)

        statues_required = self.__get_required_statues__(settings)
        statue_req = settings.statue_req.value
        if statue_req == StatueReq.RANDOM_CHOICE.value:
            if random.randint(0,1):
                statue_req = StatueReq.GAME_CHOICE.value
            else:
                statue_req = StatueReq.PLAYER_CHOICE.value

        ##########################################################################
        #                  Generate hash code for title screen
        ##########################################################################
        hash_str = filename
        h = hashlib.sha256()
        h.update(hash_str.encode())
        hash = h.digest()

        hash_dict = [ "/", ".", "[", "]", "*", ",", "+", "-", 
                      "2", "3", "4", "5", "6", "7", "8", "9", ":", 
            "(", ")", "?", "A", "B", "C", "D", "E", "F", "G", 
            "H", "I", "J", "K", "L", "M", "N",      "P", "Q", "R", 
            "S", "T", "U", "V", "W", "X", "Y", "Z", "'", "<", ">", 
            "#", "a", "b", "c", "d", "e", "f", "g", "h", "i", 
            "j", "k",      "m", "n", "o", "p", "q", "r", "s", "t", 
            "u", "v", "w", "x", "y", "z", "{", "}",      "=", ";" ]

        hash_len = len(hash_dict)

        i = 0
        hash_final = ""
        while i < 6:
            key = hash[i] % hash_len
            hash_final += hash_dict[key]
            i += 1

        self.asar_defines["RandoTitleScreenHashString"] = hash_final
        
        ##########################################################################
        #                   Adjust Moon Tribe timer for enemizer
        ##########################################################################
        timer = 20
        if settings.enemizer.value != Enemizer.NONE.value:
            timer += 5
            if settings.enemizer.value != Enemizer.LIMITED.value:
                timer += 5
        self.asar_defines["MoonTribeTimeLimit"] = timer

        ##########################################################################
        #                            Randomize Inca tile
        ##########################################################################
        # Set random X/Y for new Inca tile
        inca_x = random.randint(0, 11)
        inca_y = random.randint(0, 5)
        inca_tile_west =  2 * inca_x + 4
        inca_tile_north = 2 * inca_y + 15
        inca_tile_east =  2 * inca_x + 7
        inca_tile_south = 2 * inca_y + 18

        # Determine address location for new tile in uncompressed map data
        row = 32 + 2 * inca_y + 16 * int(inca_x / 6)
        column = 2 * ((inca_x + 2) % 8)
        addr = 16 * row + column

        # Create empty map, insert tile, and compress
        incamap_data = b"\x00"
        while len(incamap_data) < 0x400:
            incamap_data += b"\x00"
        incamap_data = incamap_data[:addr] + b"\x40\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x42\x43" + incamap_data[addr+18:]
        incamap_compressed = qt_compress(incamap_data)
        
        # The tilemap define is awkward because it has to be a text representation, not raw bytes.
        self.asar_defines["IncaTileRoomCompTilemap"] = ""
        i = 0
        while i < len(incamap_compressed):
            self.asar_defines["IncaTileRoomCompTilemap"] += "$"+format(incamap_compressed[i],"02X")
            i += 1
            if i < len(incamap_compressed):
                self.asar_defines["IncaTileRoomCompTilemap"] += ","
        # The other defines are normal.
        self.asar_defines["IncaTileWest"] = inca_tile_west
        self.asar_defines["IncaTileNorth"] = inca_tile_north
        self.asar_defines["IncaTileEast"] = inca_tile_east
        self.asar_defines["IncaTileSouth"] = inca_tile_south

        ##########################################################################
        #                       Randomize heiroglyph order
        ##########################################################################
        hieroglyph_info = {    # 2-byte text word, sprite addr, tile ID
            1: [0xc1c0, 0x81de, 0x84],
            2: [0xc3c2, 0x81e4, 0x85],
            3: [0xc5c4, 0x81ea, 0x86],
            4: [0xc7c6, 0x81f0, 0x8c],
            5: [0xc9c8, 0x81f6, 0x8d],
            6: [0xcbca, 0x81fc, 0x8e]
        }
        hieroglyph_order = [1, 2, 3, 4, 5, 6]
        random.shuffle(hieroglyph_order)
        this_pos = 1
        while this_pos < 7:
            this_hiero = hieroglyph_order[this_pos-1]
            self.asar_defines["HieroOrder"+str(this_pos)] = this_hiero
            self.asar_defines["HieroSpritePointer"+str(this_pos)] = hieroglyph_info[this_hiero][1]
            self.asar_defines["HieroItemTile"+str(this_pos)] = hieroglyph_info[this_hiero][2]
            self.asar_defines["HieroJournalText"+str(this_pos)] = hieroglyph_info[this_hiero][0]
            this_pos += 1

        ##########################################################################
        #                          Randomize Snake Game
        ##########################################################################
        snakes_per_sec = [0.85, 0.85, 1.175, 1.50]         # By level
        if settings.fluteless:
            snakes_per_sec = [i/4.0 for i in snakes_per_sec]
        snake_adj = random.uniform(0.9, 1.1)               # Varies snakes per second by +/-10%
        snake_timer = 5 * random.randint(2,12)             # Timer between 10 and 60 sec (inc 5)
        snake_target = []
        snake_target.append(int(snake_timer * snakes_per_sec[0] * snake_adj))
        snake_target.append(int(snake_timer * snakes_per_sec[1] * snake_adj))
        snake_target.append(int(snake_timer * snakes_per_sec[2] * snake_adj))
        snake_target.append(int(snake_timer * snakes_per_sec[3] * snake_adj))

        snake_frames_str = format((60 * snake_timer) % 256, "02x") + format(int((60 * snake_timer) / 256), "02x")
        snake_target_str = []
        snake_target_str.append(format(int(snake_target[0] / 10), "x") + format(snake_target[0] % 10, "x"))
        snake_target_str.append(format(int(snake_target[1] / 10), "x") + format(snake_target[1] % 10, "x"))
        snake_target_str.append(format(int(snake_target[2] / 10), "x") + format(snake_target[2] % 10, "x"))
        snake_target_str.append(format(int(snake_target[3] / 10), "x") + format(snake_target[3] % 10, "x"))

        # Update snake game logic and text with new values
        self.asar_defines["SnakeGameTimeLimitSeconds"] = snake_timer
        self.asar_defines["SnakeGameTargetEasy"] = int(snake_timer * snakes_per_sec[0] * snake_adj)
        self.asar_defines["SnakeGameTargetIntermediate"] = int(snake_timer * snakes_per_sec[1] * snake_adj)
        self.asar_defines["SnakeGameTargetAdvanced"] = int(snake_timer * snakes_per_sec[2] * snake_adj)
        self.asar_defines["SnakeGameTargetExpert"] = int(snake_timer * snakes_per_sec[3] * snake_adj)
        # The initial space forces the define to resolve as text instead of a number.
        self.asar_defines["SnakeGameTimeLimitSecondsString"] = "_" + str(snake_timer)
        self.asar_defines["SnakeGameTargetEasyString"] = "_" + str(int(snake_timer * snakes_per_sec[0] * snake_adj))
        self.asar_defines["SnakeGameTargetIntermediateString"] = "_" + str(int(snake_timer * snakes_per_sec[1] * snake_adj))
        self.asar_defines["SnakeGameTargetAdvancedString"] = "_" + str(int(snake_timer * snakes_per_sec[2] * snake_adj))
        self.asar_defines["SnakeGameTargetExpertString"] = "_" + str(int(snake_timer * snakes_per_sec[3] * snake_adj))

        ##########################################################################
        #                    Randomize Jeweler Reward amounts
        ##########################################################################
        gem = []
        if settings.z3:
            gem.append(random.randint(1, 2))
            gem.append(random.randint(3, 4))
            gem.append(random.randint(5, 7))
            gem.append(random.randint(8, 11))
            gem.append(random.randint(12, 17))
            gem.append(random.randint(18, 23))
            gem.append(random.randint(24, 34))

            if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
                if settings.difficulty.value == 0:
                    gem[6] = GEMS_Z3_EASY
                elif settings.difficulty.value == 1:
                    gem[6] = GEMS_Z3_NORMAL
                elif settings.difficulty.value == 2:
                    gem[6] = GEMS_Z3_HARD
                elif settings.difficulty.value == 3:
                    gem[6] = GEMS_Z3_EXTREME
        else:
            gem.append(random.randint(1, 3))
            gem.append(random.randint(4, 6))
            gem.append(random.randint(7, 9))
            gem.append(random.randint(10, 14))
            gem.append(random.randint(16, 24))
            gem.append(random.randint(26, 34))
            gem.append(random.randint(36, 50))

            if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
                if settings.difficulty.value == 0:
                    gem[6] = GEMS_EASY
                elif settings.difficulty.value == 1:
                    gem[6] = GEMS_NORMAL
                elif settings.difficulty.value == 2:
                    gem[6] = GEMS_HARD
                elif settings.difficulty.value == 3:
                    gem[6] = GEMS_EXTREME

        i = 1
        while i <= 7:
            self.asar_defines["Jeweler"+str(i)+"Cost"] = gem[i-1]
            i += 1

        ##########################################################################
        #                    Randomize Mystic Statue requirement
        ##########################################################################
        statueOrder = [1, 2, 3, 4, 5, 6]
        random.shuffle(statueOrder)
        statues = []
        statues_hex = []
        
        self.asar_defines["StatuesRequiredCount"] = statues_required
        for i in statueOrder:
            self.asar_defines["Statue"+str(i)+"Required"] = 0

        if statue_req == StatueReq.PLAYER_CHOICE.value:
            self.asar_defines["SettingStatuesPlayerChoice"] = 1
        else:
            self.asar_defines["SettingStatuesPlayerChoice"] = 0
            i = 0
            while i < statues_required:
                if statueOrder[i] == 1:
                    statues.append(1)
                    statues_hex.append(b"\x21")
                    self.asar_defines["Statue1Required"] = 1
                if statueOrder[i] == 2:
                    statues.append(2)
                    statues_hex.append(b"\x22")
                    self.asar_defines["Statue2Required"] = 1
                if statueOrder[i] == 3:
                    statues.append(3)
                    statues_hex.append(b"\x23")
                    self.asar_defines["Statue3Required"] = 1
                if statueOrder[i] == 4:
                    statues.append(4)
                    statues_hex.append(b"\x24")
                    self.asar_defines["Statue4Required"] = 1
                if statueOrder[i] == 5:
                    statues.append(5)
                    statues_hex.append(b"\x25")
                    self.asar_defines["Statue5Required"] = 1
                if statueOrder[i] == 6:
                    statues.append(6)
                    statues_hex.append(b"\x26")
                    self.asar_defines["Statue6Required"] = 1
                i += 1

        # Teacher at start spoils required Mystic Statues
        statue_str = ""
        statues_hex.sort()
        if len(statues_hex) == 0:
            if statues_required == 0:
                statue_str = b"\x4d\x8e"
            else:
                statue_str = (0x20+statues_required).to_bytes(1,byteorder="little")
            statue_str += b"\xac\xd6\xd2\x80\xa2\x84\xac\xa2\x84\xa1\xa5\x88\xa2\x84\x83\x4f\xc0"
        else:
            statue_str = b"\x69\x8e\xa5\xac\x8d\x84\x84\x83\xac"
            statue_str += b"\x4c\xa9\xa3\xa4\x88\x82\xac\x63\xa4\x80\xa4\xa5\x84"
            if len(statues_hex) == 1:
                statue_str += b"\xac"
                statue_str += statues_hex[0]
                statue_str += b"\x4f"

            else:
                statue_str += b"\xa3\xcb"
                while statues_hex:
                    if len(statues_hex) > 1:
                        statue_str += statues_hex[0]
                        statue_str += b"\x2b\xac"

                    else:
                        statue_str += b"\x80\x8d\x83\xac"
                        statue_str += statues_hex[0]
                        statue_str += b"\x4f"

                    statues_hex.pop(0)

        self.asar_defines["TextTeacherStatuesString"] = ""
        i = 0
        while i < len(statue_str):
            self.asar_defines["TextTeacherStatuesString"] += "$" + format(statue_str[i],"02x")
            i += 1
            if i < len(statue_str):
                self.asar_defines["TextTeacherStatuesString"] += ","

        ##########################################################################
        #                           Determine Boss Order
        ##########################################################################
        boss_order = [*range(1,8)]
        if settings.boss_shuffle:
            non_will_bosses = [5]               # Can't be forced to play Mummy Queen as Will
            if settings.difficulty.value < 3:   # Solid Arm cannot be shuffled in non-Extreme seeds
                boss_order.remove(7)
                if settings.difficulty.value < 2:
                    non_will_bosses.append(3)   # In Easy/Normal, can't be forced to play Vampires as Will
            random.shuffle(non_will_bosses)
        
            # Determine statue order for shuffle
            for x in non_will_bosses:
                boss_order.remove(x)
            random.shuffle(boss_order)
            non_will_dungeons = [0,1,2,4]
            random.shuffle(non_will_dungeons)
            non_will_dungeons = non_will_dungeons[:len(non_will_bosses)]
            non_will_dungeons.sort()
            while non_will_bosses:
                boss = non_will_bosses.pop(0)
                dungeon = non_will_dungeons.pop(0)
                boss_order.insert(dungeon,boss)
            if 7 not in boss_order:
                boss_order.append(7)
        
            boss_music_card_labels = ["Inca","SkGn","Mu","GtWl","Pymd","Mansion","MinorDungeon"]
            # Patch music headers into new dungeons (beginner and intermediate modes)
            if settings.difficulty.value <= 1:
                i = 0
                while i < 6:
                    boss = boss_order[i]
                    this_dungeon_card = "Map"+boss_music_card_labels[i]+"CardMusic"
                    replacement_card = "DefaultMap"+boss_music_card_labels[boss-1]+"CardMusic"
                    self.asar_defines[this_dungeon_card] = "!"+replacement_card
                    i += 1
        # Set up assembly defines for boss order
        i = 1
        while i < 8:
            self.asar_defines["Boss"+str(i)+"Id"] = boss_order[i-1]
            i += 1

        ##########################################################################
        #                   Randomize Location of Kara Portrait
        #       Sets spoiler in Lance's Letter and places portrait sprite
        ##########################################################################
        # Determine random location ID
        kara_location = random.randint(1, 5)
        self.asar_defines["KaraLocation"] = kara_location

        # Set Kara's location and logic mode in RAM switches (for autotracker)
        ## (hmm, I don't think tracker supports this yet? --rae)
        #if settings.logic.value == Logic.COMPLETABLE.value:
        #    logic_int = 0x10 + kara_location
        #elif settings.logic.value == Logic.BEATABLE.value:
        #    logic_int = 0x20 + kara_location
        #else:
        #    logic_int = 0x40 + kara_location
        self.asar_defines["AutotrackerLogicAndKaraVal"] = kara_location#logic_int

        ##########################################################################
        #                          Have fun with death text
        ##########################################################################
        death_list = []
        death_list.append(
            b"\x2d\x48\xa4\xac\xd6\xa3\xa3\x8e\xac\x87\x80\xa0\xa0\x84\x8d\xa3\xac\xd6\xd7\xcb\xd6\xfe\x85\xa2\x88\x84\x8d\x83\xac\xd7\x73\x88\xa3\xac\xd7\x89\xcb\x4c\x4e\x63\x64\x4b\x69\xac\x83\x84\x80\x83\x2a\x2e\xcb\xac\xac\x6d\x4c\x88\xa2\x80\x82\x8b\x84\xac\x4c\x80\xa8\xc0")
        death_list.append(
            b"\x2d\x69\x8e\xa5\xac\xd7\x9e\x80\xac\x83\x84\x82\x84\x8d\xa4\xac\x85\x84\x8b\x8b\x8e\xa7\x2a\xcb\x48\xac\x87\x80\xa4\x84\xac\xa4\x8e\xac\x8a\x88\x8b\x8b\xac\xa9\x8e\xa5\x2a\x2e\xcb\xac\xac\x6d\x48\x8d\x88\x86\x8e\xac\x4c\x8e\x8d\xa4\x8e\xa9\x80\xc0")
        death_list.append(
            b"\x2d\x64\x8e\xac\x83\x88\x84\xac\xd6\xef\x81\x84\xac\x80\xac\xd6\x95\xcb\x80\x83\xa6\x84\x8d\xa4\xa5\xa2\x84\x2a\x2e\xcb\xac\xac\x6d\x60\x84\xa4\x84\xa2\xac\x41\x80\x8d\x8d\x88\x8d\x86\xc0")
        death_list.append(
            b"\x2d\x4b\x88\x8a\x84\xac\xd6\x94\xa3\x8b\x84\x84\xa0\xac\x82\x8e\x8c\x84\xa3\xcb\x80\x85\xa4\x84\xa2\xac\x87\x80\xa2\x83\xac\xa7\x8e\xa2\x8a\xab\xac\xd6\x94\xa2\x84\xa3\xa4\xcb\x82\x8e\x8c\x84\xa3\xac\x80\x85\xa4\x84\xa2\xac\x80\x8d\xac\x87\x8e\x8d\x84\xa3\xa4\xcb\x8b\x88\x85\x84\x2a\x2e\xac\xac\xac\xac\x6d\x64\xa5\xa2\x81\x8e\xc0")
        death_list.append(
            b"\x2d\x45\x8e\x8b\x8b\x8e\xa7\xac\xd6\xfe\x83\xa2\x84\x80\x8c\xa3\x2a\x2a\x2a\xcb\x83\x84\x80\xa4\x87\xac\x88\xa3\xac\x8d\x8e\xa4\x87\x88\x8d\x86\xab\xac\xd6\xb0\x88\xa3\xcb\x84\xa6\x84\xa2\xa9\xa4\x87\x88\x8d\x86\x2a\x2e\xcb\xac\xac\x6d\x63\xa4\x84\x85\x80\x8d\xac\x4a\x80\xa2\x8b\xac\x63\xa4\x84\x85\x80\x8d\xa3\xa3\x8e\x8d\xc0")
        death_list.append(
            b"\x2d\x40\x8b\x8b\xac\x83\x84\x80\xa4\x87\xa3\xac\x80\xa2\x84\xac\xa3\xa5\x83\x83\x84\x8d\xab\xac\x8d\x8e\xcb\xd6\xb8\x87\x8e\xa7\xac\x86\xa2\x80\x83\xa5\x80\x8b\xac\xa4\x87\x84\xcb\x83\xa9\x88\x8d\x86\xac\x8c\x80\xa9\xac\x81\x84\x2a\x2e\xcb\xac\xac\x6d\x4c\x88\x82\x87\x80\x84\x8b\xac\x4c\x82\x43\x8e\xa7\x84\x8b\x8b\xc0")
        death_list.append(
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa0\x84\xa2\x87\x80\xa0\xa3\xac\x80\x8d\xcb\x8e\xa2\x83\x84\x80\x8b\xab\xac\x81\xa5\xa4\xac\x88\xa4\xac\x88\xa3\xac\x8d\x8e\xa4\xac\x80\x8d\xcb\x84\xa8\xa0\x88\x80\xa4\x88\x8e\x8d\x2a\x2e\xcb\xac\xac\x6d\x40\x8b\x84\xa8\x80\x8d\x83\xa2\x84\xac\x43\xa5\x8c\x80\xa3\xc0")
        death_list.append(
            b"\x2d\xd6\x62\xd7\x95\x8c\x80\xa4\xa4\x84\xa2\x84\x83\xac\x88\x8d\xcb\x8b\x88\x85\x84\xab\xac\xd6\xf7\x86\x80\xa6\x84\xac\x88\xa4\xcb\xa7\x84\x88\x86\x87\xa4\xab\xac\xa7\x80\xa3\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x49\x84\x85\x85\xa2\x84\xa9\xac\x44\xa5\x86\x84\x8d\x88\x83\x84\xa3\xc0")
        death_list.append(
            b"\x2d\x4d\x8e\xac\x8e\x8d\x84\xac\xd7\x6d\x8e\xa5\xa4\xac\x8e\x85\xac\xd6\xd6\xcb\xd6\xf5\x80\x8b\x88\xa6\x84\x2a\x2a\x2a\xac\x84\xa8\x82\x84\xa0\xa4\xcb\x80\xa3\xa4\xa2\x8e\x8d\x80\xa5\xa4\xa3\x2a\x2e\xcb\xac\xac\x6d\x63\xa4\x84\xa7\x80\xa2\xa4\xac\x63\xa4\x80\x85\x85\x8e\xa2\x83\xc0")
        death_list.append(b"\x2d\x44\xa4\xac\xa4\xa5\xac\x41\xa2\xa5\xa4\x84\x0d\x2e\xcb\xac\xac\x6d\x49\xa5\x8b\x88\xa5\xa3\xac\x42\x80\x84\xa3\x80\xa2\xc0")
        death_list.append(
            b"\x2d\x64\x8e\xac\xa4\x87\x84\xac\xa7\x88\xaa\x80\xa2\x83\xac\x83\x84\x80\xa4\x87\xac\x88\xa3\xcb\x8c\x84\xa2\x84\x8b\xa9\xac\x80\xac\x81\x84\x8b\x88\x84\x85\x2a\x2e\xcb\xac\xac\x6d\x43\x84\x84\xa0\x80\x8a\xac\x42\x87\x8e\xa0\xa2\x80\xc0")
        death_list.append(
            b"\x2d\x44\xa6\x84\xa2\xa9\xac\xd6\xdf\xa9\x8e\xa5\xac\x83\x88\x84\xab\xac\x88\xa4\xcb\x87\xa5\xa2\xa4\xa3\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\xa3\x87\xac\x47\x84\x8d\x83\x84\xa2\xa3\x8e\x8d\xc0")
        death_list.append(
            b"\x2d\x48\x85\xac\x48\xac\xd6\x98\xa4\x8e\xac\x83\x88\x84\xab\xac\x8b\x84\xa4\xac\x8c\x84\xcb\x83\x88\x84\xac\x85\x88\x86\x87\xa4\x88\x8d\x86\x2a\x2e\xcb\xac\xac\x6d\x46\x80\x81\xa2\x88\x84\x8b\xac\x46\x80\xa2\x82\x88\x80\xac\x4c\x80\xa2\xa1\xa5\x84\xaa\xc0")
        death_list.append(
            b"\x2d\x44\x80\x82\x87\xac\x83\x84\x80\xa4\x87\xac\x88\xa3\xac\x80\xa3\xac\xa5\x8d\x88\xa1\xa5\x84\xcb\x80\xa3\xac\x84\x80\x82\x87\xac\x8b\x88\x85\x84\x2a\x2e\xcb\xac\xac\x6d\x4d\x88\x82\x87\x8e\x8b\x80\xa3\xac\x67\x8e\x8b\xa4\x84\xa2\xa3\xa4\x8e\xa2\x85\x85\xc0")
        death_list.append(
            b"\x2d\x48\x8d\xac\xd6\xb0\xa9\x8e\xa5\xac\xd6\x78\xd6\xb5\xcb\x85\x8e\xa2\xa7\x80\xa2\x83\xac\xd6\xab\x81\x80\x82\x8a\x2a\x2e\xcb\xac\xac\x6d\x4c\x80\xa2\x8a\xac\x4c\x80\xa2\xa3\x8b\x80\x8d\x83\xc0")
        death_list.append(
            b"\x2d\x48\xac\x82\x80\x8d\xac\xd6\x91\xa4\x87\x84\xac\x83\x80\x88\xa3\x88\x84\xa3\xcb\x86\xa2\x8e\xa7\x88\x8d\x86\xac\xd6\xbe\x8c\x84\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x4a\x84\x80\xa4\xa3\xc0")
        death_list.append(
            b"\x2d\x40\xac\xa0\x84\xa2\xa3\x8e\x8d\x0e\xa3\xac\x83\x84\xa3\xa4\x88\x8d\xa9\xac\x8e\x85\xa4\x84\x8d\xcb\x84\x8d\x83\xa3\xac\xd6\x74\x87\x88\xa3\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x4c\x88\x8b\x80\x8d\xac\x4a\xa5\x8d\x83\x84\xa2\x80\xc0")
        death_list.append(
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa4\x87\x84\xac\x83\x84\xa3\xa4\xa2\x8e\xa9\x84\xa2\xcb\x80\x8d\x83\xac\x86\x88\xa6\x84\xa2\xac\x8e\x85\xac\xa3\x84\x8d\xa3\x84\x2a\x2e\xcb\xac\xac\x6d\x40\x8d\x83\xa9\xac\x47\x80\xa2\x86\x8b\x84\xa3\x88\xa3\xc0")
        death_list.append(
            b"\x2d\x41\x84\xac\x82\x80\x8b\x8c\x2a\xac\x46\x8e\x83\xac\x80\xa7\x80\x88\xa4\xa3\xac\xa9\x8e\xa5\xcb\x80\xa4\xac\xa4\x87\x84\xac\x83\x8e\x8e\xa2\x2a\x2e\xcb\xac\xac\x6d\x46\x80\x81\xa2\x88\x84\x8b\xac\x46\x80\xa2\x82\x88\x80\xac\x4c\x80\xa2\xa1\xa5\x84\xaa\xc0")
        death_list.append(
            b"\x2d\x67\x84\xac\xd6\x91\xd7\x88\x80\x8b\x88\xa6\x84\xac\xd6\xf6\xcb\xa7\x84\xac\x80\xa2\x84\xac\x82\x8b\x8e\xa3\x84\xa3\xa4\xac\xa4\x8e\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x4d\x84\x8d\x88\x80\xac\x42\x80\x8c\xa0\x81\x84\x8b\x8b\xc0")
        death_list.append(
            b"\x43\x84\x80\xa4\x87\xac\xa4\xa7\x88\xa4\x82\x87\x84\xa3\xac\x8c\xa9\xac\x84\x80\xa2\x2f\xcb\x2d\x4b\x88\xa6\x84\xab\x2e\xac\x87\x84\xac\xa3\x80\xa9\xa3\x2a\x2a\x2a\xac\x2d\x48\x0e\x8c\xcb\x82\x8e\x8c\x88\x8d\x86\x2a\x2e\xcb\xac\xac\x6d\x66\x88\xa2\x86\x88\x8b\xc0")
        death_list.append(
            b"\x2d\x47\x84\x80\xa6\x84\x8d\xac\x88\xa3\xac\x80\xac\xd7\x90\xd6\xf4\xcb\x80\x8b\x8b\xac\xa4\x87\x84\xac\x83\x8e\x86\xa3\xac\xa9\x8e\xa5\x0e\xa6\x84\xac\xd7\x5d\xcb\x8b\x8e\xa6\x84\x83\xac\xd6\x79\xa4\x8e\xac\x86\xa2\x84\x84\xa4\xac\xa9\x8e\xa5\x2a\x2e\xcb\xac\xac\x6d\x4e\x8b\x88\xa6\x84\xa2\xac\x46\x80\xa3\xa0\x88\xa2\xa4\xaa\xc0")
        death_list.append(
            b"\x2d\x44\xa6\x84\xa2\xa9\xac\x8c\x80\x8d\xac\x83\x88\x84\xa3\x2a\xac\x4d\x8e\xa4\xcb\x84\xa6\x84\xa2\xa9\xac\x8c\x80\x8d\xac\xd7\x95\x8b\x88\xa6\x84\xa3\x2a\x2e\xcb\xac\xac\x6d\x67\x88\x8b\x8b\x88\x80\x8c\xac\x67\x80\x8b\x8b\x80\x82\x84\xc0")
        death_list.append(
            b"\x2d\x40\x8d\x83\xac\x48\xac\xa7\x88\x8b\x8b\xac\xa3\x87\x8e\xa7\xac\xa4\x87\x80\xa4\xcb\x8d\x8e\xa4\x87\x88\x8d\x86\xac\x82\x80\x8d\xac\x87\x80\xa0\xa0\x84\x8d\xac\x8c\x8e\xa2\x84\xcb\x81\x84\x80\xa5\xa4\x88\x85\xa5\x8b\xac\xa4\x87\x80\x8d\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x67\x80\x8b\xa4\xac\x67\x87\x88\xa4\x8c\x80\x8d\xc0")
        death_list.append(
            b"\x2d\x46\x84\xa4\xac\x81\xa5\xa3\xa9\xac\x8b\x88\xa6\x88\x8d\x0e\x2b\xac\x8e\xa2\xac\x86\x84\xa4\xcb\x81\xa5\xa3\xa9\xac\x83\xa9\x88\x8d\x0e\x2a\x2e\xcb\xac\xac\x6d\x40\x8d\x83\xa9\xac\x43\xa5\x85\xa2\x84\xa3\x8d\x84\xc0")
        death_list.append(
            b"\x2d\x69\x8e\xa5\x0e\xa2\x84\xac\x8a\x88\x8b\x8b\x88\x8d\x0e\xac\x8c\x84\x2b\xcb\x63\x8c\x80\x8b\x8b\xa3\x4f\x2e\xcb\xac\xac\x6d\x47\x80\x8c\x88\x8b\xa4\x8e\x8d\xac\x60\x8e\xa2\xa4\x84\xa2\xc0")
        death_list.append(
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x89\xa5\xa3\xa4\xac\x80\x8d\x8e\xa4\x87\x84\xa2\xcb\xa0\x80\xa4\x87\x2a\xac\x4E\x8d\x84\xac\xa4\x87\x80\xa4\xac\xa7\x84\xac\x80\x8b\x8b\xac\x8c\xa5\xa3\xa4\xcb\xa4\x80\x8a\x84\x2a\x2e\xcb\xac\xac\x6d\x46\x80\x8d\x83\x80\x8b\x85\xc0")
        death_list.append(
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x8d\x8e\xa4\x87\x88\x8d\x86\x2b\xac\x81\xa5\xa4\xac\xa4\x8e\xcb\x8b\x88\xa6\x84\xac\x83\x84\x85\x84\x80\xa4\x84\x83\xac\x80\x8d\x83\xac\x88\x8d\x86\x8b\x8e\xa2\x6d\xcb\x88\x8e\xa5\xa3\xac\x88\xa3\xac\xa4\x8e\xac\x83\x88\x84\xac\x83\x80\x88\x8b\xa9\x2a\x2e\xcb\xac\xac\x6d\x4D\x80\xa0\x8e\x8b\x84\x8e\x8d\xac\x41\x8e\x8d\x80\xa0\x80\xa2\xa4\x84\xc0")
        death_list.append(
            b"\x2d\x44\xa6\x84\xa2\xa9\xac\xa0\x80\xa2\xa4\x88\x8d\x86\xac\x86\x88\xa6\x84\xa3\xac\x80\xcb\x85\x8e\xa2\x84\xa4\x80\xa3\xa4\x84\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2b\xac\x84\xa6\x84\xa2\xa9\xcb\xa2\x84\xa5\x8d\x88\x8e\x8d\xac\x80\xac\x87\x88\x8d\xa4\xac\x8e\x85\xac\xa4\x87\x84\xac\xa2\x84\x6d\xcb\xa3\xa5\xa2\xa2\x84\x82\xa4\x88\x8e\x8d\x2a\x2e\xac\x6d\x63\x82\x87\x8e\xa0\x84\x8d\x87\x80\xa5\x84\xa2\xc0")
        death_list.append(
            b"\x2d\x45\x8e\xa2\xac\x8b\x88\x85\x84\xac\x80\x8d\x83\xac\x83\x84\x80\xa4\x87\xac\x80\xa2\x84\xcb\x8e\x8d\x84\x2b\xac\x84\xa6\x84\x8d\xac\x80\xa3\xac\xa4\x87\x84\xac\xa2\x88\xa6\x84\xa2\xac\x80\x8d\x83\xcb\xa4\x87\x84\xac\xa3\x84\x80\xac\x80\xa2\x84\xac\x8e\x8d\x84\x2a\x2e\xcb\xac\x6d\x4A\x87\x80\x8b\x88\x8b\xac\x46\x88\x81\xa2\x80\x8d\xc0")
        death_list.append(
            b"\x2d\x4B\x88\xa6\x84\xac\xa9\x8e\xa5\xa2\xac\x8b\x88\x85\x84\xac\xa4\x87\x80\xa4\xac\xa4\x87\x84\xcb\x85\x84\x80\xa2\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\xac\x82\x80\x8d\xac\x8d\x84\xa6\x84\xa2\xcb\x84\x8d\xa4\x84\xa2\xac\xa9\x8e\xa5\xa2\xac\x87\x84\x80\xa2\xa4\x2a\x2e\xcb\xac\xac\x6d\x64\x84\x82\xa5\x8c\xa3\x84\x87\xc0")
        death_list.append(
            b"\x2d\x40\x82\x87\x88\x84\xa6\x88\x8d\x86\xac\x8b\x88\x85\x84\xac\x88\xa3\xac\x8d\x8e\xa4\xac\xa4\x87\x84\xcb\x84\xa1\xa5\x88\xa6\x80\x8b\x84\x8d\xa4\xac\x8e\x85\xac\x80\xa6\x8e\x88\x83\x88\x8d\x86\xcb\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x40\xa9\x8d\xac\x62\x80\x8d\x83\xc0")
        death_list.append(
            b"\x2d\x48\x85\xac\xa7\x84\xac\x8c\xa5\xa3\xa4\xac\x83\x88\x84\x2b\xac\xa7\x84\xac\x83\x88\x84\xcb\x83\x84\x85\x84\x8d\x83\x88\x8d\x86\xac\x8e\xa5\xa2\xac\xa2\x88\x86\x87\xa4\xa3\x2a\x2e\xcb\xac\xac\x6d\x63\x88\xa4\xa4\x88\x8d\x86\xac\x41\xa5\x8b\x8b\xc0")
        death_list.append(
            b"\x2d\x64\x87\x84\xac\x82\x8b\x8e\xa3\x84\xa2\xac\xa7\x84\xac\x82\x8e\x8c\x84\xac\xa4\x8e\xac\xa4\x87\x84\xcb\x8d\x84\x86\x80\xa4\x88\xa6\x84\x2b\xac\xa4\x8e\xac\x83\x84\x80\xa4\x87\x2b\xac\xa4\x87\x84\xcb\x8c\x8e\xa2\x84\xac\xa7\x84\xac\x81\x8b\x8e\xa3\xa3\x8e\x8c\x2a\x2e\xcb\xac\xac\x6d\x4C\x8e\x8d\xa4\x86\x8e\x8c\x84\xa2\xa9\xac\x42\x8b\x88\x85\xa4\xc0")
        death_list.append(
            b"\x2d\x48\x85\xac\xa7\x84\xac\x83\x8e\x8d\x0e\xa4\xac\x8a\x8d\x8e\xa7\xac\x8b\x88\x85\x84\x2b\xcb\x87\x8e\xa7\xac\x82\x80\x8d\xac\xa7\x84\xac\x8a\x8d\x8e\xa7\xac\x83\x84\x80\xa4\x87\x0d\x2e\xcb\xac\xac\x6d\x42\x8e\x8d\x85\xa5\x82\x88\xa5\xa3\xc0")
        death_list.append(
            b"\x2d\x48\xac\x83\x8e\x8d\x0e\xa4\xac\x87\x80\xa6\x84\xac\x8d\x8e\xac\x85\x84\x80\xa2\xac\x8e\x85\xcb\x83\x84\x80\xa4\x87\x2a\xac\x4C\xa9\xac\x8e\x8d\x8b\xa9\xac\x85\x84\x80\xa2\xac\x88\xa3\xcb\x82\x8e\x8c\x88\x8d\x86\xac\x81\x80\x82\x8a\xac\xa2\x84\x88\x8d\x82\x80\xa2\x8d\x80\xa4\x84\x83\x2a\x2e\xcb\xac\xac\x6d\x64\xa5\xa0\x80\x82\xac\x63\x87\x80\x8a\xa5\xa2\xc0")
        death_list.append(
            b"\x2d\x4B\x88\x85\x84\xac\x88\xa4\xa3\x84\x8b\x85\xac\x88\xa3\xac\x81\xa5\xa4\xac\xa4\x87\x84\xcb\xa3\x87\x80\x83\x8e\xa7\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2b\xac\x80\x8d\x83\xac\xa3\x8e\xa5\x8b\xa3\xcb\x83\x84\xa0\x80\xa2\xa4\x84\x83\xac\x81\xa5\xa4\xac\xa4\x87\x84\xac\xa3\x87\x80\x83\x8e\xa7\xa3\xcb\x8e\x85\xac\xa4\x87\x84\xac\x8b\x88\xa6\x88\x8d\x86\x2a\x2e\xac\x6d\x64\x2a\xac\x41\xa2\x8e\xa7\x8d\x84\xc0")
        death_list.append(
            b"\x2d\x63\x8e\x8c\x84\x8e\x8d\x84\xac\x87\x80\xa3\xac\xa4\x8e\xac\x83\x88\x84\xac\x88\x8d\xcb\x8e\xa2\x83\x84\xa2\xac\xa4\x87\x80\xa4\xac\xa4\x87\x84\xac\xa2\x84\xa3\xa4\xac\x8e\x85\xac\xa5\xa3\xcb\xa3\x87\x8e\xa5\x8b\x83\xac\xa6\x80\x8b\xa5\x84\xac\x8b\x88\x85\x84\xac\x8c\x8e\xa2\x84\x2a\x2e\xcb\xac\xac\x6d\x66\x88\xa2\x86\x88\x8d\x88\x80\xac\x67\x8e\x8e\x8b\x85\xc0")
        death_list.append(
            b"\x2d\x4E\xa5\xa2\xac\x8b\x88\x85\x84\xac\x83\xa2\x84\x80\x8c\xa3\xac\xa4\x87\x84\xcb\x65\xa4\x8e\xa0\x88\x80\x2a\xac\x4E\xa5\xa2\xac\x83\x84\x80\xa4\x87\xac\x80\x82\x87\x88\x84\xa6\x84\xa3\xcb\xa4\x87\x84\xac\x48\x83\x84\x80\x8b\x2a\x2e\xcb\xac\xac\x6d\x66\x88\x82\xa4\x8e\xa2\xac\x47\xa5\x86\x8e\xc0")
        death_list.append(
            b"\x2d\x48\x85\xac\xa9\x8e\xa5\xac\x83\x88\x84\xac\x88\x8d\xac\x80\x8d\xcb\x84\x8b\x84\xa6\x80\xa4\x8e\xa2\x2b\xac\x81\x84\xac\xa3\xa5\xa2\x84\xac\xa4\x8e\xac\xa0\xa5\xa3\x87\xcb\xa4\x87\x84\xac\x65\xa0\xac\x81\xa5\xa4\xa4\x8e\x8d\x2a\x2e\xcb\xac\xac\x6d\x63\x80\x8c\xac\x4B\x84\xa6\x84\x8d\xa3\x8e\x8d\xc0")
        death_list.append(
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa6\x84\xa2\xa9\xac\x8e\x85\xa4\x84\x8d\xcb\xa2\x84\x85\x84\xa2\xa2\x84\x83\xac\xa4\x8e\xac\x80\xa3\xac\x80\xac\x86\x8e\x8e\x83\xcb\x82\x80\xa2\x84\x84\xa2\xac\x8c\x8e\xa6\x84\x2a\x2e\xcb\xac\xac\x6d\x41\xa5\x83\x83\xa9\xac\x47\x8e\x8b\x8b\xa9\xc0")
        death_list.append(
            b"\x2d\x42\x8e\xa5\xa2\x80\x86\x84\xac\x88\xa3\xac\x81\x84\x88\x8d\x86\xac\xa3\x82\x80\xa2\x84\x83\xcb\xa4\x8e\xac\x83\x84\x80\xa4\x87\x2a\x2a\x2a\xac\x80\x8d\x83\xac\xa3\x80\x83\x83\x8b\x88\x8d\x86\xcb\xa5\xa0\xac\x80\x8d\xa9\xa7\x80\xa9\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x67\x80\xa9\x8d\x84\xc0")
        death_list.append(
            b"\x2d\x48\x8d\x80\x82\xa4\x88\xa6\x88\xa4\xa9\xac\x88\xa3\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x41\x84\x8d\x88\xa4\x8e\xac\x4C\xa5\xa3\xa3\x8e\x8b\x88\x8d\x88\xc0")
        death_list.append(
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa4\x87\x84\xac\x86\x8e\x8b\x83\x84\x8d\xac\x8a\x84\xa9\xcb\xa4\x87\x80\xa4\xac\x8e\xa0\x84\x8d\xa3\xac\xa4\x87\x84\xac\xa0\x80\x8b\x80\x82\x84\xac\x8e\x85\xcb\x84\xa4\x84\xa2\x8d\x88\xa4\xa9\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x4C\x88\x8b\xa4\x8e\x8d\xc0")
        death_list.append(
            b"\x2d\x48\xac\x80\x8b\xa7\x80\xa9\xa3\xac\xa3\x80\xa9\x2b\xac\x82\x8e\x8c\xa0\x8b\x80\x82\x84\x8d\x82\xa9\xcb\x88\xa3\xac\xa4\x87\x84\xac\x8a\x88\xa3\xa3\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x63\x87\x80\xa2\x88\xac\x62\x84\x83\xa3\xa4\x8e\x8d\x84\xc0")
        death_list.append(
            b"\x2d\x48\x8d\xac\xa4\x87\x84\xac\x8b\x8e\x8d\x86\xac\xa2\xa5\x8d\xac\xa7\x84\xac\x80\xa2\x84\xcb\x80\x8b\x8b\xac\x83\x84\x80\x83\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x4C\x80\xa9\x8d\x80\xa2\x83\xac\x4A\x84\xa9\x8d\x84\xa3\xc0")
        death_list.append(
            b"\x2d\x48\x0e\x8c\xac\x8d\x8e\xa4\xac\x80\x85\xa2\x80\x88\x83\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2b\xcb\x81\xa5\xa4\xac\x48\x0e\x8c\xac\x88\x8d\xac\x8d\x8e\xac\x87\xa5\xa2\xa2\xa9\xac\xa4\x8e\xcb\x83\x88\x84\x2a\xac\x48\xac\x87\x80\xa6\x84\xac\xa3\x8e\xac\x8c\xa5\x82\x87\xac\x48\xac\xa7\x80\x8d\xa4\xcb\xa4\x8e\xac\x83\x8e\xac\x85\x88\xa2\xa3\xa4\x2a\x2e\xac\x6d\x63\x2a\xac\x47\x80\xa7\x8a\x88\x8d\x86\xc0")
        death_list.append(
            b"\x2d\x45\x8e\xa2\xac\xa4\x88\xa3\xac\x8d\x8e\xa4\xac\x88\x8d\xac\x8c\x84\xa2\x84\xac\x83\x84\x80\xa4\x87\xcb\xa4\x87\x80\xa4\xac\x8c\x84\x8d\xac\x83\x88\x84\xac\x8c\x8e\xa3\xa4\x2a\x2e\xcb\xac\xac\x6d\x44\x8b\x88\xaa\x80\x81\x84\xa4\x87\xac\x41\x80\xa2\xa2\x84\xa4\xa4\xcb\xac\xac\xac\xac\xac\x41\xa2\x8e\xa7\x8d\x88\x8d\x86\xc0")
        death_list.append(
            b"\x2d\x43\x8e\xac\x8d\x8e\xa4\xac\x85\x84\x80\xa2\xac\x83\x84\x80\xa4\x87\xac\xa3\x8e\xac\x8c\xa5\x82\x87\xcb\x81\xa5\xa4\xac\xa2\x80\xa4\x87\x84\xa2\xac\xa4\x87\x84\xac\x88\x8d\x80\x83\x84\xa1\xa5\x80\xa4\x84\xcb\x8b\x88\x85\x84\x2a\x2e\xcb\xac\xac\x6d\x41\x84\xa2\xa4\x8e\x8b\xa4\xac\x41\xa2\x84\x82\x87\xa4\xc0")
        death_list.append(
            b"\x2d\x4D\x8e\xa4\x87\x88\x8d\x86\xac\x88\x8d\xac\x8b\x88\x85\x84\xac\x88\xa3\xcb\xa0\xa2\x8e\x8c\x88\xa3\x84\x83\xac\x84\xa8\x82\x84\xa0\xa4\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x4A\x80\x8d\xa9\x84\xac\x67\x84\xa3\xa4\xc0")
        death_list.append(
            b"\x2d\x4C\xa9\xac\x85\x84\x80\xa2\xac\xa7\x80\xa3\xac\x8d\x8e\xa4\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\xcb\x88\xa4\xa3\x84\x8b\x85\x2b\xac\x81\xa5\xa4\xac\x80\xac\x83\x84\x80\xa4\x87\xac\xa7\x88\xa4\x87\x6d\xcb\x8e\xa5\xa4\xac\x8c\x84\x80\x8d\x88\x8d\x86\x2a\x2e\xcb\xac\xac\x6d\x47\xa5\x84\xa9\xac\x4D\x84\xa7\xa4\x8e\x8d\xc0")
        death_list.append(
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x89\xa5\xa3\xa4\xac\x8b\x88\x85\x84\x0e\xa3\xac\x8d\x84\xa8\xa4\xcb\x81\x88\x86\xac\x80\x83\xa6\x84\x8d\xa4\xa5\xa2\x84\x2a\x2e\xcb\xac\xac\x6d\x49\x2a\xac\x4A\x2a\xac\x62\x8e\xa7\x8b\x88\x8d\x86\xc0")
        death_list.append(
            b"\x2d\x41\x84\x82\x80\xa5\xa3\x84\xac\x8e\x85\xac\x88\x8d\x83\x88\x85\x85\x84\xa2\x84\x8d\x82\x84\x2b\xcb\x8e\x8d\x84\xac\x83\x88\x84\xa3\xac\x81\x84\x85\x8e\xa2\x84\xac\x8e\x8d\x84\xcb\x80\x82\xa4\xa5\x80\x8b\x8b\xa9\xac\x83\x88\x84\xa3\x2a\x2e\xcb\xac\xac\x6d\x44\x8b\x88\x84\xac\x67\x88\x84\xa3\x84\x8b\xc0")
        death_list.append(
            b"\x2d\x4C\xa5\xa3\xa4\xac\x8d\x8e\xa4\xac\x80\x8b\x8b\xac\xa4\x87\x88\x8d\x86\xa3\xac\x80\xa4\xcb\xa4\x87\x84\xac\x8b\x80\xa3\xa4\xac\x81\x84\xac\xa3\xa7\x80\x8b\x8b\x8e\xa7\x84\x83\xac\xa5\xa0\xcb\x88\x8d\xac\x83\x84\x80\xa4\x87\x0d\x2e\xcb\xac\xac\x6d\x60\x8b\x80\xa4\x8e\xc0")
        death_list.append(
            b"\x2d\x64\x87\x84\xa2\x84\xac\x88\xa3\xac\x8d\x8e\xac\x83\x84\x80\xa4\x87\x2b\xac\x8e\x8d\x8b\xa9\xcb\x80\xac\x82\x87\x80\x8d\x86\x84\xac\x8e\x85\xac\xa7\x8e\xa2\x8b\x83\xa3\x2a\x2e\xcb\xac\xac\x6d\x42\x87\x88\x84\x85\xac\x63\x84\x80\xa4\xa4\x8b\x84\xc0")
        death_list.append(
            b"\x2d\x48\xac\x87\x80\x83\xac\xa3\x84\x84\x8d\xac\x81\x88\xa2\xa4\x87\xac\x80\x8d\x83\xcb\x83\x84\x80\xa4\x87\xac\x81\xa5\xa4\xac\x87\x80\x83\xac\xa4\x87\x8e\xa5\x86\x87\xa4\xac\xa4\x87\x84\xa9\xcb\xa7\x84\xa2\x84\xac\x83\x88\x85\x85\x84\xa2\x84\x8d\xa4\x2a\x2e\xcb\xac\xac\x6d\x64\x2a\xac\x63\x2a\xac\x44\x8b\x88\x8e\xa4\xc0")
        death_list.append(
            b"\x2d\x42\xa5\xa2\x88\x8e\xa3\x88\xa4\xa9\xac\x88\xa3\xac\x8b\x88\x85\x84\x2a\xcb\x40\xa3\xa3\xa5\x8c\xa0\xa4\x88\x8e\x8d\xac\x88\xa3\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x4C\x80\xa2\x8a\xac\x60\x80\xa2\x8a\x84\xa2\xc0")
        death_list.append(
            b"\x2d\x48\xac\x85\x84\x84\x8b\xac\x8c\x8e\x8d\x8e\xa4\x8e\x8d\xa9\xac\x80\x8d\x83\xac\x83\x84\x80\xa4\x87\xcb\xa4\x8e\xac\x81\x84\xac\x80\x8b\x8c\x8e\xa3\xa4\xac\xa4\x87\x84\xac\xa3\x80\x8c\x84\x2a\x2e\xcb\xac\xac\x6d\x42\x87\x80\xa2\x8b\x8e\xa4\xa4\x84\xac\x41\xa2\x8e\x8d\xa4\x84\xc0")
        death_list.append(
            b"\x2d\x63\x8e\x8c\x84\xac\xa0\x84\x8e\xa0\x8b\x84\xac\x80\xa2\x84\xac\xa3\x8e\xac\x80\x85\xa2\x80\x88\x83\xcb\xa4\x8e\xac\x83\x88\x84\xac\xa4\x87\x80\xa4\xac\xa4\x87\x84\xa9\xac\x8d\x84\xa6\x84\xa2\xcb\x81\x84\x86\x88\x8d\xac\xa4\x8e\xac\x8b\x88\xa6\x84\x2a\x2e\xcb\xac\xac\x6d\x47\x84\x8d\xa2\xa9\xac\x66\x80\x8d\xac\x43\xa9\x8a\x84\xc0")
        death_list.append(
            b"\x2d\x64\x87\x84\xac\x81\x8e\x83\xa9\xac\x83\x88\x84\xa3\x2b\xac\x81\xa5\xa4\xac\xa4\x87\x84\xcb\xa3\xa0\x88\xa2\x88\xa4\xac\xa4\x87\x80\xa4\xac\xa4\xa2\x80\x8d\xa3\x82\x84\x8d\x83\xa3\xac\x88\xa4\xcb\x82\x80\x8d\x8d\x8e\xa4\xac\x81\x84\xac\xa4\x8e\xa5\x82\x87\x84\x83\xac\x81\xa9\xcb\x83\x84\x80\xa4\x87\x2a\x2e\xac\xac\x6d\x62\x80\x8c\x80\x8d\x80\xac\x4C\x80\x87\x80\xa2\xa3\x87\x88\xc0")
        death_list.append(
            b"\x2d\x67\x87\x84\xa4\x87\x84\xa2\xac\x85\x8e\xa2\xac\x8b\x88\x85\x84\xac\x8e\xa2\xcb\x83\x84\x80\xa4\x87\x2b\xac\x83\x8e\xac\xa9\x8e\xa5\xa2\xac\x8e\xa7\x8d\xac\xa7\x8e\xa2\x8a\xcb\xa7\x84\x8b\x8b\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x62\xa5\xa3\x8a\x88\x8d\xc0")
        death_list.append(
            b"\x2d\x64\x87\x84\xac\xa2\x84\xa0\x8e\xa2\xa4\xa3\xac\x8e\x85\xac\x8c\xa9\xac\x83\x84\x80\xa4\x87\xcb\x87\x80\xa6\x84\xac\x81\x84\x84\x8d\xac\x86\xa2\x84\x80\xa4\x8b\xa9\xcb\x84\xa8\x80\x86\x86\x84\xa2\x80\xa4\x84\x83\x2a\x2e\xcb\xac\xac\x6d\x4C\x80\xa2\x8a\xac\x64\xa7\x80\x88\x8d\xc0")
        death_list.append(
            b"\x2d\x64\x87\x84\xac\xa6\x80\x8b\x88\x80\x8d\xa4\xac\x8d\x84\xa6\x84\xa2\xac\xa4\x80\xa3\xa4\x84\xcb\x8e\x85\xac\x83\x84\x80\xa4\x87\xac\x81\xa5\xa4\xac\x8e\x8d\x82\x84\x2a\x2e\xcb\xac\xac\x6d\x67\x88\x8b\x8b\x88\x80\x8c\xac\x63\x87\x80\x8a\x84\xa3\xa0\x84\x80\xa2\x84\xc0")
        death_list.append(
            b"\x2d\x67\x84\xac\x8a\x8d\x8e\xa7\xac\xa4\x87\x84\xac\xa2\x8e\x80\x83\xac\xa4\x8e\xcb\x85\xa2\x84\x84\x83\x8e\x8c\xac\x87\x80\xa3\xac\x80\x8b\xa7\x80\xa9\xa3\xac\x81\x84\x84\x8d\xcb\xa3\xa4\x80\x8b\x8a\x84\x83\xac\x81\xa9\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\x6d\x40\x8d\x86\x84\x8b\x80\xac\x43\x80\xa6\x88\xa3\xc0")
        death_list.append(
            b"\x2d\x43\x84\xa3\xa0\x88\xa3\x84\xac\x8d\x8e\xa4\xac\x83\x84\x80\xa4\x87\x2b\xac\x81\xa5\xa4\xcb\xa7\x84\x8b\x82\x8e\x8c\x84\xac\x88\xa4\x2b\xac\x85\x8e\xa2\xac\x8d\x80\xa4\xa5\xa2\x84\xcb\xa7\x88\x8b\x8b\xa3\xac\x88\xa4\xac\x8b\x88\x8a\x84\xac\x80\x8b\x8b\xac\x84\x8b\xa3\x84\x2a\x2e\xcb\xac\xac\x6d\x4C\x80\xa2\x82\xa5\xa3\xac\x40\xa5\xa2\x84\x8b\x88\xa5\xa3\xc0")
        death_list.append(
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x8d\x8e\xa4\xac\xa4\x87\x84\xac\xa7\x8e\xa2\xa3\xa4\xcb\xa4\x87\x80\xa4\xac\x82\x80\x8d\xac\x87\x80\xa0\xa0\x84\x8d\xac\xa4\x8e\xac\x8c\x84\x8d\x2a\x2e\xcb\xac\xac\x6d\x60\x8b\x80\xa4\x8e\xc0")
        death_list.append(
            b"\x2d\x4B\x88\x85\x84\xac\x8b\x84\xa6\x84\x8b\xa3\xac\x80\x8b\x8b\xac\x8c\x84\x8d\x2a\xcb\x43\x84\x80\xa4\x87\xac\xa2\x84\xa6\x84\x80\x8b\xa3\xac\xa4\x87\x84\xcb\x84\x8c\x88\x8d\x84\x8d\xa4\x2a\x2e\xcb\xac\xac\x6d\x46\x84\x8e\xa2\x86\x84\xac\x41\x84\xa2\x8d\x80\xa2\x83\xac\x63\x87\x80\xa7\xc0")
        death_list.append(
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa4\x87\x84\xac\xa7\x88\xa3\x87\xac\x8e\x85\xcb\xa3\x8e\x8c\x84\x2b\xac\xa4\x87\x84\xac\xa2\x84\x8b\x88\x84\x85\xac\x8e\x85\xac\x8c\x80\x8d\xa9\x2b\xcb\x80\x8d\x83\xac\xa4\x87\x84\xac\x84\x8d\x83\xac\x8e\x85\xac\x80\x8b\x8b\x2a\x2e\xcb\xac\xac\x6d\x4B\xa5\x82\x88\xa5\xa3\xac\x40\x8d\x8d\x80\x84\xa5\xa3\xac\x63\x84\x8d\x84\x82\x80\xc0")
        death_list.append(
            b"\x2d\x43\x84\x80\xa4\x87\xac\xa7\x88\x8b\x8b\xac\x81\x84\xac\x80\xac\x86\xa2\x84\x80\xa4\xcb\xa2\x84\x8b\x88\x84\x85\x2a\xac\x4D\x8e\xac\x8c\x8e\xa2\x84\xcb\x88\x8d\xa4\x84\xa2\xa6\x88\x84\xa7\xa3\x2a\x2e\xcb\xac\xac\x6d\x4A\x80\xa4\x87\x80\xa2\x88\x8d\x84\xac\x47\x84\xa0\x81\xa5\xa2\x8d\xc0\xc0")
        if settings.difficulty.value >= 3:
            death_list.append(b"\x2d\x46\x88\xa4\xac\x86\xa5\x83\xac\xa3\x82\xa2\xa5\x81\x2a\x2e\xcb\xac\xac\x6d\x41\x80\x86\xa5\xc0")

        # Will death text
        death_str = death_list[random.randint(0, len(death_list) - 1)]
        self.asar_defines["PlayerDeathText"] = ""
        i = 0
        while i < len(death_str):
            self.asar_defines["PlayerDeathText"] += "$" + format(death_str[i],"02x")
            i += 1
            if i < len(death_str):
                self.asar_defines["PlayerDeathText"] += ","

        ##########################################################################
        #                   Randomize item and ability placement
        ##########################################################################
        done = False
        seed_adj = 0
        while not done:
            if seed_adj > MAX_RANDO_RETRIES:
                self.logger.error("ERROR: Max number of seed adjustments exceeded")
                raise RecursionError
            elif seed_adj > 0:
                if PRINT_LOG > -1:
                    print("Trying again... attempt", seed_adj+1)
            self.w = World(settings, statues_required, statues, statue_req, kara_location, gem, [inca_x + 1, inca_y + 1], hieroglyph_order, boss_order)
            done = self.w.randomize(seed_adj,PRINT_LOG)
            seed_adj += 1
        #breakpoint()
        self.w.generate_spoiler(VERSION)
        self.w.populate_asar_defines()
        for wdef in self.w.asar_defines:
            self.asar_defines[wdef] = self.w.asar_defines[wdef]

        ##########################################################################
        #             Handle Jeweler inventory strings and tracker RAM
        ##########################################################################
        if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            self.asar_defines["Jeweler7RowText"] = "Beat the game"
        else:
            self.asar_defines["Jeweler7RowText"] = "My Secrets"
        for i in [1,2,3,4,5,6,7]:
            while len(self.asar_defines["Jeweler"+str(i)+"RowText"]) < 14:
                self.asar_defines["Jeweler"+str(i)+"RowText"] += "_"
            if gem[i-1] < 10:
                self.asar_defines["Jeweler"+str(i)+"RowText"] += "_"
            self.asar_defines["Jeweler"+str(i)+"RowText"] += str(gem[i-1])

        ##########################################################################
        #                        Randomize Ishtar puzzle
        ##########################################################################
        # Create temporary map file
        f_ishtarmapblank = open(BIN_PATH + "ishtarmapblank.bin", "rb")
        ishtarmapdata = f_ishtarmapblank.read()
        f_ishtarmapblank.close()
        f_ishtarmap = tempfile.TemporaryFile()
        f_ishtarmap.write(ishtarmapdata)

        # Initialize data
        coords = [[],[],[],[]]
        idx_diff = [[],[],[],[]]
        other_changes = [[],[],[],[]]
        changes = [list(range(11)), list(range(8)), list(range(5)), list(range(10))]

        # Check if chest contents in room 3 are identical
        same_chest = (self.w.item_locations[80][3] == self.w.item_locations[81][3])
        
        # This is required, and should be 0 if no room's difference is Will's hair
        self.asar_defines["IshtarRoomWithHairDifference"] = 0

        # Loop through the four rooms, determine and apply map changes
        for room in range(4):
            random.shuffle(changes[room])

            # Pick correct change (second room only)
            idx_diff[room] = changes[room].pop(0)

            # Set additional changes for both rooms (higher difficulties only)
            if settings.difficulty.value >= 2:
                # Will's hair can only be changed in second room
                if 0 in changes[room]:
                    changes[room].remove(0)
                other_changes[room] = changes[room][:settings.difficulty.value]

            if PRINT_LOG > -1:
                print("Ishtar room",room+1,":",idx_diff[room],other_changes[room])
            done = False
            while not done:
                if other_changes[room]:
                    change_id = other_changes[room].pop(0)
                else:
                    change_id = idx_diff[room]
                    done = True
                if change_id == 0 and self.asar_defines["IshtarRoomWithHairDifference"] > 0:
                    change_id = 1    # Only one room can have hair as the difference

                # Set change for Room 1
                if room == 0:
                    if change_id == 0:  # Will's hair
                        self.asar_defines["IshtarRoomWithHairDifference"] = 1
                        coords[room] = [0x01a0, 0x01c0, 0x00b0, 0x00d0]

                    elif change_id == 1:  # Change right vase to light (vanilla)
                        f_ishtarmap.seek(int("17b", 16))
                        f_ishtarmap.write(b"\x7b")
                        f_ishtarmap.seek(int("18b", 16))
                        f_ishtarmap.write(b"\x84")
                        if done:
                            coords[room] = [0x01B0, 0x01C0, 0x0070, 0x0090]
                        else:
                            f_ishtarmap.seek(int("7b", 16))
                            f_ishtarmap.write(b"\x7b")
                            f_ishtarmap.seek(int("8b", 16))
                            f_ishtarmap.write(b"\x84")

                    elif change_id == 2:  # Change middle vase to light
                        f_ishtarmap.seek(int("175", 16))
                        f_ishtarmap.write(b"\x7b")
                        f_ishtarmap.seek(int("185", 16))
                        f_ishtarmap.write(b"\x84")
                        if done:
                            coords[room] = [0x0150, 0x0160, 0x0070, 0x0090]
                        else:
                            f_ishtarmap.seek(int("75", 16))
                            f_ishtarmap.write(b"\x7b")
                            f_ishtarmap.seek(int("85", 16))
                            f_ishtarmap.write(b"\x84")

                    elif change_id == 3:  # Change left vase to dark
                        f_ishtarmap.seek(int("174", 16))
                        f_ishtarmap.write(b"\x83")
                        f_ishtarmap.seek(int("184", 16))
                        f_ishtarmap.write(b"\x87")
                        if done:
                            coords[room] = [0x0140, 0x0150, 0x0070, 0x0090]
                        else:
                            f_ishtarmap.seek(int("74", 16))
                            f_ishtarmap.write(b"\x83")
                            f_ishtarmap.seek(int("84", 16))
                            f_ishtarmap.write(b"\x87")

                    elif change_id == 4:  # Change left shelf to empty
                        f_ishtarmap.seek(int("165", 16))
                        f_ishtarmap.write(b"\x74")
                        if done:
                            coords[room] = [0x0150, 0x0160, 0x0058, 0x0070]
                        else:
                            f_ishtarmap.seek(int("65", 16))
                            f_ishtarmap.write(b"\x74")

                    elif change_id == 5:  # Change left shelf to books
                        f_ishtarmap.seek(int("165", 16))
                        f_ishtarmap.write(b"\x76")
                        if done:
                            coords[room] = [0x0150, 0x0160, 0x0058, 0x0070]
                        else:
                            f_ishtarmap.seek(int("65", 16))
                            f_ishtarmap.write(b"\x76")

                    elif change_id == 6:  # Change right shelf to jar
                        f_ishtarmap.seek(int("166", 16))
                        f_ishtarmap.write(b"\x75")
                        if done:
                            coords[room] = [0x0160, 0x0170, 0x0058, 0x0070]
                        else:
                            f_ishtarmap.seek(int("66", 16))
                            f_ishtarmap.write(b"\x75")

                    elif change_id == 7:  # Change right shelf to empty
                        f_ishtarmap.seek(int("166", 16))
                        f_ishtarmap.write(b"\x74")
                        if done:
                            coords[room] = [0x0160, 0x0170, 0x0058, 0x0070]
                        else:
                            f_ishtarmap.seek(int("66", 16))
                            f_ishtarmap.write(b"\x74")

                    elif change_id == 8:  # Remove left sconce
                        f_ishtarmap.seek(int("157", 16))
                        f_ishtarmap.write(b"\x12\x12")
                        f_ishtarmap.seek(int("167", 16))
                        f_ishtarmap.write(b"\x1a\x1a")
                        if done:
                            coords[room] = [0x0170, 0x0190, 0x0050, 0x0070]
                        else:
                            f_ishtarmap.seek(int("57", 16))
                            f_ishtarmap.write(b"\x12\x12")
                            f_ishtarmap.seek(int("67", 16))
                            f_ishtarmap.write(b"\x1a\x1a")

                    elif change_id == 9:  # Remove right sconce
                        f_ishtarmap.seek(int("15a", 16))
                        f_ishtarmap.write(b"\x12\x12")
                        f_ishtarmap.seek(int("16a", 16))
                        f_ishtarmap.write(b"\x1a\x1a")
                        if done:
                            coords[room] = [0x01a0, 0x01c0, 0x0050, 0x0070]
                        else:
                            f_ishtarmap.seek(int("5a", 16))
                            f_ishtarmap.write(b"\x12\x12")
                            f_ishtarmap.seek(int("6a", 16))
                            f_ishtarmap.write(b"\x1a\x1a")

                    elif change_id == 10:  # Shift right vase
                        f_ishtarmap.seek(int("17a", 16))
                        f_ishtarmap.write(b"\x83\x22")
                        f_ishtarmap.seek(int("18a", 16))
                        f_ishtarmap.write(b"\x87\x13")
                        if done:
                            coords[room] = [0x01a0, 0x01b0, 0x0070, 0x0090]
                        else:
                            f_ishtarmap.seek(int("7a", 16))
                            f_ishtarmap.write(b"\x83\x22")
                            f_ishtarmap.seek(int("8a", 16))
                            f_ishtarmap.write(b"\x87\x13")


                # Set change for Room 2
                elif room == 1:
                    if change_id == 0:  # Will's hair
                        self.asar_defines["IshtarRoomWithHairDifference"] = 2
                        coords[room] = [0x0390, 0x03b0, 0x00a0, 0x00c0]

                    elif change_id == 1:  # Change left vase to light
                        f_ishtarmap.seek(int("3a3", 16))
                        f_ishtarmap.write(b"\x7c")
                        f_ishtarmap.seek(int("3b3", 16))
                        f_ishtarmap.write(b"\x84")
                        if done:
                            coords[room] = [0x0330, 0x0340, 0x00a0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("2a3", 16))
                            f_ishtarmap.write(b"\x7c")
                            f_ishtarmap.seek(int("2b3", 16))
                            f_ishtarmap.write(b"\x84")

                    elif change_id == 2:  # Change right vase to light
                        f_ishtarmap.seek(int("3a4", 16))
                        f_ishtarmap.write(b"\x7c")
                        f_ishtarmap.seek(int("3b4", 16))
                        f_ishtarmap.write(b"\x84")
                        if done:
                            coords[room] = [0x0340, 0x0350, 0x00a0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("2a4", 16))
                            f_ishtarmap.write(b"\x7c")
                            f_ishtarmap.seek(int("2b4", 16))
                            f_ishtarmap.write(b"\x84")

                    elif change_id == 3:  # Remove rock
                        f_ishtarmap.seek(int("3bd", 16))
                        f_ishtarmap.write(b"\x73")
                        if done:
                            coords[room] = [0x03d0, 0x03e0, 0x00b0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("2bd", 16))
                            f_ishtarmap.write(b"\x73")

                    elif change_id == 4:  # Add round table
                        f_ishtarmap.seek(int("395", 16))
                        f_ishtarmap.write(b"\x7d\x7e")
                        f_ishtarmap.seek(int("3a5", 16))
                        f_ishtarmap.write(b"\x85\x86")
                        f_ishtarmap.seek(int("3b5", 16))
                        f_ishtarmap.write(b"\x8d\x8e")
                        if done:
                            coords[room] = [0x0350, 0x0370, 0x0090, 0x00b0]
                        else:
                            f_ishtarmap.seek(int("295", 16))
                            f_ishtarmap.write(b"\x7d\x7e")
                            f_ishtarmap.seek(int("2a5", 16))
                            f_ishtarmap.write(b"\x85\x86")
                            f_ishtarmap.seek(int("2b5", 16))
                            f_ishtarmap.write(b"\x8d\x8e")

                    elif change_id == 5:  # Add sconce
                        f_ishtarmap.seek(int("357", 16))
                        f_ishtarmap.write(b"\x88\x89")
                        f_ishtarmap.seek(int("367", 16))
                        f_ishtarmap.write(b"\x90\x91")
                        if done:
                            coords[room] = [0x0370, 0x0390, 0x0050, 0x0070]
                        else:
                            f_ishtarmap.seek(int("257", 16))
                            f_ishtarmap.write(b"\x88\x89")
                            f_ishtarmap.seek(int("267", 16))
                            f_ishtarmap.write(b"\x90\x91")

                    elif change_id == 6:  # Add rock
                        f_ishtarmap.seek(int("3b2", 16))
                        f_ishtarmap.write(b"\x77")
                        if done:
                            coords[room] = [0x0320, 0x0330, 0x00b0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("2b2", 16))
                            f_ishtarmap.write(b"\x77")

                    elif change_id == 7:  # Put moss on rock
                        f_ishtarmap.seek(int("3bd", 16))
                        f_ishtarmap.write(b"\x8f")
                        if done:
                            coords[room] = [0x03d0, 0x03e0, 0x00b0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("2bd", 16))
                            f_ishtarmap.write(b"\x8f")


                # Set change for Room 3
                elif room == 2:
                    if not same_chest:
                        coords[room] = [0x0570, 0x0590, 0x0070, 0x0090]
                        done = True
                    
                    elif (not done or same_chest) and change_id == 0:  # Will's hair
                        self.asar_defines["IshtarRoomWithHairDifference"] = 3
                        coords[room] = [0x0590, 0x05b0, 0x00a0, 0x00c0]

                    elif (not done or same_chest) and change_id == 1:  # Remove rock
                        f_ishtarmap.seek(int("5bd", 16))
                        f_ishtarmap.write(b"\x73")
                        if (done and same_chest):
                            coords[room] = [0x05d0, 0x05e0, 0x00b0, 0x00c0]
                        elif not done:
                            f_ishtarmap.seek(int("4bd", 16))
                            f_ishtarmap.write(b"\x73")

                    elif (not done or same_chest) and change_id == 2:  # Add rock
                        f_ishtarmap.seek(int("5b2", 16))
                        f_ishtarmap.write(b"\x77")
                        if (done and same_chest):
                            coords[room] = [0x0520, 0x0530, 0x00b0, 0x00c0]
                        elif not done:
                            f_ishtarmap.seek(int("4b2", 16))
                            f_ishtarmap.write(b"\x77")

                    elif (not done or same_chest) and change_id == 3:  # Add sconce
                        f_ishtarmap.seek(int("557", 16))
                        f_ishtarmap.write(b"\x88\x89")
                        f_ishtarmap.seek(int("567", 16))
                        f_ishtarmap.write(b"\x90\x91")
                        if (done and same_chest):
                            coords[room] = [0x0570, 0x0590, 0x0050, 0x0070]
                        elif not done:
                            f_ishtarmap.seek(int("457", 16))
                            f_ishtarmap.write(b"\x88\x89")
                            f_ishtarmap.seek(int("467", 16))
                            f_ishtarmap.write(b"\x90\x91")

                    elif (not done or same_chest) and change_id == 4:  # Moss rock
                        f_ishtarmap.seek(int("5bd", 16))
                        f_ishtarmap.write(b"\x8f")
                        if (done and same_chest):
                            coords[room] = [0x05d0, 0x05e0, 0x00b0, 0x00c0]
                        elif not done:
                            f_ishtarmap.seek(int("4bd", 16))
                            f_ishtarmap.write(b"\x8f")


                # Set change for Room 4
                elif room == 3:
                    if change_id == 0:  # Will's hair (vanilla)
                        self.asar_defines["IshtarRoomWithHairDifference"] = 4
                        coords[room] = [0x0790, 0x07b0, 0x00a0, 0x00c0]

                    if change_id == 1:  # Remove rock
                        f_ishtarmap.seek(int("7bd", 16))
                        f_ishtarmap.write(b"\x73")
                        if done:
                            coords[room] = [0x07d0, 0x07e0, 0x00b0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("6bd", 16))
                            f_ishtarmap.write(b"\x73")

                    if change_id == 2:  # Add rock L
                        f_ishtarmap.seek(int("7b2", 16))
                        f_ishtarmap.write(b"\x77")
                        if done:
                            coords[room] = [0x0720, 0x0730, 0x00b0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("6b2", 16))
                            f_ishtarmap.write(b"\x77")

                    if change_id == 3:  # Add moss rock L
                        f_ishtarmap.seek(int("7b2", 16))
                        f_ishtarmap.write(b"\x8f")
                        if done:
                            coords[room] = [0x0720, 0x0730, 0x00b0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("6b2", 16))
                            f_ishtarmap.write(b"\x8f")

                    if change_id == 4:  # Add light vase L
                        f_ishtarmap.seek(int("7a3", 16))
                        f_ishtarmap.write(b"\x7c")
                        f_ishtarmap.seek(int("7b3", 16))
                        f_ishtarmap.write(b"\x84")
                        if done:
                            coords[room] = [0x0730, 0x0740, 0x00a0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("6a3", 16))
                            f_ishtarmap.write(b"\x7c")
                            f_ishtarmap.seek(int("6b3", 16))
                            f_ishtarmap.write(b"\x84")

                    if change_id == 5:  # Add dark vase L
                        f_ishtarmap.seek(int("7a3", 16))
                        f_ishtarmap.write(b"\x7f")
                        f_ishtarmap.seek(int("7b3", 16))
                        f_ishtarmap.write(b"\x87")
                        if done:
                            coords[room] = [0x0730, 0x0740, 0x00a0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("6a3", 16))
                            f_ishtarmap.write(b"\x7f")
                            f_ishtarmap.seek(int("6b3", 16))
                            f_ishtarmap.write(b"\x87")

                    if change_id == 6:  # Add light vase R
                        f_ishtarmap.seek(int("7ac", 16))
                        f_ishtarmap.write(b"\x7c")
                        f_ishtarmap.seek(int("7bc", 16))
                        f_ishtarmap.write(b"\x84")
                        if done:
                            coords[room] = [0x07c0, 0x07d0, 0x00a0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("6ac", 16))
                            f_ishtarmap.write(b"\x7c")
                            f_ishtarmap.seek(int("6bc", 16))
                            f_ishtarmap.write(b"\x84")

                    if change_id == 7:  # Add dark vase R
                        f_ishtarmap.seek(int("7ac", 16))
                        f_ishtarmap.write(b"\x7f")
                        f_ishtarmap.seek(int("7bc", 16))
                        f_ishtarmap.write(b"\x87")
                        if done:
                            coords[room] = [0x07c0, 0x07d0, 0x00a0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("6ac", 16))
                            f_ishtarmap.write(b"\x7f")
                            f_ishtarmap.seek(int("6bc", 16))
                            f_ishtarmap.write(b"\x87")

                    if change_id == 8:  # Crease in floor
                        f_ishtarmap.seek(int("7b4", 16))
                        f_ishtarmap.write(b"\x69\x6a")
                        if done:
                            coords[room] = [0x0740, 0x0760, 0x00b0, 0x00c8]
                        else:
                            f_ishtarmap.seek(int("6b4", 16))
                            f_ishtarmap.write(b"\x69\x6a")

                    if change_id == 9:  # Moss rock R
                        f_ishtarmap.seek(int("7bd", 16))
                        f_ishtarmap.write(b"\x8f")
                        if done:
                            coords[room] = [0x07d0, 0x07e0, 0x00b0, 0x00c0]
                        else:
                            f_ishtarmap.seek(int("6bd", 16))
                            f_ishtarmap.write(b"\x8f")

        # Update cursor check ranges
        for i in range(4):
            self.asar_defines["IshtarRoom"+str(i+1)+"TargetWest"] = coords[i][0]
            self.asar_defines["IshtarRoom"+str(i+1)+"TargetEast"] = coords[i][1]
            self.asar_defines["IshtarRoom"+str(i+1)+"TargetNorth"] = coords[i][2]
            self.asar_defines["IshtarRoom"+str(i+1)+"TargetSouth"] = coords[i][3]

        # Compress map data and write. A bit awkward because output needs to be a string.
        f_ishtarmap.seek(0)
        ishtarmapcomp = qt_compress(f_ishtarmap.read())
        f_ishtarmap.close()
        self.asar_defines["IshtarRoomCompTilemap"] = ""
        i = 0
        while i < len(ishtarmapcomp):
            self.asar_defines["IshtarRoomCompTilemap"] += "$" + format(ishtarmapcomp[i],"02x")
            i += 1
            if i < len(ishtarmapcomp):
                self.asar_defines["IshtarRoomCompTilemap"] += ","

        ##########################################################################
        #                                   Plugins
        ##########################################################################
        if self.w.goal == "Apocalypse Gaia":
            self.asar_defines["ApocalypseGaia"] = 1
        else:
            self.asar_defines["ApocalypseGaia"] = 0

        ##########################################################################
        #                          Have fun with final text
        ##########################################################################
        superhero_list = []
        superhero_list.append("I must go, my people need me!")
        superhero_list.append("_____Up, up, and away!")
        superhero_list.append("_______Up and atom!")
        superhero_list.append("__It's clobberin' time!")
        superhero_list.append("_______For Asgard!")
        superhero_list.append("___It's morphin' time!")
        superhero_list.append("____Back in a flash!")
        superhero_list.append("______I am GROOT!")
        superhero_list.append("_______VALHALLA!")
        superhero_list.append("_______Go Joes!")
        superhero_list.append("Wonder Twin powers activate!")
        superhero_list.append("____Titans together!")
        superhero_list.append("_______HULK SMASH!")
        superhero_list.append("________Flame on!")
        superhero_list.append("________By Crom!")
        superhero_list.append("_______Excelsior!")
        superhero_list.append("Great Caesar's ghost!")
        superhero_list.append("______Odin's beard!")
        superhero_list.append("____I have the power!")
        superhero_list.append("___Avengers assemble!")
        superhero_list.append("To the Bat-pole, Robin!")
        superhero_list.append("________Shazam!")
        superhero_list.append("_____Bite me, fanboy.")
        superhero_list.append("__Hi-yo Silver... away!")
        superhero_list.append("Here I come to save the day!")
        superhero_list.append("By the hoary hosts of Hoggoth!")
        superhero_list.append("____Teen Titans, Go!")
        superhero_list.append("_______Cowabunga!")
        superhero_list.append("_______SPOOOOON!!")
        superhero_list.append("There better be bacon when I get there...")

        # Assign final text box
        rand_idx = random.randint(0, len(superhero_list) - 1)
        self.asar_defines["TextShadowSuperhero"] = superhero_list[rand_idx]

        ##########################################################################
        #            Pass all defines to assembler and return patch
        ##########################################################################
        romdata = copy.deepcopy(self.original_rom_data) + bytearray(0x200000)
        
        self.asar_defines["SettingEarlyFirebird"] = 1 if settings.firebird else 0
        self.asar_defines["SettingRedJewelHunt"] = 1 if settings.goal.value is Goal.RED_JEWEL_HUNT.value else 0
        self.asar_defines["SettingRedJewelMadness"] = 1 if settings.red_jewel_madness else 0
        self.asar_defines["SettingOpenMode"] = 1 if settings.open_mode else 0
        self.asar_defines["SettingOHKO"] = 1 if settings.ohko else 0
        self.asar_defines["SettingZ3"] = 1 if settings.z3 else 0
        self.asar_defines["SettingFluteless"] = 1 if settings.fluteless else 0
        self.asar_defines["SettingEnemizer"] = settings.enemizer.value
        self.asar_defines["SettingEntranceShuffle"] = settings.entrance_shuffle.value
        self.asar_defines["SettingDungeonShuffle"] = settings.dungeon_shuffle.value
        self.asar_defines["SettingOrbRando"] = settings.orb_rando.value
        self.asar_defines["SettingDarkRoomsLevel"] = abs(settings.darkrooms.value)
        
        self.asar_defines["OptionMuteMusic"] = 0
        
        for d in self.asar_defines:
            self.asar_defines[d] = str(self.asar_defines[d])   # The library requires defines to be string type.
        asar.init("asar.dll")
        asar_patch_result = asar.patch(os.getcwd()+"/src/randomizer/randomizer/iogr.asr", romdata, [], True, self.asar_defines)
        
        if asar_patch_result[0]:
            return asar_patch_result
        else:
            asar_error_list = asar.geterrors()
            #breakpoint()
            return [False, asar_error_list]

    def generate_spoiler(self) -> str:
        return json.dumps(self.w.spoiler)

    def generate_asm_dump(self) -> str:
        defines_sorted = dict(sorted(self.asar_defines.items()))
        defdump = ""
        for d in defines_sorted:
            defdump += "!" + d + " = " + defines_sorted[d] + "\n"
        return defdump

    def generate_graph_visualization(self) -> graphviz.Digraph:
        self.w.complete_graph_visualization()
        return self.w.graph_viz

    def __get_required_statues__(self, settings: RandomizerData) -> int:
        if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            return 0

        if settings.statues.lower() == "random":
            return random.randint(0, 6)

        return int(settings.statues)

    def __generate_patch__(self):
        data = copy.deepcopy(self.original_rom_data)

        return Patch(data, self.logger)

    def __get_offset__(self, patch):
        header = b"\x49\x4C\x4C\x55\x53\x49\x4F\x4E\x20\x4F\x46\x20\x47\x41\x49\x41\x20\x55\x53\x41"

        patch.seek(0)
        h_addr = patch.find(header)
        if h_addr < 0:
            raise OffsetError

        return h_addr - int("ffc0", 16)
