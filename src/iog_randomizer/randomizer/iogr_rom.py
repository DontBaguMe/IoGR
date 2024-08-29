import copy
import hashlib
import json
import logging
import os
import random
import sys

from . import asar
from .classes import World
from .errors import OffsetError
from .models.enums import *
from .models.randomizer_data import RandomizerData

VERSION = "5.1.4"
MAX_RANDO_RETRIES = 50
OUTPUT_FOLDER: str = os.path.dirname(os.path.realpath(
    __file__)) + os.path.sep + ".." + os.path.sep + ".." + os.path.sep + "data" + os.path.sep + "output" + os.path.sep


def generate_filename(settings: RandomizerData, extension: str):
    def getDifficulty(difficulty):
        if difficulty.value == Difficulty.EASY.value:
            return "_E"
        if difficulty.value == Difficulty.NORMAL.value:
            return "_N"
        if difficulty.value == Difficulty.HARD.value:
            return "_H"
        if difficulty.value == Difficulty.EXTREME.value:
            return "_X"

    def getGoal(goal, statues, statue_req):
        if goal.value is Goal.DARK_GAIA.value:
            return "D" + statues[0] + getStatueReq(statue_req)
        if goal.value is Goal.APO_GAIA.value:
            return "A" + statues[0] + getStatueReq(statue_req)
        if goal.value is Goal.RANDOM_GAIA.value:
            return "R" + statues[0] + getStatueReq(statue_req)
        if goal.value is Goal.RED_JEWEL_HUNT.value:
            return "J"

    def getStatueReq(statue_req):
        if statue_req.value == StatueReq.PLAYER_CHOICE.value:
            return "P"
        if statue_req.value == StatueReq.RANDOM_CHOICE.value:
            return "R"
        else:
            return "G"

    def getLogic(logic):
        if logic.value == Logic.COMPLETABLE.value:
            return "C"
        if logic.value == Logic.BEATABLE.value:
            return "B"
        if logic.value == Logic.CHAOS.value:
            return "X"

    def getEntranceShuffle(coupled_exits, town_shuffle, dungeon_shuffle, overworld_shuffle):
        if not town_shuffle and not overworld_shuffle and not dungeon_shuffle:
            return ""
        affix = "_er"
        if coupled_exits:
            affix += "C"
        else:
            affix += "U"
        affix += "-"
        if overworld_shuffle:
            affix += "W"
        if town_shuffle:
            affix += "T"
        if dungeon_shuffle:
            affix += "D"
        return affix

    def getDarkRooms(darkrooms):
        if abs(darkrooms.value) == DarkRooms.NONE.value:
            return ""
        if abs(darkrooms.value) == DarkRooms.FEW.value:
            affix = "_drF"
        if abs(darkrooms.value) == DarkRooms.SOME.value:
            affix = "_drS"
        if abs(darkrooms.value) == DarkRooms.MANY.value:
            affix = "_drM"
        if abs(darkrooms.value) == DarkRooms.ALL.value:
            affix = "_drA"
        if darkrooms.value < 0:
            affix += "C"
        return affix

    def getStartingLocation(start_location):
        if start_location.value == StartLocation.SOUTH_CAPE.value:
            return ""
        if start_location.value == StartLocation.SAFE.value:
            return "_sS"
        if start_location.value == StartLocation.UNSAFE.value:
            return "_sU"
        if start_location.value == StartLocation.FORCED_UNSAFE.value:
            return "_sF"

    def getEnemizer(enemizer, boss_shuffle):
        if enemizer.value == Enemizer.NONE.value and not boss_shuffle:
            return ""
        affix = "_en"
        if enemizer.value == Enemizer.BALANCED.value:
            affix += "B"
        if enemizer.value == Enemizer.LIMITED.value:
            affix += "L"
        if enemizer.value == Enemizer.FULL.value:
            affix += "F"
        if enemizer.value == Enemizer.INSANE.value:
            affix += "I"
        if boss_shuffle:
            affix += "-B"
        return affix

    def getFluteOpt(flute):
        if flute.value == FluteOpt.SHUFFLE.value:
            return "-fs"
        if flute.value == FluteOpt.FLUTELESS.value:
            return "-fl"
        return ""

    def getSwitch(switch, param):
        if switch:
            return param
        return ""

    filename = "IoGR" + VERSION
    filename += getDifficulty(settings.difficulty)
    filename += getLogic(settings.logic)
    filename += getGoal(settings.goal, settings.statues, settings.statue_req)
    filename += getStartingLocation(settings.start_location)
    filename += getEnemizer(settings.enemizer, settings.boss_shuffle)
    filename += getEntranceShuffle(settings.coupled_exits, settings.town_shuffle, settings.dungeon_shuffle,
                                   settings.overworld_shuffle)
    filename += getSwitch(settings.orb_rando, "_oX")
    filename += getDarkRooms(settings.darkrooms)
    if (
            settings.open_mode or settings.firebird or settings.ohko or settings.z3 or settings.allow_glitches or settings.flute.value > 0 or settings.infinite_inventory or settings.red_jewel_madness):
        filename += "_v"
        filename += getSwitch(settings.open_mode, "o")
        filename += getSwitch(settings.firebird, "f")
        filename += getSwitch(settings.allow_glitches, "g")
        filename += getSwitch(settings.ohko, "1")
        filename += getSwitch(settings.z3, "z")
        filename += getSwitch(settings.infinite_inventory, "i")
        filename += getFluteOpt(settings.flute)
        filename += getSwitch(settings.red_jewel_madness, "-rjm")
    filename += "_" + str(settings.seed)
    filename += getSwitch(settings.race_mode, "R")
    if extension != "":
        filename += "." + extension

    return filename


class Randomizer:
    statues_required = 0

    def __init__(self, rom_path: str):
        self.rom_path = rom_path
        self.output_folder = os.path.dirname(rom_path) + os.path.sep + "iogr" + os.path.sep

        data_file = open(self.rom_path, "rb")
        self.original_rom_data = data_file.read()
        data_file.close()
        if len(self.original_rom_data) == 0x200200:
            self.original_rom_data = self.original_rom_data[0x200:]  # Strip the 512-byte header
        if len(self.original_rom_data) == 0x200000:
            # Validate a 2MB input
            basehash = hashlib.md5()
            basehash.update(self.original_rom_data)
            if basehash.hexdigest() != 'a7c7a76b4d6f6df389bd631757b91b76':
                raise OffsetError
        elif len(self.original_rom_data) != 0x400000:
            # If caller gives a 4MB input, assume it knows what it's doing; otherwise fail
            raise OffsetError

        log_file_path = os.path.dirname(
            rom_path) + os.path.sep + "iogr" + os.path.sep + "logs" + os.path.sep + "app.log"
        if not os.path.exists(os.path.dirname(log_file_path)):
            os.makedirs(os.path.dirname(log_file_path))

        logging.basicConfig(filename=log_file_path, filemode='w', format='%(message)s', level=logging.DEBUG)
        self.logger = logging.getLogger("IOGR")

    def generate_rom(self, filename: str, settings: RandomizerData, profile_base_filepath=""):
        self.asar_defines = {"DummyRandomizerDefine": "DummyRandomizerDefine"}

        random.seed(settings.seed)
        if settings.race_mode:
            for i in range(random.randint(100, 1000)):
                _ = random.randint(0, 10000)

        statues_required = self.__get_required_statues__(settings)
        statue_req = settings.statue_req.value
        if statue_req == StatueReq.RANDOM_CHOICE.value:
            if random.randint(0, 1):
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

        hash_dict = ["/", ".", "[", "]", "*", ",", "+", "-",
                     "2", "3", "4", "5", "6", "7", "8", "9", ":",
                     "(", ")", "?", "A", "B", "C", "D", "E", "F", "G",
                     "H", "I", "J", "K", "L", "M", "N", "P", "Q", "R",
                     "S", "T", "U", "V", "W", "X", "Y", "Z", "'", "<", ">",
                     "#", "a", "b", "c", "d", "e", "f", "g", "h", "i",
                     "j", "k", "m", "n", "o", "p", "q", "r", "s", "t",
                     "u", "v", "w", "x", "y", "z", "{", "}", "=", ";"]

        hash_len = len(hash_dict)

        i = 0
        hash_final = ""
        while i < 6:
            key = hash[i] % hash_len
            hash_final += hash_dict[key]
            i += 1

        self.asar_defines["RandoTitleScreenHashString"] = hash_final

        ##########################################################################
        #                            Randomize Inca tile
        ##########################################################################
        # Set random X/Y for new Inca tile
        inca_x = random.randint(0, 11)
        inca_y = random.randint(0, 5)
        self.asar_defines["IncaTileX"] = inca_x
        self.asar_defines["IncaTileY"] = inca_y

        ##########################################################################
        #                       Randomize heiroglyph order
        ##########################################################################
        # hieroglyph_info = {    # 2-byte text word, sprite addr, tile ID
        #    1: [0xc1c0, 0x81de, 0x84],
        #    2: [0xc3c2, 0x81e4, 0x85],
        #    3: [0xc5c4, 0x81ea, 0x86],
        #    4: [0xc7c6, 0x81f0, 0x8c],
        #    5: [0xc9c8, 0x81f6, 0x8d],
        #    6: [0xcbca, 0x81fc, 0x8e]
        # }
        hieroglyph_order = [1, 2, 3, 4, 5, 6]
        random.shuffle(hieroglyph_order)
        this_pos = 1
        while this_pos < 7:
            this_hiero = hieroglyph_order[this_pos - 1]
            self.asar_defines["HieroOrder" + str(this_pos)] = this_hiero
            # self.asar_defines["HieroSpritePointer"+str(this_pos)] = hieroglyph_info[this_hiero][1]
            # self.asar_defines["HieroItemTile"+str(this_pos)] = hieroglyph_info[this_hiero][2]
            # self.asar_defines["HieroJournalText"+str(this_pos)] = hieroglyph_info[this_hiero][0]
            this_pos += 1

        ##########################################################################
        #                          Randomize Snake Game
        ##########################################################################
        snakes_per_sec = [0.75, 0.85, 1.175, 1.50]         # By level
        if settings.flute.value >= 1:
            snakes_per_sec = [i / 4.0 for i in snakes_per_sec]
        snake_adj = random.uniform(0.9, 1.1)  # Varies snakes per second by +/-10%
        snake_timer = 5 * random.randint(2, 12)  # Timer between 10 and 60 sec (inc 5)
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
        self.asar_defines["SnakeGameTargetIntermediateString"] = "_" + str(
            int(snake_timer * snakes_per_sec[1] * snake_adj))
        self.asar_defines["SnakeGameTargetAdvancedString"] = "_" + str(int(snake_timer * snakes_per_sec[2] * snake_adj))
        self.asar_defines["SnakeGameTargetExpertString"] = "_" + str(int(snake_timer * snakes_per_sec[3] * snake_adj))

        ##########################################################################
        #                    Randomize Jeweler Reward amounts
        ##########################################################################
        gem = []
        gem_mod = settings.difficulty.value
        if settings.z3:
            gem.append(random.randint(1, 2))
            gem.append(random.randint(3, 4))
            gem.append(random.randint(5, 7))
            gem.append(random.randint(8, 11))
            gem.append(random.randint(12, 17))
            gem.append(random.randint(18, 23))
            gem.append(random.randint(24, 34))
            if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
                gem[6] = [24, 28, 31, 34][gem_mod]
        else:
            gem.append(random.randint(1, 3))
            gem.append(random.randint(4, 6))
            gem.append(random.randint(7, 9))
            gem.append(random.randint(10, 14))
            gem.append(random.randint(16, 21 + gem_mod))
            gem.append(random.randint(23 + gem_mod, 28 + 2*gem_mod))
            gem.append(random.randint(32 + 2*gem_mod, 38 + 4*gem_mod))
            if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
                gem[6] = [35, 40, 45, 50][gem_mod]

        i = 1
        while i <= 7:
            self.asar_defines["Jeweler" + str(i) + "Cost"] = gem[i - 1]
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
            self.asar_defines["Statue" + str(i) + "Required"] = 0

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

        ##########################################################################
        #                           Boss shuffle
        ##########################################################################
        # Edge cases:
        # - MQ2 and SA post-defeat lead to the top of Babel
        # - Babel boss and Mansion boss post-defeat lead to Dao (unless the boss is MQ2 or SA)
        # - The top of Babel leads to the dungeon of MQ2
        # - Rama Statues are required by the Mu boss, not by Vamps
        # - S exit from Vamp statue room returns to the dungeon of Vamps
        boss_order = [*range(1, 8)]
        if settings.boss_shuffle:
            non_will_bosses = [5]  # Never forced to play Mummy Queen as Will
            if settings.flute.value == FluteOpt.FLUTELESS.value:
                # Can't beat Castoth as Will without Flute (or generous ability shuffle and lots of patience)
                non_will_bosses.append(1)
            if settings.difficulty.value < 3:  # For non-Extreme seeds:
                boss_order.remove(7)  # - Don't shuffle Solid Arm at all;
                if settings.flute.value == FluteOpt.FLUTELESS.value:
                    non_will_bosses.append(3)  # - Don't require fluteless Vamps.
            if settings.difficulty.value < 2:  # Also, in Easy/Normal, can't be forced to play Vampires as Will
                if 3 not in non_will_bosses:
                    non_will_bosses.append(3)
            random.shuffle(non_will_bosses)

            # Determine statue order, ensuring that non-Will bosses aren't in Will-only rooms
            # (GtWl and Mansion force Will at the boss door, so can't have a non-Will boss)
            for x in non_will_bosses:
                boss_order.remove(x)
            random.shuffle(boss_order)
            non_will_dungeons = [0, 1, 2, 4]  # i.e. dungeons that can have a non-Will boss
            # Assign non_will_bosses to the required number of random non_will_dungeons
            random.shuffle(non_will_dungeons)
            non_will_dungeons = non_will_dungeons[:len(non_will_bosses)]
            non_will_dungeons.sort()
            while non_will_bosses:
                boss = non_will_bosses.pop(0)
                dungeon = non_will_dungeons.pop(0)
                boss_order.insert(dungeon, boss)
            if 7 not in boss_order:
                boss_order.append(7)

            # Patch music headers into new dungeons (beginner and intermediate modes);
            # dungeon 5 (Babel) music is not changed, but is referenced as MinorDungeon by MQ2
            boss_music_card_labels = ["Inca", "SkGn", "Mu", "GtWl", "Pymd", "MinorDungeon", "Mansion"]
            if settings.difficulty.value <= 1:
                i = 0
                while i < 7:
                    if i != 5:
                        boss = boss_order[i]
                        this_dungeon_card = "Map" + boss_music_card_labels[i] + "CardMusic"
                        replacement_card = "DefaultMap" + boss_music_card_labels[boss - 1] + "CardMusic"
                        self.asar_defines[this_dungeon_card] = "!" + replacement_card
                    i += 1
        # Set up assembly defines for boss order
        i = 1
        while i < 8:
            self.asar_defines["Boss" + str(i) + "Id"] = boss_order[i - 1]
            i += 1

        ##########################################################################
        #                   Randomize Location of Kara Portrait
        #       Sets spoiler in Lance's Letter and places portrait sprite
        ##########################################################################
        # Determine random location ID
        kara_location = random.randint(1, 5)
        self.asar_defines["KaraLocation"] = kara_location

        # Set Kara's location and logic mode in RAM switches (for autotracker)
        ## (hmm, I don't think tracker supports this yet?)
        # if settings.logic.value == Logic.COMPLETABLE.value:
        #    logic_int = 0x10 + kara_location
        # elif settings.logic.value == Logic.BEATABLE.value:
        #    logic_int = 0x20 + kara_location
        # else:
        #    logic_int = 0x40 + kara_location
        self.asar_defines["AutotrackerLogicAndKaraVal"] = kara_location  # logic_int

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
        death_list.append(
            b"\x2d\x44\xa4\xac\xa4\xa5\xac\x41\xa2\xa5\xa4\x84\x0d\x2e\xcb\xac\xac\x6d\x49\xa5\x8b\x88\xa5\xa3\xac\x42\x80\x84\xa3\x80\xa2\xc0")
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
            death_list.append(
                b"\x2d\x46\x88\xa4\xac\x86\xa5\x83\xac\xa3\x82\xa2\xa5\x81\x2a\x2e\xcb\xac\xac\x6d\x41\x80\x86\xa5\xc0")

        # Will death text
        death_str = death_list[random.randint(0, len(death_list) - 1)]
        self.asar_defines["PlayerDeathText"] = ""
        i = 0
        while i < len(death_str):
            self.asar_defines["PlayerDeathText"] += "$" + format(death_str[i], "02x")
            i += 1
            if i < len(death_str):
                self.asar_defines["PlayerDeathText"] += ","

        ##########################################################################
        #                   Randomize item and ability placement
        ##########################################################################
        done = False
        self.seed_adj = 0
        while not done:
            if self.seed_adj > MAX_RANDO_RETRIES:
                self.logger.error("ERROR: Max number of seed adjustments exceeded")
                raise RecursionError
            elif self.seed_adj > 0:
                if settings.printlevel.value > -1:
                    print("Trying again... attempt", self.seed_adj + 1)
            self.w = World(settings, statues_required, statues, statue_req, kara_location, gem,
                           [inca_x + 1, inca_y + 1], hieroglyph_order, boss_order)
            done = self.w.randomize(self.seed_adj, settings.printlevel.value, settings.break_on_error,
                                    settings.break_on_init)
            if profile_base_filepath != "":
                val_messages = self.w.validate()
                f = open(profile_base_filepath + "_" + format(self.seed_adj, "02") + ".txt", "w")
                f.write(generate_filename(settings, ""))
                f.write("\n\n")
                f.write("Error log:\n")
                if not self.w.errorlog:
                    f.write("No errors\n")
                else:
                    for m in self.w.errorlog:
                        f.write(m + "\n")
                f.write("\n\n")
                f.write("Validation log:\n")
                for m in val_messages:
                    f.write(m + "\n")
                f.write("\n\n")
                f.write("World graph:\n")
                for n in sorted(self.w.graph):
                    f.write(str(n) + ": " + str(self.w.graph[n]) + "\n")
                f.write("\n\n")
                f.write("World edges:\n")
                for e in sorted(self.w.logic):
                    f.write(str(e) + ": " + str(self.w.logic[e]) + "\n")
                f.write("\n\n")
                f.write("World exits:\n")
                for x in sorted(self.w.exits):
                    f.write(str(x) + ": " + str(self.w.exits[x]) + "\n")
                f.write("\n\n")
                f.close()
            self.seed_adj += 1
        self.w.generate_spoiler(VERSION)
        self.w.populate_asar_defines()
        for wdef in self.w.asar_defines:
            self.asar_defines[wdef] = self.w.asar_defines[wdef]

        ##########################################################################
        #                        Randomize Ishtar puzzle
        ##########################################################################
        used_hair = False
        for room, maxchg in [(1, 10), (2, 7), (3, 4), (4, 9)]:
            minchg = 1 if used_hair else 0
            change1 = random.randint(minchg, maxchg)
            if change1 == 0:
                used_hair = True
                minchg = 1
            self.asar_defines["IshtarRoom" + str(room) + "DifferenceIndex1"] = change1
            if settings.difficulty.value >= 2:
                change2 = change1
                while change2 == change1:
                    change2 = random.randint(minchg, maxchg)
                if change2 == 0:
                    used_hair = True
                    minchg = 1
                self.asar_defines["IshtarRoom" + str(room) + "DifferenceIndex2"] = change2
                if settings.difficulty.value >= 3:
                    change3 = change2
                    while change3 == change2 or change3 == change1:
                        change3 = random.randint(minchg, maxchg)
                    if change3 == 0:
                        used_hair = True
                        minchg = 1
                    self.asar_defines["IshtarRoom" + str(room) + "DifferenceIndex3"] = change3

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
        superhero_list.append("I must go,]my people need me!")
        superhero_list.append("_____Up, up, and away!")
        superhero_list.append("_______Up and atom!")
        superhero_list.append("__It's clobberin' time!")
        superhero_list.append("_______For Asgard!")
        superhero_list.append("___It's morphin' time!")
        superhero_list.append("____Back in a flash!")
        superhero_list.append("______I am GROOT!")
        superhero_list.append("_______VALHALLA!")
        superhero_list.append("_______Go Joes!")
        superhero_list.append("Wonder Twin powers]activate!")
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
        superhero_list.append("Here I come to]save the day!")
        superhero_list.append("By the hoary hosts]of Hoggoth!")
        superhero_list.append("____Teen Titans, Go!")
        superhero_list.append("_______Cowabunga!")
        superhero_list.append("_______SPOOOOON!!")
        superhero_list.append("There better be bacon]when I get there...")

        # Assign final text box
        rand_idx = random.randint(0, len(superhero_list) - 1)
        self.asar_defines["TextShadowSuperhero"] = superhero_list[rand_idx]

        ##########################################################################
        #            Pass all defines to assembler and return patch
        ##########################################################################
        if len(self.original_rom_data) == 0x200000:
            romdata = copy.deepcopy(self.original_rom_data) + bytearray(0x200000)
        else:  # Caller provided a pre-expanded input
            romdata = copy.deepcopy(self.original_rom_data)

        self.asar_defines["SettingBossShuffle"] = 1 if settings.boss_shuffle else 0
        self.asar_defines["SettingInfiniteInventory"] = 1 if settings.infinite_inventory else 0
        self.asar_defines["SettingEarlyFirebird"] = 1 if settings.firebird else 0
        self.asar_defines["SettingRedJewelHunt"] = 1 if settings.goal.value is Goal.RED_JEWEL_HUNT.value else 0
        self.asar_defines["SettingRedJewelMadness"] = 1 if settings.red_jewel_madness and not settings.infinite_inventory else 0
        self.asar_defines["SettingOpenMode"] = 1 if settings.open_mode else 0
        self.asar_defines["SettingOHKO"] = 1 if settings.ohko else 0
        self.asar_defines["SettingZ3"] = 1 if settings.z3 else 0
        self.asar_defines["SettingFluteOpt"] = settings.flute.value
        self.asar_defines["SettingEnemizer"] = settings.enemizer.value
        self.asar_defines["SettingTownShuffle"] = 1 if settings.town_shuffle else 0
        self.asar_defines["SettingDungeonShuffle"] = 1 if settings.dungeon_shuffle else 0
        self.asar_defines["SettingOrbRando"] = 1 if settings.orb_rando else 0
        self.asar_defines["SettingDarkRoomsLevel"] = abs(settings.darkrooms.value)
        self.asar_defines["SettingDebug"] = 1 if settings.ingame_debug else 0
        self.asar_defines["SettingDsWarp"] = 1 if settings.ds_warp else 0
        if settings.red_jewel_madness:
            self.asar_defines["InitialHp"] = 40
        elif settings.ohko:
            self.asar_defines["InitialHp"] = 1
        elif settings.z3:
            self.asar_defines["InitialHp"] = 6
        else:
            self.asar_defines["InitialHp"] = 8

        self.asar_defines["OptionMuteMusic"] = 0

        for d in self.asar_defines:
            self.asar_defines[d] = str(self.asar_defines[d])  # The library requires defines to be string type.
        if os.name != "nt":
            asar.init(os.path.dirname(__file__) + os.path.sep + "asar-x64.so")
        else:  # Windows
            os.add_dll_directory(os.path.dirname(__file__))
            if sys.maxsize > 2 ** 32:  # 64-bit
                asar.init("asar-x64.dll")
            else:  # 32-bit
                asar.init("asar-x86.dll")
        self.asar_patch_result = asar.patch(os.path.dirname(__file__) + os.path.sep + "iogr.asr", romdata, [], True,
                                            self.asar_defines)

        if self.asar_patch_result[0]:
            return self.asar_patch_result
        else:
            asar_error_list = asar.geterrors()
            return [False, asar_error_list]

    # Returns a list of dicts of the form {'index': int, 'address': int, 'data': list of ints}
    def generate_legacy_patch(self, filename: str, settings: RandomizerData):
        self.generate_rom(filename, settings)
        if not self.asar_patch_result[0]:
            return False
        legacy_patch = []
        legacy_idx = 0
        new_rom_data = self.asar_patch_result[1]
        import ips
        ips_patch = ips.Patch.create(self.original_rom_data, new_rom_data)
        for record in ips_patch.records:
            if record.rle_size <= 0:
                payload = [x for x in record.content]
            else:
                payload = [record.content[0] for i in range(record.rle_size)]
            legacy_patch.append({'index': legacy_idx, 'address': record.offset, 'data': payload})
            legacy_idx += 1
        return json.dumps(legacy_patch)

    def generate_spoiler(self) -> str:
        return json.dumps(self.w.spoiler)

    def generate_def_dump(self) -> str:
        defkeys_sorted = []
        defs = {}
        if self.asar_patch_result[0]:
            defs = {define: val for define, val in asar.getalldefines().items() if
                    define[:7] not in ["Default", "Monster", "PlayerD", "AG_Spr_", "DG_Spr_"]}
            defkeys_sorted = sorted(defs)
        defdump = ""
        for d in defkeys_sorted:
            defdump += "!" + d + " = " + defs[d] + "\n"
        return defdump

    def generate_config_addrs(self) -> str:
        cfgkeys_sorted = []
        config_labels = {}
        if self.asar_patch_result[0]:
            labels = asar.getalllabels()
            config_labels = {label: val for label, val in labels.items() if label[:7] == "Config_"}
            cfgkeys_sorted = sorted(config_labels)
        addrdump = ""
        for d in cfgkeys_sorted:
            addrdump += d + "\t" + str(int(config_labels[d]) & 0x3fffff) + "\n"
        return addrdump

    def __get_required_statues__(self, settings: RandomizerData) -> int:
        if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            return 0
        if settings.statues.lower() == "random":
            return random.randint(0, 6)
        return int(settings.statues)
