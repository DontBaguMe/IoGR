import binascii
import hmac
import logging
import os
import random
import tempfile
from typing import BinaryIO

from .classes import World
from .constants import Constants as constants
from .quintet_comp import compress as qt_compress
from .quintet_text import encode as qt_encode
from .errors import FileNotFoundError, OffsetError
from .models.randomizer_data import RandomizerData
from .models.enums.difficulty import Difficulty
from .models.enums.goal import Goal
from .models.enums.logic import Logic
from .models.enums.enemizer import Enemizer
from .models.enums.start_location import StartLocation

VERSION = "2.3.0"

KARA_EDWARDS = 1
KARA_MINE = 2
KARA_ANGEL = 3
KARA_KRESS = 4
KARA_ANKORWAT = 5

GEMS_EASY = 35
GEMS_NORMAL = 40
GEMS_HARD = 50

INV_FULL = b"\x5c\x8e\xc9\x80"
FORCE_CHANGE = b"\x22\x30\xfd\x88"

OUTPUT_FOLDER: str = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + ".." + os.path.sep + ".." + os.path.sep + "data" + os.path.sep + "output" + os.path.sep
BIN_PATH: str = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "bin" + os.path.sep


def get_offset(rom_data):
    header = b"\x49\x4C\x4C\x55\x53\x49\x4F\x4E\x20\x4F\x46\x20\x47\x41\x49\x41\x20\x55\x53\x41"

    h_addr = rom_data.find(header)
    if h_addr < 0:
        raise OffsetError

    return h_addr - int("ffc0", 16)


def __get_data_file__(data_filename: str) -> BinaryIO:
    path = BIN_PATH + data_filename
    return open(path, "rb")


class Randomizer:
    total_bytes: int = 0
    offset: int = 0
    statues_required = 0
    inca_x = random.randint(0, 11)
    inca_y = random.randint(0, 5)

    def __init__(self, data: RandomizerData, rom_path: str):
        self.rom_path = rom_path
        self.output_folder = os.path.dirname(rom_path) + os.path.sep + "iogr" + os.path.sep
        self.settings = data
        self.logger = logging.getLogger("IOGR")

    def generate_filename(self):
        def getDifficulty(difficulty):
            if difficulty.value == Difficulty.EASY.value:
                return "_easy"
            if difficulty.value == Difficulty.NORMAL.value:
                return "_normal"
            if difficulty.value == Difficulty.HARD.value:
                return "_hard"
            if difficulty.value == Difficulty.EXTREME.value:
                return "_extreme"

        def getGoal(goal, statues):
            if goal.value is Goal.DARK_GAIA.value:
                return "_DG" + statues[0]
            if goal.value is Goal.RED_JEWEL_HUNT.value:
                return "_RJ"

        def getLogic(logic):
            if logic.value == Logic.COMPLETABLE.value:
                return "_C"
            if logic.value == Logic.BEATABLE.value:
                return "_B"
            if logic.value == Logic.CHAOS.value:
                return "_X"

        def getStartingLocation(start_location):
            if start_location.value == StartLocation.SOUTH_CAPE.value:
                return ""
            if start_location.value == StartLocation.SAFE.value:
                return "_ss"
            if start_location.value == StartLocation.UNSAFE.value:
                return "_su"
            if start_location.value == StartLocation.FORCED_UNSAFE.value:
                return "_sf"

        def getEnemizer(enemizer):
            if enemizer.value == Enemizer.NONE.value:
                return ""
            if enemizer.value == Enemizer.BALANCED.value:
                return "_eb"
            if enemizer.value == Enemizer.LIMITED.value:
                return "_el"
            if enemizer.value == Enemizer.FULL.value:
                return "_ef"
            if enemizer.value == Enemizer.INSANE.value:
                return "_ei"

        def getSwitch(switch, param):
            if switch:
                return "_" + param
            return ""

        filename = "IoGR_v" + VERSION
        filename += getDifficulty(self.settings.difficulty)
        filename += getGoal(self.settings.goal, self.settings.statues)
        filename += getLogic(self.settings.logic)
        filename += getStartingLocation(self.settings.start_location)
        filename += getSwitch(self.settings.firebird, "f")
        filename += getSwitch(self.settings.ohko, "ohko")
        filename += getEnemizer(self.settings.enemizer)
        filename += "_" + str(self.settings.seed) + ".sfc"

        return filename

    def generate_rom(self, filename: str):
        # Initiate random seed
        random.seed(self.settings.seed)
        statues_required = self.__get_required_statues__()

        f = self.__copy_original_rom__()
        rom_offset = self.offset

        ##########################################################################
        #                             Early Firebird
        ##########################################################################
        # Write new Firebird logic into unused memory location
        self.__append_file_data__("02f0c0_firebird.bin", "2f0c0", f)

        if self.settings.firebird:
            # Change firebird logic
            # Requires Shadow's form, Crystal Ring (switch #$3e) and Kara rescued (switch #$8a)
            self.__write_game_data__("2cd07", b"\x4c\xc0\xf0\xea\xea\xea", f)
            self.__write_game_data__("2cd88", b"\x4c\xe0\xf0\xea\xea\xea", f)
            self.__write_game_data__("2ce06", b"\x4c\x00\xf1\xea\xea\xea", f)
            self.__write_game_data__("2ce84", b"\x4c\x20\xea\xea\xea\xea", f)

            # Load firebird assets into every map
            self.__write_game_data__("3e03a", b"\x80\x00", f)
            self.__write_game_data__("eaf0", b"\x20\xa0\xf4\xea\xea", f)
            self.__write_game_data__("f4a0", b"\x02\x3b\x71\xb2\xf4\x80\xa9\x00\x10\x04\x12\x60", f)
            self.__write_game_data__("f4b0", b"\x02\xc1\xad\xd4\x0a\xc9\x02\x00\xf0\x01\x6b\x02\x36\x02\x39\x80\xef", f)

        ##########################################################################
        #                            Modify ROM Header
        ##########################################################################
        self.__write_game_data__("ffd1", b"\x52\x41\x4E\x44\x4F", f)  # New game title
        self.__write_game_data__("1da4c", b"\x52\x41\x4E\x44\x4F\x90\x43\x4F\x44\x45\x90", f)  # Put randomizer hash code on start screen

        hash_value = self.__build_hash__(filename)
        self.__write_game_data__("1da57", hash_value, f)

        ##########################################################################
        #                           Negate useless switches
        #                 Frees up switches for the randomizer's use
        ##########################################################################
        self.__write_game_data__("48a03", b"\x10", f)  # Switch 17 - Enter Seth's house
        self.__write_game_data__("4bca9", b"\x10", f)  # Switch 18 - Enter Will's house (1/2)
        self.__write_game_data__("4bccc", b"\x10", f)  # Switch 18 - Enter Will's house (2/2)
        self.__write_game_data__("4bcda", b"\x10", f)  # Switch 19 - Enter Lance's house
        self.__write_game_data__("4bce8", b"\x10", f)  # Switch 20 - Enter Erik's house
        self.__write_game_data__("4be3d", b"\x10", f)  # Switch 21 - Enter seaside cave
        self.__write_game_data__("4bcf6", b"\x10", f)  # Switch 23 - Complete seaside cave events
        self.__write_game_data__("9bf95", b"\x10", f)  # Switch 58 - First convo with Lilly
        self.__write_game_data__("4928a", b"\x10", f)  # Switch 62 - First convo with Lola (1/2)
        self.__write_game_data__("49873", b"\x10", f)  # Switch 62 - First convo with Lola (2/2)
        self.__write_game_data__("4e933", b"\x10", f)  # Switch 65 - Hear Elder's voice
        self.__write_game_data__("58a29", b"\x10", f)  # Switch 78 - Talk to Gold Ship queen
        self.__write_game_data__("4b067", b"\x10\x00", f)
        self.__write_game_data__("4b465", b"\x10\x00", f)
        self.__write_game_data__("4b8b6", b"\x10\x00", f)
        self.__write_game_data__("686fa", b"\x10", f)  # Switch 111 - meet Lilly at Seaside Palace
        self.__write_game_data__("78d76", b"\x10", f)
        self.__write_game_data__("78d91", b"\x10", f)
        self.__write_game_data__("7d7b1", b"\x10", f)  # Switch 159 - Mt. Kress on map

        ##########################################################################
        #                           Update map headers
        ##########################################################################
        self.__append_file_data__("0d8000_mapdata.bin", "d8000", f)

        if self.settings.difficulty.value == Difficulty.EASY.value:
            f.seek(0)
            rom = f.read()
            addr = rom.find(b"\x00\x07\x00\x02\x01", int("d8000", 16) + self.offset)
            self.__write_game_data__(addr, b"\x00\x09", f)
            addr = rom.find(b"\x00\x09\x00\x02\x08", int("d8000", 16) + self.offset)
            self.__write_game_data__(addr, b"\x00\x07", f)

        ##########################################################################
        #                        Update treasure chest data
        ##########################################################################
        self.__append_file_data__("01afa6_chests.bin", "1afa6", f)  # Remove fanfares from treasure chests
        self.__append_file_data__("01fd24_acquisition.bin", "1fd24", f)  # Update item acquisition messages and add messages for new items (29-2f)

        ##########################################################################
        #                            Update item events
        #    Adds new items that increase HP, DEF, STR and improve abilities
        ##########################################################################
        self.__write_game_data__("38491", b"\x6f\x9f\x91\x9f\x1d\x88\x3a\x88\x5f\x88\x90\x9d\xd0\x9d", f)  # Add pointers for new items @38491
        self.__append_file_data__("01dabf_startmenu.bin", "1dabf", f)  # Add start menu descriptions for new items
        self.__append_file_data__("01e132_itemdesc.bin", "1e132", f)

        # Update sprites for new items - first new item starts @108052, 7 new items
        # Points all items to unused sprite for item 4c ("76 83" in address table)
        self.__write_game_data__("108052", b"\x76\x83\x76\x83\x76\x83\x76\x83\x76\x83\x76\x83\x76\x83", f)
        self.__write_game_data__("1e12a", b"\x9f\xff\x97\x37\xb0\x01", f)  # Update item removal restriction flags

        # Write STR, Psycho Dash, and Dark Friar upgrade items
        # Replaces code for item 05 - Inca Melody @3881d
        self.__append_file_data__("03881d_item05.bin", "3881d", f)

        # Modify Prison Key, now is destroyed when used
        self.__write_game_data__("385d4", b"\x0a\x17\x0c\x18", f)
        self.__write_game_data__("385fe", b"\x02\xd5\x02\x60", f)

        # Modify Lola's Melody, now is destroyed when used and only works in Itory
        self.__append_file_data__("038bf5_item09.bin", "38bf5", f)
        self.__write_game_data__("38bbc", b"\x00", f)
        self.__write_game_data__("38bc1", b"\x00", f)

        # Modify code for Memory Melody to heal Neil's memory
        self.__append_file_data__("038f17_item0d.bin", "38f17", f)
        self.__write_game_data__("393c3", b"\x8a", f)  # Modify Magic Dust, alters switch set and text

        # Modify Blue Journal, functions as an in-game tutorial
        self.__write_game_data__("3943b", b"\xf0\x94", f)
        self.__write_game_data__("39440", b"\x10\xf2", f)
        self.__write_game_data__("39445", b"\x00\xf8", f)
        self.__write_game_data__("3944a", b"\x00\xfb", f)

        self.__write_game_data__("3944e",
                                 b"\xce" + qt_encode("       Welcome to") + b"\xcb\xcb" + qt_encode("  Bagu's Super-Helpful") +
                                 b"\xcb" + qt_encode("  In-Game Tutorial!(TM)|") +
                                 qt_encode("Whadaya wanna know about?") + b"\xcb" + qt_encode(" Beating the Game") + b"\xcb" +
                                 qt_encode(" Exploring the World") + b"\xcb" + qt_encode(" What If I'm Stuck?") + b"\xca", f)
        self.__write_game_data__("394f0", b"\xce" + qt_encode("He closed the journal.") + b"\xc0", f)

        if self.settings.goal.value == Goal.DARK_GAIA.value:
            self.__write_game_data__("3f210", b"\xce" +
                                     qt_encode("BEATING THE GAME:       You must do the following two things to beat the game:|")
                                     + qt_encode("1. RESCUE KARA          Kara is trapped in a painting! You need Magic Dust to free her.|")
                                     + qt_encode("She can be in either Edward's Prison, Diamond Mine, Angel Village, Mt. Temple, or Ankor Wat.|")
                                     + qt_encode("You can search for her yourself, or find Lance's Letter to learn where she can be found.|")
                                     + qt_encode("Once you find Kara, use the Magic Dust on her portrait to free her.|")
                                     + qt_encode("2. GATHER MYSTIC STATUES Each time you play the game, you may be required to gather Mystic Statues.|")
                                     + qt_encode("Talk to the teacher in the South Cape classroom to find out which Statues you need.|")
                                     + qt_encode("Statue 1 is in the Inca Ruins. You need the Wind Melody, Diamond Block, and both Incan Statues.|")
                                     + qt_encode("Statue 2 is in the Sky Garden. You'll need all four Crystal Balls to fight the boss Viper.|")
                                     + qt_encode("Statue 3 is in Mu. You need both Statues of Hope and both Rama Statues to fight the Vampires.|")
                                     + qt_encode("Statue 4 is in the Great Wall. You need Spin Dash and Dark Friar to face the boss Sand Fanger.|")
                                     + qt_encode("Statue 5 is in the Pyramid. You'll need all six Hieroglyphs as well as your father's journal.|")
                                     + qt_encode("Statue 6 is at the top of Babel Tower. You'll need the Aura and the Crystal Ring to get to the top.|")
                                     + qt_encode("Alternatively, if you collect enough Red Jewels to face Solid Arm, he can also take you there.|")
                                     + qt_encode("Once you've freed Kara and gathered the Statues you need, enter any Dark Space and talk to Gaia.|")
                                     + qt_encode("She will give you the option to face Dark Gaia and beat the game. Good luck, and have fun!")
                                     + b"\xc0", f)

        elif self.settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            self.__write_game_data__("3f210", b"\xce"
                                     + qt_encode("BEATING THE GAME:       It's a Red Jewel hunt! The objective is super simple:|")
                                     + qt_encode("Find the Red Jewels you need, and talk to the Jeweler. That's it!|")
                                     + qt_encode("Check the Jeweler's inventory to find out how many Red Jewels you need to beat the game.|")
                                     + qt_encode("Happy hunting!") + b"\xc0", f)

        self.__write_game_data__("3f800",
                                 b"\xce" +
                                 qt_encode("EXPLORING THE WORLD:    When you start the game, you only have access to a few locations.|") +
                                 qt_encode("As you gain more items, you will be able to visit other continents and access more locations.|") +
                                 qt_encode("Here are some of the helpful travel items you can find in the game:|") +
                                 qt_encode("- Lola's Letter         If you find this letter, read it and go see Erik in South Cape.|") +
                                 qt_encode("- The Teapot            If you use the Teapot in the Moon Tribe camp, you can travel by Sky Garden.|") +
                                 qt_encode("- Memory Melody         Play this melody in Neil's Cottage, and he'll fly you in his airplane.|") +
                                 qt_encode("- The Will              Show this document to the stable masters in either Watermia or Euro.|") +
                                 qt_encode("- The Large Roast       Give this to the hungry child in the Natives' Village.|") +
                                 qt_encode("If you're ever stuck in a location, find a Dark Space. Gaia can always return you to South Cape.") + b"\xc0",
                                 f)

        stuck = b"\xce" + qt_encode("WHAT IF I'M STUCK?      There are a lot of item locations in this game! It's easy to get stuck.|")
        stuck += qt_encode("Here are some resources that might help you:|")
        stuck += qt_encode("- Video Tutorial        Search YouTube for a video guide of this randomizer.|")
        stuck += qt_encode("- Ask the Community     Find the IoGR community on Discord! Someone will be happy to help you.|")
        if self.settings.difficulty.value == Difficulty.EASY.value:
            stuck += qt_encode("- In-Game Tracker       Enter the east-most house in South Cape to check your collection rate.|")
        else:
            stuck += qt_encode("- In-Game Tracker       (Easy mode only)|")
        stuck += qt_encode("- Check the Spoiler Log Every seed comes with a detailed list of where every item can be found.") + b"\xc0"
        self.__write_game_data__("3fb00", stuck, f)

        self.__append_file_data__("03950c_item16.bin", "3950c", f)  # Modify Lance's Letter, Prepare it to spoil Kara location
        self.__append_file_data__("03983d_item19.bin", "3983d", f)  # Modify Teapot, Now activates in Moon Tribe camp instead of Euro

        # Modify Black Glasses, now permanently worn and removed from inventory when used
        self.__write_game_data__("39881", b"\x8a\x99\x02\xcc\xf5\x02\xd5\x1c\x60\xd3\x42\x8e\x8e\x8b\x8d\x84\xa3\xa3\xac\x88\x8d\xa4\x84\x8d\xa3\x88\x85\x88\x84\xa3\x4f\xc0", f)

        # Modify Aura, now unlocks Shadow's form when used
        self.__write_game_data__("39cdc", b"\x02\xbf\xe4\x9c\x02\xcc\xb4\x60\xd3\xd6\x4c\x85\x8e\xa2\x8c\xac\xa5\x8d\x8b\x8e\x82\x8a\x84\x83\x4f\xc0", f)

        # Write 2 Jewel and 3 Jewel items; Lola's Letter now teaches Morse Code
        # Replaces and modifies code for item 25 - Lola's Letter @39d09
        self.__append_file_data__("039d09_item25.bin", "39d09", f)

        # Have fun with text in Item 26 (Father's Journal)
        self.__write_game_data__("39ea8",
                                 qt_encode("It reads: ") + b"\x2d" + qt_encode("He who is ") + b"\xcb" + qt_encode("valiant and pure of spirit...") + b"\xcf\x2d" +
                                 qt_encode("... may find the Holy Grail in the Castle of... Aauugghh") + b"\x2e\xcf" +
                                 qt_encode("Here a page is missing.") + b"\xc0", f)

        # Modify Crystal Ring, now permanently worn and removed from inventory when used
        self.__write_game_data__("39f32", b"\x3b\x9f\x02\xcc\x3e\x02\xd5\x27\x60\xd3\x41\x8b\x88\x8d\x86\xac\x81\x8b\x88\x8d\x86\x2a\xc0", f)

        # Write HP and DEF upgrade items; make the Apple non-consumable
        # Replaces and modifies code for item 28 - Apple @39f5d
        self.__append_file_data__("039f5d_item28.bin", "39f5d", f)

        # Update herb HP fill based on difficulty
        self.__seek__("", f)
        if self.settings.difficulty.value == Difficulty.EASY.value:  # Easy mode = full HP
            self.__write_game_data__("3889f", b"\x28", f)
        elif self.settings.difficulty.value == Difficulty.HARD.value:  # Hard mode = fill 4 HP
            self.__write_game_data__("3889f", b"\x04", f)
        elif self.settings.difficulty.value == Difficulty.EXTREME.value:  # Extreme mode = fill 2 HP
            self.__write_game_data__("3889f", b"\x02", f)

        # Update HP jewel HP fill based on difficulty
        if self.settings.difficulty.value == Difficulty.EASY.value:  # Easy mode = full HP
            self.__write_game_data__("39f7a", b"\x28", f)

        # Change item functionality for game variants
        self.__write_game_data__("3fce0", qt_encode("Will drops the HP Jewel. It shatters into a million pieces. Whoops.", True), f)
        self.__write_game_data__("3fd40", qt_encode("As the Jewel disappears, Will feels his strength draining", True), f)

        # In OHKO, the HP Jewels do nothing, and start @1HP
        if self.settings.ohko:
            self.__write_game_data__("8068", b"\x01", f)
            self.__write_game_data__("39f71", b"\xe0\xfc\x02\xd5\x29\x60", f)

        # In Red Jewel Madness, start @40 HP, Red Jewels remove -1 HP when used
        #    elif self.settings.red_jewel_madness:
        #        f.seek(int("8068",16)+rom_offset)
        #        f.write(b"\x28")
        #        f.seek(int("384d5",16)+rom_offset)
        #        f.write(b"\x4c\x30\xfd")
        #        f.seek(int("3fd30",16)+rom_offset)
        #        f.write(b"\x02\xbf\x40\xfd\xce\xca\x0a\xce\xce\x0a\x4c\xd9\x84")

        ##########################################################################
        #                  Update overworld map movement scripts
        #   Removes overworld animation and allows free travel within continents
        ##########################################################################
        self.__append_file_data__("03b401_mapchoices.bin", "3b401", f)  # Update map choice scripts
        self.__append_file_data__("03b955_mapdest.bin", "3b955", f)  # Update map destination array

        ##########################################################################
        #                   Rewrite Red Jewel acquisition event
        #      Makes unique code for each instance (overwrites unused code)
        ##########################################################################
        self.__append_file_data__("00f500_redjewel.bin", "f500", f)

        # Update event table instances to point to new events
        # New pointers include leading zero byte to negate event parameters
        self.__write_game_data__("c8318", b"\x00\x00\xf5\x80", f)  # South Cape: bell tower
        self.__write_game_data__("c837c", b"\x00\x80\xf5\x80", f)  # South Cape: Lance's house
        self.__write_game_data__("c8ac0", b"\x00\x00\xf6\x80", f)  # Underground Tunnel: barrel
        self.__write_game_data__("c8b50", b"\x00\x80\xf6\x80", f)  # Itory Village: logs
        self.__write_game_data__("c9546", b"\x00\x00\xf7\x80", f)  # Diamond Coast: jar
        self.__write_game_data__("c97a6", b"\x00\x80\xf7\x80", f)  # Freejia: hotel
        self.__write_game_data__("caf60", b"\x00\x00\xf8\x80", f)  # Angel Village: dance hall
        self.__write_game_data__("cb3a6", b"\x00\x80\xf8\x80", f)  # Angel Village: Ishtar's room
        self.__write_game_data__("cb563", b"\x00\x00\xf9\x80", f)  # Watermia: west Watermia
        self.__write_game_data__("cb620", b"\x00\x80\xf9\x80", f)  # Watermia: gambling house
        self.__write_game_data__("cbf55", b"\x00\x00\xfa\x80", f)  # Euro: behind house
        self.__write_game_data__("cc17c", b"\x00\x80\xfa\x80", f)  # Euro: slave room
        self.__write_game_data__("ccb14", b"\x00\x00\xfb\x80", f)  # Natives' Village: statue room
        self.__write_game_data__("cd440", b"\x00\x80\xfb\x80", f)  # Dao: east Dao
        self.__write_game_data__("cd57e", b"\x00\x00\xfc\x80", f)  # Pyramid: east entrance
        self.__write_game_data__("ce094", b"\x00\x80\xfc\x80", f)  # Babel: pillow

        ##########################################################################
        #                         Modify Game Start events
        ##########################################################################
        self.__write_game_data__("be51c", b"\x80\x00\x12\x4c\x00\xfd", f)  # Set beginning switches
        self.__append_file_data__("0bfd00_switches.bin", "bfd00", f)

        ##########################################################################
        #                         Modify South Cape events
        ##########################################################################
        self.__append_file_data__("048a94_teacher.bin", "48a94", f)  # Teacher sets switch #$38 and spoils Mystic Statues required
        self.__write_game_data__("48377", b"\x02\xd0\x10\x01\xaa\x83", f)  # Force fisherman to always appear on E side of docks, and fix inventory full
        self.__write_game_data__("48468", b"\x02\xBF\x79\x84\x02\xD4\x01\x75\x84\x02\xCC\xD7\x6B" + INV_FULL, f)
        self.__write_game_data__("49985", b"\x6b", f)  # Disable Lola Melody cutscene
        # Set flag 35 at Lola Melody acquisition
        self.__write_game_data__("499dc", b"\xeb\x99\x02\xbf\xe5\x9b\x02\xd4\x09\xf0\x99\x02\xcc\x35\x6b\x02\xbf\x94\x9d\x6b" + INV_FULL, f)

        self.__append_file_data__("04b9a5_seaside.bin", "4b9a5", f)  # Erik in Seaside Cave allows player to use Lola's Letter to travel by sea
        self.__write_game_data__("4b8b6", b"\x10\x01\x62", f)
        self.__write_game_data__("4b96a", b"\xa5", f)

        self.__append_file_data__("04fb50_tutorial.bin", "4fb50", f)  # Various NPCs can give you a tutorial
        self.__write_game_data__("49231", b"\x50\xfb", f)  # NPC in front of school
        # f.seek(int("49238",16)+rom_offset)   # Grants max stats
        # f.write(b"\xA9\x28\x00\x8D\xCA\x0A\x8D\xCE\x0A\x8D\xDC\x0A\x8D\xDE\x0A\x02\xBF\x4C\x92\x6B")
        # f.write(qt_encode("Max stats baby!",True))

        # Turns house in South Cape into item-tracking overworld map (Easy only)
        if self.settings.difficulty.value == Difficulty.EASY.value:
            self.__write_game_data__("18480", b"\x07\x90\x00\xd0\x03\x00\x00\x44", f)
            self.__write_game_data__("1854e", b"\x00\x3e\x40\x02", f)
            self.__write_game_data__("c846c", b"\x00\x01\x00\x00\xde\x86\x00\xFF\xCA", f)
            self.__append_file_data__("06dd30_collectioncheck.bin", "6dd30", f)
        else:
            self.__write_game_data__("491ed", qt_encode("This room is a lot cooler in Easy mode.", True), f)

        ##########################################################################
        #                       Modify Edward's Castle events
        ##########################################################################
        self.__write_game_data__("4c3d6", b"\x06\xc4", f)  # Shorten Edward conversation
        self.__append_file_data__("04c4fb_edward.bin", "4c4fb", f)
        self.__write_game_data__("4c4fb", b"\xd3", f)
        self.__write_game_data__("4c746", b"\x10", f)  # Talking to Edward doesn't soft lock you
        self.__append_file_data__("04d1a0_castleguard.bin", "4d1a0", f)  # Move guard to allow roast location get
        self.__write_game_data__("c8551", b"\x10", f)
        #  Update Large Roast event
        self.__write_game_data__("4d0da", b"\x02\xc0\xe1\xd0\x02\xc1\x6b\x02\xd0\x46\x00\xe9\xd0\x02\xe0\x02\xbf\x41\xd1\x02\xd4\x0a\xf6\xd0\x02\xcc\x46\x6b" + INV_FULL, f)

        self.__write_game_data__("4c297", b"\xc0", f)  # Fix hidden guard text box
        self.__write_game_data__("4c20e", b"\x02\xBF\x99\xC2\x02\xD4\x00\x1B\xC2\x02\xCC\xD8\x6B" + INV_FULL, f)

        ##########################################################################
        #                   Modify Edward's Prison/Tunnel events
        ##########################################################################
        # Skip long cutscene in prison
        self.__write_game_data__("4d209", b"\x34\xd2", f)
        self.__write_game_data__("4d234", b"\x02\xd0\x23\x00\xcf\xd2\x02\xe0", f)
        self.__write_game_data__("4d335", b"\x6b", f)

        # Move Dark Space, allows player to exit area without key
        self.__write_game_data__("18614", b"\x12\x07", f)  # Set new X/Y coordinates in exit table
        self.__write_game_data__("C8635", b"\x12\x08", f)  # Set new X/Y coordinates in event table

        # Progression triggers when Lilly is with you
        self.__write_game_data__("9aa45", b"\x6f\x00", f)
        self.__write_game_data__("9aa4b", b"\x02", f)
        self.__write_game_data__("9be74", b"\xd7\x18", f)

        # Give appearing Dark Space the option of handling an ability
        self.__write_game_data__("9bf7f", b"\xAC\xD6\x88\xA8\x00\xC0\x04\x00\x0B\x4c\x10\xf7", f)
        self.__write_game_data__("9f710", b"\xA5\x0E\x85\x24\xA9\x00\x20\x85\x0E\x02\xE0", f)
        self.__write_game_data__("c8aa2", b"\x03", f)
        self.__write_game_data__("9c037", b"\x02\xe0", f)  # Fix forced form change

        ##########################################################################
        #                            Modify Itory events
        ##########################################################################
        self.__append_file_data__("04e2a3_itory.bin", "4e2a3", f)  # Lilly event becomes Lola's Melody handler
        self.__append_file_data__("04e5ff_lilly.bin", "4e5ff", f)  # Lilly now joins if you give her the Necklace
        self.__write_game_data__("4e5a6", b"\x6f", f)
        self.__write_game_data__("4e5ac", b"\xff\xe5\x02\x0b\x6b", f)
        self.__write_game_data__("4f37b", b"\x02\xbf\x8d\xf3\x6b", f)  # Shorten Inca Statue get
        # For elder to always give spoiler
        self.__write_game_data__("4e933", b"\x10\x01", f)
        self.__write_game_data__("4e97a", b"\x02\xbf\xff\xe9\x6b", f)

        ##########################################################################
        #                          Modify Moon Tribe events
        ##########################################################################
        self.__append_file_data__("09d11e_moontribe.bin", "9d11e", f)  # Allows player to use Teapot to travel by Sky Garden

        # Lilly event serves as an overworld exit
        self.__write_game_data__("4f441", b"\x00\x00\x30\x02\x45\x14\x1c\x17\x1d\x4d\xf4\x6b\x02\x40\x00\x04\x54\xf4\x6b\x02\x66\x90\x00\x60\x02\x01\x02\xC1\x6b", f)

        # Adjust timer by mode
        timer = 20
        if self.settings.difficulty.value == Difficulty.EASY.value:
            timer += 5
        if self.settings.enemizer.value != Enemizer.NONE.value:
            timer += 5
            if self.settings.enemizer.value != Enemizer.LIMITED:
                timer += 5
        self.__write_game_data__("4f8b8", binascii.unhexlify(str(timer)), f)
        self.__write_game_data__("4fae7", b"\x02\xbf\xf9\xfa\x6b", f)  # Shorten Inca Statue get

        ##########################################################################
        #                          Modify Inca events
        ##########################################################################
        self.__write_game_data__("9cfaa", FORCE_CHANGE + b"\xA9\xF0\xEF\x1C\x5A\x06\x02\xe0", f)  # Fix forced form change
        self.__write_game_data__("c8c9c", b"\x19\x1c\x00\x4e\x85\x85\x00", f)  # Put Gold Ship captain at Inca entrance

        ##########################################################################
        #                          Modify Gold Ship events
        ##########################################################################
        # Move Seth from deserted ship to gold ship, allows player to acquire item
        # Write pointer to Seth event in new map
        self.__write_game_data__("c945c", b"\x0b\x24\x00\x3e\x96\x85\x00\xff\xca", f)
        self.__write_game_data__("c805a", b"\x65", f)
        self.__write_game_data__("59643", b"\x10\x00", f)  # Modify Seth event to ignore switch conditions
        self.__write_game_data__("59665", INV_FULL, f)  # Add in inventory full text
        # Entering Gold Ship doesn't lock out Castoth
        self.__write_game_data__("58188", b"\x02\xc1\x02\xc1", f)
        self.__write_game_data__("18a09", b"\xd0\x00\x40\x02\x03", f)
        self.__write_game_data__("583cb", b"\x10", f)  # Have ladder NPC move aside only if Mystic Statue has been acquired

        # Modify queen switches
        self.__write_game_data__("58a04", b"\x10\x00", f)
        self.__write_game_data__("58a1f", b"\x10", f)

        # Have crow's nest NPC warp directly to Diamond Coast
        # Also checks for Castoth being defeated
        self.__append_file_data__("0584a9_goldship.bin", "584a9", f)
        self.__write_game_data__("586a3", b"\x02\x26\x30\x48\x00\x20\x00\x03\x00\x21", f)  # Sleeping sends player to Diamond Coast

        ##########################################################################
        #                        Modify Diamond Coast events
        ##########################################################################
        # Allow Turbo to contact Seth
        self.__write_game_data__("c953e", b"\x01", f)
        self.__write_game_data__("5aa76", b"\x00\xff", f)
        self.__write_game_data__("5ff00", b"\x02\xCC\x01\x02\xD0\x11\x01\x0E\xFF\x02\xBF\x60\xFF\x6B\x02\xD0\x12\x01\x1B\xFF\x02\xcc\x12\x02\xBF\x1F\xFF\x5C\xBD\xB9\x84\xd3" +
                                 qt_encode("Woof woof!") + b"\xcb" + qt_encode("(Oh good, you know Morse Code. Let's see what Seth's up to:)") + b"\xc0" +
                                 b"\xd3" + qt_encode("Woof woof!") + b"\xcb" + qt_encode("(You don't happen to know Morse Code, do you?)") + b"\xc0", f)
        # Kara event serves as an overworld exit
        self.__write_game_data__("5aa9e", b"\x00\x00\x30\x02\x45\x03\x00\x06\x01\xaa\xaa\x6b\x02\x40\x00\x08\xb1\xaa\x6b\x02\x66\x50\x02\x50\x03\x07\x02\xC1\x6b", f)

        ##########################################################################
        #                           Modify Freejia events
        ##########################################################################
        # Trash can 1 gives you an item instead of a status upgrade
        # NOTE: This cannibalizes the following event @5cfbc (locked door)
        self.__append_file_data__("05cf85_freejia.bin", "5cf85", f)
        self.__write_game_data__("5cf37", b"\x02\xBF\x49\xCF\x02\xD4\x12\x44\xCF\x02\xCC\x53\x6B" + INV_FULL, f)  # Give full inventory text to trash can 2

        # Redirect event table to bypass deleted event
        # Changes locked door to a normal door
        self.__write_game_data__("c95bb", b"\xf3\xc5\x80", f)

        # Update NPC dialogue to acknowledge change
        self.__write_game_data__("5c331",
                                 b"\x42\xa2\x80\xa0\x2b\xac\x48\xac\xd6\xae\xa4\x87\x84\xac\xd7\x58\xcb\xa5\x8d\x8b\x8e\x82\x8a\x84\x83\xac\x80\x86\x80\x88\x8d\x2a\x2a\x2a\xc0", f)
        self.__write_game_data__("5b6df", INV_FULL, f)  # Add inventory full option to Creepy Guy event
        self.__write_game_data__("5bfdb", b"\xde\xbf", f)  # Alter laborer text

        # Have some fun with snitch item text
        self.__write_game_data__("5b8bc", b"\x62", f)
        self.__write_game_data__("5b925", b"\x88\xa4\x84\x8c\x2a\xcb\xac\x69\x84\xa3\x2b\xac\x48\x0e\x8c\xac\x80\xac\x81\x80\x83\xac\xa0\x84\xa2\xa3\x8e\x8d" +
                                 b"\xcb\xac\x63\x8d\x88\xa4\x82\x87\x84\xa3\xac\x86\x84\xa4\xac\xa3\xa4\x88\xa4\x82\x87\x84\xa3\x2b\xac\xa9\x8e\xca", f)

        ##########################################################################
        #                        Modify Diamond Mine events
        ##########################################################################
        self.__write_game_data__("5d739", b"\x4c\x5d\xd8\x85", f)  # Trapped laborer gives you an item instead of sending Jewels to Jeweler
        self.__append_file_data__("05d7e2_trappedlaborer.bin", "5d7e3", f)

        # Shorten laborer items
        self.__write_game_data__("aa753", b"\xef\xa7", f)
        self.__write_game_data__("aa75a", b"\x6b", f)
        self.__write_game_data__("aa773", b"\x5c\xa8", f)
        self.__write_game_data__("aa77a", b"\x6b", f)
        self.__write_game_data__("5d4d8", b"\x02\xbf\xeb\xd4\x02\xe0", f)  # Shorten morgue item get
        self.__write_game_data__("5d24f", b"\x6b", f)  # Cut out Sam's song
        self.__write_game_data__("5d62f", b"\xAC\xD6\x88\x00\x2B\xA5\x0E\x85\x24\xA9\x00\x20\x85\x0E\x02\xE0", f)  # Give appearing Dark Space the option of handling an ability

        ##########################################################################
        #                       Modify Neil's Cottage events
        ##########################################################################
        self.__append_file_data__("05d89a_neilscottage.bin", "5d89a", f)  # Allow travel by plane with the Memory Melody
        # Invention event serves as an overworld exit
        self.__write_game_data__("5e305", b"\x00\x00\x30\x02\x45\x07\x0d\x0a\x0e\x11\xe3\x6b\x02\x40\x00\x04\x18\xe3\x6b\x02\x66\x70\x02\x70\x02\x07\x02\xC1\x6b", f)

        ##########################################################################
        #                            Modify Nazca events
        ##########################################################################
        self.__append_file_data__("05e647_nazca.bin", "5e647", f)  # Speedup warp sequence to Sky Garden
        # Allow exit to world map
        self.__write_game_data__("5e80c", b"\x02\x66\x10\x03\x90\x02\x07\x02\xC1\x6B", f)

        ##########################################################################
        #                          Modify Sky Garden events
        ##########################################################################
        self.__append_file_data__("05f356_skygarden.bin", "5f356", f)  # Allow travel from Sky Garden to other locations
        # Instant form change & warp to Seaside Palace if Viper is defeated
        self.__write_game_data__("ace9b", b"\x4c\x90\xfd", f)
        self.__write_game_data__("acecb", b"\x01\x02\x26\x5a\x90\x00\x70\x00\x83\x00\x14\x02\xc1\x6b", f)
        self.__append_file_data__("0afd90_viperchange.bin", "afd90", f)

        ##########################################################################
        #                       Modify Seaside Palace events
        ##########################################################################
        self.__write_game_data__("191de", b"\x04\x06\x02\x03\x69\xa0\x02\x38\x00\x00\x00\x13", f)  # Add exit from Mu passage to Angel Village @191de
        # Temporarily put exit one tile south
        # f.write(b"\x04\x05\x02\x03\x69\xa0\x02\x38\x00\x00\x00\x13")  # Change to this if map is ever updated

        self.__append_file_data__("1e28a5_mupassage.bin", "1e28a5", f)  # Replace Mu Passage map with one that includes a door to Angel Village
        self.__write_game_data__("68b01", b"\x6b", f)  # Shorten NPC item get

        # Purification event won't softlock if you don't have Lilly
        self.__write_game_data__("69406", b"\x10", f)
        self.__write_game_data__("6941a", b"\x01\x02\xc1\x02\xc1", f)

        # Remove Lilly text when Mu door opens
        self.__write_game_data__("39174", b"\x60", f)
        self.__write_game_data__("391d7", b"\xc0", f)

        # Allow player to open Mu door from the back
        self.__append_file_data__("069739_mudoor.bin", "69739", f)

        # Remove fanfare from coffin item get
        self.__write_game_data__("69232", b"\x9e\x93\x4c\x61\x92", f)
        self.__write_game_data__("69267", b"\x80\x04", f)

        # Make coffin spoiler re-readable
        self.__write_game_data__("68ff3", b"\xf5\x8f", f)
        self.__write_game_data__("68ffb", b"\x70\xe5", f)
        self.__write_game_data__("69092", b"\x02\xce\x01\x02\x25\x2F\x0A\x4c\xfd\x8f", f)
        self.__write_game_data__("6e570", b"\x02\xD1\x3A\x01\x01\x8A\xE5\x02\xD0\x6F\x01\x82\xE5\x02\xBF\xA7\x90\x6B\x02\xBF\xCF\x90\x02\xCC\x01\x6B\x02\xBF\x67\x91\x6B", f)

        ##########################################################################
        #                             Modify Mu events
        ##########################################################################
        self.__write_game_data__("698cd", INV_FULL, f)  # Add "inventory full" option to Statue of Hope items

        # Shorten Statue of Hope get
        self.__write_game_data__("698b8", b"\x02\xBF\xD2\x98\x02\xD4\x28\xCD\x98\x02\xCC\x79\x6B", f)
        self.__write_game_data__("69960", b"\x02\xBF\x75\x99\x02\xD4\x1E\xCD\x98\x02\xCC\x7F\x6B", f)

        # Shorten Rama statue event
        self.__write_game_data__("69e50", b"\x10", f)
        self.__write_game_data__("69f26", b"\x00", f)

        # Text in Hope Room
        self.__write_game_data__("69baa", qt_encode("Hey.", True), f)

        # Spirits in Rama statue room can't lock you
        self.__write_game_data__("6a07a", b"\x6b", f)
        self.__write_game_data__("6a082", b"\x6b", f)
        self.__write_game_data__("6a08a", b"\x6b", f)
        self.__write_game_data__("6a092", b"\x6b", f)
        self.__write_game_data__("6a09a", b"\x6b", f)
        self.__write_game_data__("6a0a2", b"\x6b", f)

        # Move exits around to make Vampires required for Statue
        self.__write_game_data__("193ea", b"\x5f\x80\x00\x50\x00\x03\x00\x44", f)
        self.__write_game_data__("193f8", b"\x65\xb8\x00\x80\x02\x03\x00\x44", f)
        self.__write_game_data__("69c62", b"\x67\x78\x01\xd0\x01\x80\x01\x22", f)
        self.__write_game_data__("6a4c9", b"\x02\x26\x66\xf8\x00\xd8\x01\x00\x00\x22\x02\xc1\x6b", f)

        # Instant form change after Vamps are defeated
        self.__write_game_data__("6a43b", b"\x4c\x00\xe5", f)
        self.__append_file_data__("06e500_vampchange.bin", "6e500", f)

        ##########################################################################
        #                       Modify Angel Village events
        ##########################################################################
        # Add exit from Angel Village to Mu passage @1941a
        self.__write_game_data__("1941a", b"\x2a\x05\x01\x01\x5e\x48\x00\x90\x00\x01\x00\x14", f)
        # f.write(b"\x2a\x05\x01\x01\x5e\x48\x00\x80\x00\x01\x00\x14")  # Change to this if map is ever updated

        # Update sign to read "Passage to Mu"
        self.__append_file_data__("06ba36_angelsign.bin", "6ba36", f)

        # Entering this area clears your enemy defeat count and forces change to Will
        self.__write_game_data__("6bff7", b"\x00\x00\x30\x02\x40\x01\x0F\x01\xC0\x6b\xA0\x00\x00\xA9\x00\x00\x99\x80\x0A\xC8\xC8\xC0\x20\x00\xD0\xF6" +
                                 FORCE_CHANGE + b"\x02\xE0", f)

        # Insert new arrangement for map 109, takes out rock to prevent spin dash softlock
        self.__append_file_data__("1a5a37_angelmap.bin", "1a5a37", f)

        # Ishtar's game never closes
        self.__write_game_data__("6d9fc", b"\x10", f)
        self.__write_game_data__("6cede", b"\x9c\xa6\x0a\x6b", f)
        self.__write_game_data__("6cef6", b"\x40\x86\x80\x88\x8d\x4f\xc0", f)

        ##########################################################################
        #                           Modfy Watermia events
        ##########################################################################
        # Allow NPC to contact Seth
        self.__write_game_data__("78542", b"\x50\xe9", f)
        self.__write_game_data__("7e950", b"\x02\xD0\x11\x01\x5B\xE9\x02\xBF\xb8\xe9\x6B\x02\xD0\x12\x01\x68\xE9" +
                                 b"\x02\xcc\x12\x02\xBF\x6c\xE9\x5C\xBD\xB9\x84" +
                                 b"\xd3" + qt_encode("Oh, you know Bagu? Then I can help you cross.") + b"\xcb" +
                                 qt_encode("(And by Bagu I mean Morse Code.)") + b"\xc0" +
                                 b"\xd3" + qt_encode("Only town folk may cross this river!") + b"\xcb" +
                                 qt_encode("(Or, if you can talk to fish, I guess.)") + b"\xc0",
                                 f)

        # Allow for travel from  Watermia to Euro
        # Update address pointer
        self.__write_game_data__("78544", b"\x69", f)

        self.__append_file_data__("078569_watermia1.bin", "78569", f)  # Update event address pointers
        self.__append_file_data__("0786c1_watermia2.bin", "786c1", f)  # Change textbox contents
        self.__append_file_data__("079237_russianglass.bin", "79237", f)  # Russian Glass NPC just gives you the item

        # Fix Lance item get text
        self.__write_game_data__("7ad28", INV_FULL, f)

        ##########################################################################
        #                          Modify Great Wall events
        ##########################################################################
        # Rewrite Necklace Stone acquisition event
        # Fill block with new item acquisition code (2 items)
        self.__append_file_data__("07b59e_necklace.bin", "7b59e", f)

        # Update event table instance to point to new events
        # New pointers include leading zero byte to negate event parameters
        self.__write_game_data__("cb822", b"\x00\x9e\xb5\x87", f)  # First stone, map 130
        self.__write_game_data__("cb94a", b"\x00\xfe\xb5\x87", f)  # Second stone, map 131

        # Entering wrong door in 2nd map area doesn't softlock you
        self.__write_game_data__("19a4c", b"\x84", f)

        # Give appearing Dark Space the option of handling an ability
        self.__write_game_data__("7be0b", b"\xAC\xD6\x88\xC8\x01\x80\x02\x00\x2B\xA5\x0E\x85\x24\xA9\x00\x20\x85\x0E\x02\xE0", f)
        self.__write_game_data__("cbc60", b"\x03", f)

        # Exit after Sand Fanger takes you back to start
        self.__write_game_data__("19c84", b"\x82\x10\x00\x90\x00\x07\x00\x18", f)

        ##########################################################################
        #                            Modify Euro events
        ##########################################################################
        # Allow travel from Euro to Watermia
        self.__append_file_data__("07c432_euro1.bin", "7c432", f)  # Update event address pointers
        self.__append_file_data__("07c4d0_euro2.bin", "7c4d0", f)  # Change textbox contents
        self.__write_game_data__("7c482", qt_encode("A moose once bit my sister.", True), f)

        self.__append_file_data__("07e398_euroneil.bin", "7e398", f)  # Neil in Euro
        self.__write_game_data__("7e37f", b"\x14\x00", f)
        self.__write_game_data__("7e394", b"\x10\x00", f)

        self.__append_file_data__("07e517_euroitem.bin", "7e517", f)  # Hidden house replaces STR upgrade with item acquisition
        self.__write_game_data__("7d5e1", b"\x00\x01", f)  # Speed up store line

        # Change vendor event, allows for only one item acquisition
        # Note: this cannibalizes the following event
        self.__write_game_data__("7c0a7", b"\x02\xd0\x9a\x01\xba\xc0\x02\xbf\xf3\xc0\x02\xd4\x28\xbf\xc0\x02\xcc\x9a\x6b\x02\xbf\xdd\xc0\x6b" + INV_FULL, f)
        self.__write_game_data__("7c09b", b"\xc4", f)  # Change pointer for cannibalized event

        # Store replaces status upgrades with item acquisition
        # HP upgrade
        self.__write_game_data__("7cd03", b"\x02\xd0\xf0\x01\x32\xcd\x02\xc0\x10\xcd\x02\xc1\x6b\x02\xd4\x29\x20\xcd\x02\xcc\xf0\x02\xbf\x39\xcd\x02\xe0", f)
        # Dark Friar upgrade
        self.__write_game_data__("7cdf7", b"\x02\xd4\x2d\x05\xce\x02\xcc\xf1\x02\xbf\x28\xce\x02\xe0\x02\xbf\x3e\xce\x6b", f)

        # Old men text no longer checks for Teapot
        self.__write_game_data__("7d60a", b"\x14\xd6", f)
        self.__write_game_data__("7d7a5", b"\xbd\xd7", f)

        # Various NPC dialogue
        self.__write_game_data__("7d6db", b"\x2A\xD0\xC8\xC9\x1E\xC2\x0B\xC2\x03" + qt_encode("It could be carried by an African swallow!") +
                                 b"\xCF\xC2\x03\xC2\x04" + qt_encode("Oh yeah, an African swallow maybe, but not a European swallow, that's my point!") +
                                 b"\xc0", f)
        self.__write_game_data__("7d622", qt_encode("Rofsky: Wait a minute, supposing two swallows carried it together?...") + b"\xc0", f)
        self.__write_game_data__("7c860", b"\xce" + qt_encode("Nobody expects the Spanish Inquisition!") + b"\xc0", f)
        self.__write_game_data__("7c142", qt_encode("I am no longer infected.", True), f)
        self.__write_game_data__("7c160", qt_encode("My hovercraft is full of eels.", True), f)
        self.__write_game_data__("7c182", qt_encode("... w-i-i-i-i-ith... a herring!!", True), f)
        self.__write_game_data__("7c1b6", qt_encode("It's only a wafer-thin mint, sir...", True), f)
        self.__write_game_data__("7c1dc", b"\xd3" + qt_encode("The mill's closed. There's no more work. We're destitute.|") +
                                 qt_encode("I've got no option but to sell you all for scientific experiments.") + b"\xc0", f)
        self.__write_game_data__("7c3d4", qt_encode("You're a looney.", True), f)

        ##########################################################################
        #                        Modify Native Village events
        ##########################################################################
        # Native can guide you to Dao if you give him the roast
        self.__append_file_data__("088fc4_natives.bin", "88fc4", f)
        # Change event pointers for cannibalized NPC code
        self.__write_game_data__("cca93", b"\x88\x8f\x88", f)

        ##########################################################################
        #                         Modify Ankor Wat events
        ##########################################################################
        # Modify Gorgon Flower event, make it a simple item get
        self.__append_file_data__("089abf_ankorwat.bin", "89abf", f)

        # Shorten black glasses get
        self.__write_game_data__("89fa9", b"\x02\xe0", f)

        # Bright room looks at switch 4f rather than equipment
        self.__append_file_data__("089a31_ankorwat.bin", "89a31", f)

        ##########################################################################
        #                            Modify Dao events
        ##########################################################################
        # Snake game grants an item instead of sending Jewels to the Jeweler
        self.__append_file_data__("08b010_snakegame.bin", "8b010", f)
        # Neil in Dao
        self.__append_file_data__("08a5bd_daoneil.bin", "8a5bd", f)
        self.__write_game_data__("8a5b3", b"\x14\x00", f)

        # Allow travel back to Natives' Village
        self.__write_game_data__("8b16d", b"\x4c\x50\xfe", f)
        self.__write_game_data__("8fe50", b"\x02\xBF\x71\xFE\x02\xBE\x02\x01\x5A\xFE\x60\xFE\x60\xFE\x65\xFE" +
                                 b"\x02\xBF\x93\xFE\x6B\x02\x26\xAC\xC0\x01\xD0\x01\x06\x00\x22\x02\xC5" +
                                 b"\xd3" + qt_encode("Go to Natives' Village?") + b"\xcb\xac" +
                                 qt_encode("No") + b"\xcb\xac" + qt_encode("Yes") + b"\xca" +
                                 b"\xce" + qt_encode("Come back anytime!") + b"\xc0", f)

        # Modify two-item acquisition event
        self.__write_game_data__("8b1bb", b"\x6b", f)
        self.__write_game_data__("8b189", b"\xe0\xfd", f)
        self.__write_game_data__("8fde0", b"\xD3\x4b\x8e\x8b\x80\x0e\xa3\xac\x4b\x84\xa4\xa4\x84\xa2\xCB\x49\x8e\xa5\xa2\x8d\x80\x8b\xac\xac\xac\xac\xac\xac\xCF\xCE" +
                                 qt_encode("If you want a guide to take you to the Natives' Village, I can get one for you.") + b"\xc0", f)

        # Spirit appears only after you defeat Mummy Queen or Solid Arm
        self.__write_game_data__("980cb", b"\x4c\xb0\xf6", f)
        self.__write_game_data__("9f6b0", b"\x02\xd0\xf6\x01\xd1\x80\x02\xd1\x79\x01\x01\xd1\x80\x02\xe0", f)

        ##########################################################################
        #                           Modify Pyramid events
        ##########################################################################
        # Can give journal to the guide in hieroglyph room
        self.__write_game_data__("8c207", b"\x0E\xC2\x02\x0B\x02\xC1\x6B\x02\xD0\xEF\x01\x1E\xC2\x02\xD6\x26\x22\xC2\x02\xBF\x2D\xC2" +
                                 b"\x6B\x5C\x08\xF2\x83\x02\xCC\xEF\x02\xD5\x26\x02\xBF\x7F\xC2\x6B" +
                                 qt_encode("If you have any information about the pyramid, I'd be happy to hold onto it for you.", True) +
                                 qt_encode("I'll hold onto that journal for you. Come back anytime if you want to read it.", True), f)
        self.__write_game_data__("3f208", b"\x02\xbf\x1a\x9e\x6b", f)

        # Shorten hieroglyph get
        self.__write_game_data__("8c7b8", b"\x6b", f)
        self.__write_game_data__("8c87f", b"\x6b", f)
        self.__write_game_data__("8c927", b"\x6b", f)
        self.__write_game_data__("8c9cf", b"\x6b", f)
        self.__write_game_data__("8ca77", b"\x6b", f)
        self.__write_game_data__("8cb1f", b"\x6b", f)

        ##########################################################################
        #                            Modify Babel events
        ##########################################################################
        # Move Dark Space in Babel Tower from map 224 to map 223
        # Allows player to exit Babel without crystal ring
        # Modify address pointer for Maps 224 in exit table
        self.__write_game_data__("183f4", b"\xea", f)

        self.__append_file_data__("01a7c2_babel.bin", "1a7c2", f)  # Move Dark Space exit data to Map 223
        self.__write_game_data__("c81c0", b"\xa2\xe0\xe3\xe0\x0f\xe1\x2d\xe1", f)  # Modify address pointer for Maps 224-227 in event table
        self.__write_game_data__("bf8c4", b"\x47\xfa", f)  # Assign new Dark Space correct overworld name
        # Move Dark Space event data to Map 223
        # Also move spirits for entrance warp
        self.__append_file_data__("0ce099_babel.bin", "ce099", f)

        # Spirits can warp you back to start
        self.__write_game_data__("99b69", b"\x76\x9B\x76\x9B\x76\x9B\x76\x9B", f)
        self.__write_game_data__("99b7a", b"\x02\xBE\x02\x01\x80\x9B\x86\x9B\x86\x9B\x16\x9D\x02\xBF\x95\x9C\x6B", f)
        self.__write_game_data__("99c1e", b"\xd3" + qt_encode("What'd you like to do?") + b"\xcb\xac" + qt_encode("Git gud") + b"\xcb\xac" + qt_encode("Run away!") + b"\xca", f)
        self.__write_game_data__("99c95", b"\xce" + qt_encode("Darn straight.") + b"\xc0", f)
        self.__write_game_data__("99d16", b"\x02\x26\xDE\x78\x00\xC0\x00\x00\x00\x11\x02\xC5", f)

        # Change switch conditions for Crystal Ring item
        self.__write_game_data__("9999b", b"\x4c\xd0\xf6", f)
        self.__write_game_data__("9f6d0", b"\x02\xd0\xdc\x00\xa0\x99\x02\xd0\x3e\x00\xa0\x99\x02\xd0\xb4\x01\x9a\x99\x4c\xa0\x99", f)
        self.__write_game_data__("999aa", b"\x4c\xf0\xf6", f)
        self.__write_game_data__("9f6f0", b"\x02\xd0\xdc\x01\x9a\x99\x4c\xaf\x99", f)
        self.__write_game_data__("99a49", b"\x02\xbf\xe4\x9a\x02\xd4\x27\x57\x9a\x02\xcc\xdc\x02\xe0" + INV_FULL, f)
        # Change text
        self.__write_game_data__("99a70", qt_encode("Well, lookie there.", True), f)

        # Olman event no longer warps you out of the room
        self.__write_game_data__("98891", b"\x02\x0b\x6b", f)

        # Shorten Olman text boxes
        self.__write_game_data__("9884c", b"\x01\x00", f)
        self.__write_game_data__("98903", qt_encode("heya.", True), f)
        self.__write_game_data__("989a2", qt_encode("you've been busy, huh?", True), f)

        # Speed up roof sequence
        self.__write_game_data__("98fad", b"\x02\xcc\x0e\x02\xcc\x0f\x6b", f)

        ##########################################################################
        #                      Modify Jeweler's Mansion events
        ##########################################################################
        # Set exit warp to Dao
        self.__write_game_data__("8fcb2", b"\x02\x26\xc3\x40\x01\x88\x00\x00\x00\x23", f)
        # Set flag when Solid Arm is killed
        self.__write_game_data__("8fa25", b"\x4c\x20\xfd", f)
        self.__write_game_data__("8fd20", b"\x02\xcc\xf6\x02\x26\xe3\x80\x02\xa0\x01\x80\x10\x23\x02\xe0", f)

        # Solid Arm text
        self.__write_game_data__("8fa32", qt_encode("Weave a circle round him") + b"\xcb" + qt_encode("  thrice,") +
                                 b"\xcb" + qt_encode("And close your eyes with") + b"\xcb" + qt_encode("  holy dread,") +
                                 b"\xcf" + qt_encode("For he on honey-dew hath") + b"\xcb" + qt_encode("  fed,") +
                                 b"\xcb" + qt_encode("And drunk the milk of ") + b"\xcb" + qt_encode("  Paradise.") + b"\xc0", f)

        self.__write_game_data__("8fbc9", b"\xd5\x02" +
                                 qt_encode("Ed, what an ugly thing to say... does this mean we're not friends anymore?|") +
                                 qt_encode("You know, Ed, if I thought you weren't my friend, I just don't think I could bear it.") + b"\xc0", f)

        ##########################################################################
        #                           Modify Ending cutscene
        ##########################################################################
        # Custom credits
        str_endpause = b"\xC9\xB4\xC8\xCA"

        self.__write_game_data__("bd566", b"\xCB" + qt_encode("    Thanks a million.") + str_endpause, f)
        self.__write_game_data__("bd5ac", b"\xCB" + qt_encode(" Extra special thanks to") + b"\xCB" + qt_encode("       manafreak") +
                                 b"\xC9\x78\xCE\xCB" + qt_encode(" This project would not") + b"\xCB" + qt_encode("  exist without his work.") +
                                 b"\xC9\x78\xCE\xCB" + qt_encode("     gaiathecreator") + b"\xCB" + qt_encode("      .blogspot.com") + str_endpause, f)
        self.__write_game_data__("bd71c", qt_encode("    Created by") + b"\xCB" + qt_encode("       DontBaguMe") + str_endpause, f)
        self.__write_game_data__("bd74f", qt_encode("Additional Development By") + b"\xCB" + qt_encode("    bryon w and Raeven0") + b"\xCB" +
                                 qt_encode("  EmoTracker by Apokalysme") + b"\xC9\x78\xCE\xCB" + qt_encode("   Thanks to all the") + b"\xCB" +
                                 qt_encode("  amazing playtesters!") + str_endpause, f)
        self.__write_game_data__("bdee2", b"\xCB" + qt_encode(" That's it, show's over.") + str_endpause, f)
        self.__write_game_data__("bda09", b"\xCB" + qt_encode("   Thanks for playing!") + str_endpause, f)
        self.__write_game_data__("bdca5", qt_encode("Wait a minute...") + b"\xCB" + qt_encode("what happened to Hamlet?") + str_endpause, f)
        self.__write_game_data__("bdd48", qt_encode("Um...") + b"\xCB" + qt_encode("I wouldn't worry about") + b"\xCB" + qt_encode("that too much...") + str_endpause, f)
        self.__write_game_data__("bddf6", qt_encode("Well, but...") + str_endpause, f)
        self.__write_game_data__("bde16", qt_encode("Shh... here,") + b"\xCB" + qt_encode("have some bacon.") + str_endpause, f)

        # Thank the playtesters
        self.__write_game_data__("be056", b"\x80\xfa", f)
        self.__write_game_data__("bfa80", b"\xD3\xD2\x00\xD5\x00" +
                                 qt_encode("Contributors and Testers:") +
                                 b"\xCB" + qt_encode("-Alchemic   -Austin21300")
                                 + b"\xCB" + qt_encode("-Atlas      -BOWIEtheHERO")
                                 + b"\xCB" + qt_encode("-Bonzaibier -BubbaSWalter")
                                 + b"\xC9\xB4\xCE" + qt_encode("-Crazyhaze  -DerTolleIgel")
                                 + b"\xCB" + qt_encode("-DoodSF     -djtifaheart")
                                 + b"\xCB" + qt_encode("-Eppy37     -Keypaladin")
                                 + b"\xCB" + qt_encode("-Lassic")
                                 + b"\xC9\xB4\xCE" + qt_encode("-Le Hulk    -Plan")
                                 + b"\xCB" + qt_encode("-manafreak  -Pozzum Senpai")
                                 + b"\xCB" + qt_encode("-Mikan      -roeya")
                                 + b"\xCB" + qt_encode("-Mr Freet")
                                 + b"\xC9\xB4\xCE" + qt_encode("-Scheris    -SmashManiac")
                                 + b"\xCB" + qt_encode("-SDiezal    -solarcell007")
                                 + b"\xCB" + qt_encode("-Skarsnik   -steve hacks")
                                 + b"\xCB" + qt_encode("-Skipsy")
                                 + b"\xC9\xB4\xCE" + qt_encode("-Sye990     -Verallix")
                                 + b"\xCB" + qt_encode("-Tsurana    -Volor") + b"\xCB"
                                 + qt_encode("-Tymekeeper -Veetorp")
                                 + b"\xC9\xB4\xCE" + qt_encode("-Voranthe   -Xyrcord")
                                 + b"\xCB" + qt_encode("-Wilddin    -Z4t0x")
                                 + b"\xCB" + qt_encode("-wormsofcan -ZockerStu")
                                 + b"\xC9\xB4\xCE\xCB" + qt_encode("  Thank you all so much!") + b"\xCB" + qt_encode("     This was so fun!") + b"\xC9\xF0\xC8\xCA", f)

        ##########################################################################
        #                           Modify Jeweler event
        ##########################################################################
        self.__append_file_data__("08cec9_jeweler.bin", "8cec9", f)  # Replace status upgrades with item acquisitions
        self.__append_file_data__("08fd90_jeweler2.bin", "8fd90", f)  # Allow jeweler to take 2- and 3-jewel items
        self.__write_game_data__("8cea5", b"\x10\x00", f)  # Jeweler doesn't disappear when defeated

        # Jeweler warps you to credits for Red Jewel hunts
        if self.settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            self.__write_game_data__("8d32a", b"\xE5\x00\x00\x00\x00\x00\x00\x11", f)
            self.__write_game_data__("8d2d8", qt_encode("Beat the game"), f)

        ##########################################################################
        #                          Update dark space code
        ##########################################################################
        # Allow player to return to South Cape at any time
        # Also, checks for end game state and warps to final boss
        self.__append_file_data__("08db07_darkspace.bin", "8db07", f)
        self.__write_game_data__("8eb81", b"\xc0", f)  # Shorten ability acquisition text

        # Cut out ability explanation text
        self.__write_game_data__("8eb15", b"\xa4\x26\xa9\x00\x00\x99\x24\x00\x02\x04\x16\x02\xda\x01\xa9\xf0\xff\x1c\x5a\x06\x02\xe0", f)

        # Remove abilities from all Dark Spaces
        self.__write_game_data__("c8b34", b"\x01", f)  # Itory Village (Psycho Dash)
        self.__write_game_data__("c9b49", b"\x03", f)  # Diamond Mine (Dark Friar)
        self.__write_game_data__("caa99", b"\x03", f)  # Mu (Psycho Slide)
        self.__write_game_data__("cbb80", b"\x03", f)  # Great Wall (Spin Dash)
        self.__write_game_data__("cc7b8", b"\x03", f)  # Mt. Temple (Aura Barrier)
        self.__write_game_data__("cd0a2", b"\x03", f)  # Ankor Wat (Earthquaker)

        # Insert subroutine that can force change back to Will
        self.__append_file_data__("08fd30_forcechange.bin", "8fd30", f)

        ##########################################################################
        #                          Fix special attacks
        ##########################################################################
        # Earthquaker no longer charges; Aura Barrier can be used w/o Friar
        self.__write_game_data__("2b871", b"\x30", f)

        # Insert new code to explicitly check for Psycho Dash and Friar
        self.__write_game_data__("2f090",
                                 b"\xAD\xA2\x0A\x89\x01\x00\xF0\x06\xA9\xA0\xBE\x20\x26\xB9\x4C\x01\xB9" +  # Psycho Dash @2f090
                                 b"\xAD\xA2\x0A\x89\x10\x00\xF0\x06\xA9\x3B\xBB\x20\x26\xB9\x4C\x01\xB9",  # Dark Friar @2f0a1
                                 f)

        # Insert jumps to new code
        self.__write_game_data__("2b858", b"\x4c\x90\xf0", f)  # Psycho Dash
        self.__write_game_data__("2b8df", b"\x4c\xa1\xf0", f)  # Dark Friar

        ##########################################################################
        #                      Disable NPCs in various maps
        ##########################################################################
        # School
        self.__write_game_data__("48d25", b"\xe0\x6b", f)  # Lance
        self.__write_game_data__("48d72", b"\xe0\x6b", f)  # Seth
        self.__write_game_data__("48d99", b"\xe0\x6b", f)  # Erik

        # Seaside cave
        self.__write_game_data__("4afb6", b"\xe0\x6b", f)  # Playing cards
        self.__write_game_data__("4b06c", b"\xe0\x6b", f)  # Lance
        self.__write_game_data__("4b459", b"\xe0\x6b", f)  # Seth

        # Edward's Castle
        self.__write_game_data__("4cb5e", b"\xe0\x6b", f)  # Kara
        self.__write_game_data__("9bc37", b"\x02\xe0\x6b", f)  # Lilly's flower

        # Itory Village
        self.__write_game_data__("4e06e", b"\xe0\x6b", f)  # Kara
        self.__write_game_data__("4f0a7", b"\xe0\x6b", f)  # Lola
        self.__write_game_data__("4ef78", b"\xe0\x6b", f)  # Bill

        # Lilly's House
        self.__write_game_data__("4e1b7", b"\xe0\x6b", f)  # Kara

        # Moon Tribe
        # f.seek(int("4f445",16)+rom_offset)   # Lilly
        # f.write(b"\xe0\x6b")

        # Inca Ruins Entrance
        self.__write_game_data__("9ca03", b"\xe0\x6b", f)  # Lilly
        self.__write_game_data__("9cea7", b"\xe0\x6b", f)  # Kara

        # Diamond Coast
        # f.seek(int("5aaa2",16)+rom_offset)   # Kara
        # f.write(b"\xe0\x6b")

        # Freejia Hotel
        self.__write_game_data__("5c782", b"\xe0\x6b", f)  # Lance
        self.__write_game_data__("5cb34", b"\xe0\x6b", f)  # Erik
        self.__write_game_data__("5c5b7", b"\xe0\x6b", f)  # Lilly ??
        self.__write_game_data__("5c45a", b"\xe0\x6b", f)  # Kara ??

        # Nazca Plain
        self.__write_game_data__("5e845", b"\xe0\x6b", f)
        self.__write_game_data__("5ec8f", b"\xe0\x6b", f)
        self.__write_game_data__("5eea5", b"\xe0\x6b", f)
        self.__write_game_data__("5efed", b"\xe0\x6b", f)
        self.__write_game_data__("5f1fd", b"\xe0\x6b", f)

        # Seaside Palace
        self.__write_game_data__("68689", b"\xe0\x6b", f)  # Lilly

        # Mu
        self.__write_game_data__("6a2cc", b"\xe0\x6b", f)  # Erik

        # Watermia
        self.__write_game_data__("7a871", b"\xe0\x6b", f)  # Lilly

        # Euro
        self.__write_game_data__("7d989", b"\xe0\x6b", f)  # Kara
        self.__write_game_data__("7daa1", b"\xe0\x6b", f)  # Erik
        self.__write_game_data__("7db29", b"\xe0\x6b", f)  # Neil

        # Natives' Village
        # f.seek(int("8805d",16)+rom_offset)   # Kara
        # f.write(b"\xe0\x6b")
        # f.seek(int("8865f",16)+rom_offset)   # Hamlet
        # f.write(b"\xe0\x6b")
        # f.seek(int("8854a",16)+rom_offset)   # Erik
        # f.write(b"\xe0\x6b")

        # Dao
        self.__write_game_data__("8a4af", b"\xe0\x6b", f)  # Kara
        self.__write_game_data__("8a56b", b"\xe0\x6b", f)  # Erik
        # f.seek(int("980cc",16)+rom_offset)   # Spirit
        # f.write(b"\xe0\x6b")

        # Pyramid
        self.__write_game_data__("8b7a1", b"\xe0\x6b", f)  # Kara
        self.__write_game_data__("8b822", b"\xe0\x6b", f)  # Jackal

        # Babel
        self.__write_game_data__("99e90", b"\xe0\x6b", f)  # Kara 1
        self.__write_game_data__("98519", b"\xe0\x6b", f)  # Kara 2

        ##########################################################################
        #                Prepare Room/Boss Rewards for Randomization
        ##########################################################################
        # Remove existing rewards
        self.__append_file_data__("01aade_roomrewards.bin", "1aade", f)

        # Make room-clearing HP rewards grant +3 HP each
        self.__write_game_data__("e041", b"\x03", f)

        # Make boss rewards also grant +3 HP per unclaimed reward
        self.__write_game_data__("c381", b"\x20\x90\xf4", f)
        self.__write_game_data__("f490", b"\xee\xca\x0a\xee\xca\x0a\xee\xca\x0a\x60", f)

        # Change boss room ranges
        self.__write_game_data__("c31a", b"\x67\x5A\x73\x00\x8A\x82\xA8\x00\xDD\xCC\xDD\x00\xEA\xB0\xBF\x00", f)
        # f.write(b"\xF6\xB0\xBF\x00")   # If Solid Arm ever grants Babel rewards

        # Add boss reward events to Babel and Jeweler Mansion
        self.__write_game_data__("ce536", b"\x00\x01\x01\xBB\xC2\x80\x00\xFF\xCA", f)  # Mummy Queen (Babel)
        # f.seek(int("ce3cb",16)+rom_offset)  # Solid Arm
        # f.write(b"\x00\x01\x01\xDF\xA5\x8B\x00\x00\x01\x01\xBB\xC2\x80\x00\xFF\xCA")

        # Black Glasses allow you to "see" which upgrades are available
        self.__append_file_data__("03fdb0_startmenu.bin", "3fdb0", f)
        self.__write_game_data__("381d6", b"\x4C\xB0\xFD", f)

        # Change start menu "FORCE" text
        self.__write_game_data__("1ff70", b"\x01\xC6\x01\x03\x14\x2D\x33\x48\x50\x00", f)  # "+3HP"
        self.__write_game_data__("1ff80", b"\x01\xC6\x01\x03\x14\x2D\x31\x53\x54\x52\x00", f)  # "+1STR"
        self.__write_game_data__("1ff90", b"\x01\xC6\x01\x03\x14\x2D\x31\x44\x45\x46\x00", f)  # "+1DEF"

        ##########################################################################
        #                        Balance Enemy Stats
        ##########################################################################
        # Determine enemy stats, by difficulty
        if self.settings.difficulty.value == Difficulty.EASY.value:
            self.__append_file_data__("01abf0_enemieseasy.bin", "1abf0", f)
        elif self.settings.difficulty.value == Difficulty.NORMAL.value:
            self.__append_file_data__("01abf0_enemiesnormal.bin", "1abf0", f)
        elif self.settings.difficulty.value == Difficulty.HARD.value:
            self.__append_file_data__("01abf0_enemieshard.bin", "1abf0", f)
        elif self.settings.difficulty.value == Difficulty.EXTREME.value:
            self.__append_file_data__("01abf0_enemiesextreme.bin", "1abf0", f)

        ##########################################################################
        #                            Randomize Inca tile
        ##########################################################################
        # Prepare file for uncompressed map data
        f_incamapblank = __get_data_file__("incamapblank.bin")
        f_incamap = tempfile.TemporaryFile()
        f_incamap.write(f_incamapblank.read())
        f_incamapblank.close()

        # Modify coordinates in event data
        inca_str = format(2 * self.inca_x + 4, "02x") + format(15 + 2 * self.inca_y, "02x")
        inca_str = inca_str + format(7 + 2 * self.inca_x, "02x") + format(18 + 2 * self.inca_y, "02x")

        self.__write_game_data__("9c683", binascii.unhexlify(inca_str), f)

        # Remove Wind Melody when door opens
        self.__write_game_data__("9c660", b"\x02\xcd\x12\x01\x02\xd5\x08\x02\xe0", f)
        self.__write_game_data__("9c676", b"\x67", f)
        self.__write_game_data__("9c6a3", b"\x02\xd0\x10\x01\x60\xc6", f)

        # Determine address location for new tile in uncompressed map data
        row = 32 + 2 * self.inca_y + 16 * int(self.inca_x / 6)
        column = 2 * ((self.inca_x + 2) % 8)
        addr = 16 * row + column

        # Write single tile at new location in uncompressed data
        f_incamap.seek(addr)
        f_incamap.write(b"\x40\x41\x00\x00\x00\x00\x00\x00\x00")
        f_incamap.write(b"\x00\x00\x00\x00\x00\x00\x00\x42\x43")
        f_incamap.seek(0)

        # Compress map data and write to file
        f_incamapcomp = tempfile.TemporaryFile()
        f_incamapcomp.write(qt_compress(f_incamap.read()))
        f_incamapcomp.seek(0)
        f_incamap.close()

        # Insert new compressed map data
        # f.seek(int("1f38db",16)+rom_offset)
        self.__write_game_data__("1f3ea0", b"\x02\x02" + f_incamapcomp.read(), f)
        f_incamapcomp.close()

        # Direct map arrangement pointer to new data - NO LONGER NECESSARY
        # f.seek(int("d8703",16)+rom_offset)
        # f.write(b"\xa0\x3e")

        ##########################################################################
        #                       Randomize heiroglyph order
        ##########################################################################
        # Determine random order
        hieroglyph_order = [1, 2, 3, 4, 5, 6]
        random.shuffle(hieroglyph_order)

        # Update Father's Journal with correct order
        order = b""
        for x in hieroglyph_order:
            if x == 1:
                order += b"\xc0\xc1"
            elif x == 2:
                order += b"\xc2\xc3"
            elif x == 3:
                order += b"\xc4\xc5"
            elif x == 4:
                order += b"\xc6\xc7"
            elif x == 5:
                order += b"\xc8\xc9"
            elif x == 6:
                order += b"\xca\xcb"

        self.__write_game_data__("39e9a", order, f)

        # Update sprite pointers for hieroglyph items, Item 1e is @10803c
        pointer = b""
        for x in hieroglyph_order:
            if x == 1:
                pointer += b"\xde\x81"
            if x == 2:
                pointer += b"\xe4\x81"
            if x == 3:
                pointer += b"\xea\x81"
            if x == 4:
                pointer += b"\xf0\x81"
            if x == 5:
                pointer += b"\xf6\x81"
            if x == 6:
                pointer += b"\xfc\x81"
        self.__write_game_data__("10803c", pointer, f)

        # Update which tiles are called when hieroglyph is placed
        i = 0
        for x in hieroglyph_order:
            addr = str(int("39b89", 16) + 5 * i + rom_offset)
            if x == 1:
                self.__write_game_data__(addr, b"\x84", f)
            elif x == 2:
                self.__write_game_data__(addr, b"\x85", f)
            elif x == 3:
                self.__write_game_data__(addr, b"\x86", f)
            elif x == 4:
                self.__write_game_data__(addr, b"\x8c", f)
            elif x == 5:
                self.__write_game_data__(addr, b"\x8d", f)
            elif x == 6:
                self.__write_game_data__(addr, b"\x8e", f)
            i += 1

        # Update which tiles are called from placement flags
        tile = b""
        for x in hieroglyph_order:
            if x == 1:
                tile += b"\x84"
            elif x == 2:
                tile += b"\x85"
            elif x == 3:
                tile += b"\x86"
            elif x == 4:
                tile += b"\x8c"
            elif x == 5:
                tile += b"\x8d"
            elif x == 6:
                tile += b"\x8e"
        self.__write_game_data__("8cb94", tile, f)

        ##########################################################################
        #                    Randomize Jeweler Reward amounts
        ##########################################################################
        # Randomize jeweler reward values
        gem = [random.randint(1, 3), random.randint(4, 6), random.randint(7, 9), random.randint(10, 14), random.randint(16, 24), random.randint(26, 34), random.randint(36, 50)]

        if self.settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            if self.settings.difficulty.value == Difficulty.EASY.value:
                gem[6] = GEMS_EASY
            elif self.settings.difficulty.value == Difficulty.NORMAL.value:
                gem[6] = GEMS_NORMAL
            else:
                gem[6] = GEMS_HARD

        gem_str = [format(int(gem[0] / 10), "x") + format(gem[0] % 10, "x"), format(int(gem[1] / 10), "x") + format(gem[1] % 10, "x"),
                   format(int(gem[2] / 10), "x") + format(gem[2] % 10, "x"), format(int(gem[3] / 10), "x") + format(gem[3] % 10, "x"),
                   format(int(gem[4] / 10), "x") + format(gem[4] % 10, "x"), format(int(gem[5] / 10), "x") + format(gem[5] % 10, "x"),
                   format(int(gem[6] / 10), "x") + format(gem[6] % 10, "x"), format(int(gem[0] / 10), "x") + format(gem[0] % 10, "x"),
                   format(int(gem[1] / 10), "x") + format(gem[1] % 10, "x"), format(int(gem[2] / 10), "x") + format(gem[2] % 10, "x"),
                   format(int(gem[3] / 10), "x") + format(gem[3] % 10, "x"), format(int(gem[4] / 10), "x") + format(gem[4] % 10, "x"),
                   format(int(gem[5] / 10), "x") + format(gem[5] % 10, "x"), format(int(gem[6] / 10), "x") + format(gem[6] % 10, "x")]

        # Write new values into reward check code (BCD format)
        self.__write_game_data__("8cee0", binascii.unhexlify(gem_str[0]), f)
        self.__write_game_data__("8cef1", binascii.unhexlify(gem_str[1]), f)
        self.__write_game_data__("8cf02", binascii.unhexlify(gem_str[2]), f)
        self.__write_game_data__("8cf13", binascii.unhexlify(gem_str[3]), f)
        self.__write_game_data__("8cf24", binascii.unhexlify(gem_str[4]), f)
        self.__write_game_data__("8cf35", binascii.unhexlify(gem_str[5]), f)
        self.__write_game_data__("8cf40", binascii.unhexlify(gem_str[6]), f)

        # Write new values into inventory table (Quintet text table format)
        # NOTE: Hard-coded for 1st, 2nd and 3rd rewards each < 10
        gem_str[0] = format(2, "x") + format(gem[0] % 10, "x")
        self.__write_game_data__("8d26f", binascii.unhexlify(gem_str[0]), f)

        gem_str[1] = format(2, "x") + format(gem[1] % 10, "x")
        self.__write_game_data__("8d283", binascii.unhexlify(gem_str[1]), f)

        gem_str[2] = format(2, "x") + format(gem[2] % 10, "x")
        self.__write_game_data__("8d297", binascii.unhexlify(gem_str[2]), f)

        gem_str[3] = format(2, "x") + format(int(gem[3] / 10), "x")
        gem_str[3] = gem_str[3] + format(2, "x") + format(gem[3] % 10, "x")
        self.__write_game_data__("8d2aa", binascii.unhexlify(gem_str[3]), f)

        gem_str[4] = format(2, "x") + format(int(gem[4] / 10), "x")
        gem_str[4] = gem_str[4] + format(2, "x") + format(gem[4] % 10, "x")
        self.__write_game_data__("8d2be", binascii.unhexlify(gem_str[4]), f)

        gem_str[5] = format(2, "x") + format(int(gem[5] / 10), "x")
        gem_str[5] = gem_str[5] + format(2, "x") + format(gem[5] % 10, "x")
        self.__write_game_data__("8d2d2", binascii.unhexlify(gem_str[5]), f)

        gem_str[6] = format(2, "x") + format(int(gem[6] / 10), "x")
        gem_str[6] = gem_str[6] + format(2, "x") + format(gem[6] % 10, "x")
        self.__write_game_data__("8d2e6", binascii.unhexlify(gem_str[6]), f)

        ##########################################################################
        #                    Randomize Mystic Statue requirement
        ##########################################################################
        statueOrder = [1, 2, 3, 4, 5, 6]
        random.shuffle(statueOrder)

        statues = []
        statues_hex = []

        i = 0
        while i < statues_required:
            if statueOrder[i] == 1:
                statues.append(1)
                statues_hex.append(b"\x21")

                # Check for Mystic Statue possession at end game state
                self.__write_game_data__("8dd19", b"\xf8", f)

            if statueOrder[i] == 2:
                statues.append(2)
                statues_hex.append(b"\x22")

                # Check for Mystic Statue possession at end game state
                self.__write_game_data__("8dd1f", b"\xf9", f)

            if statueOrder[i] == 3:
                statues.append(3)
                statues_hex.append(b"\x23")

                # Check for Mystic Statue possession at end game state
                self.__write_game_data__("8dd25", b"\xfa", f)
                # Restrict removal of Rama Statues from inventory
                self.__write_game_data__("1e12c", b"\x9f", f)

            if statueOrder[i] == 4:
                statues.append(4)
                statues_hex.append(b"\x24")

                # Check for Mystic Statue possession at end game state
                self.__write_game_data__("8dd2b", b"\xfb", f)

            if statueOrder[i] == 5:
                statues.append(5)
                statues_hex.append(b"\x25")

                # Check for Mystic Statue possession at end game state
                self.__write_game_data__("8dd31", b"\xfc", f)
                # Restrict removal of Hieroglyphs from inventory
                self.__write_game_data__("1e12d", b"\xf7\xff", f)

            if statueOrder[i] == 6:
                statues.append(6)
                statues_hex.append(b"\x26")

                # Check for Mystic Statue possession at end game state
                self.__write_game_data__("8dd37", b"\xfd", f)
            i += 1

        # Can't face Dark Gaia in Red Jewel hunts
        if self.settings.goal.value != Goal.DARK_GAIA.value:
            self.__write_game_data__("8dd0d", b"\x10\x01", f)

        statues.sort()
        statues_hex.sort()

        # Teacher at start spoils required Mystic Statues
        if len(statues_hex) == 0:
            statue_str = b"\xd3\x4d\x8e\xac\xd6\xd2\x80\xa2\x84\xac\xa2\x84\xa1\xa5\x88\xa2\x84\x83\x4f\xc0"
        else:
            statue_str = b"\xd3\x69\x8e\xa5\xac\x8d\x84\x84\x83\xac\x4c\xa9\xa3\xa4\x88\x82\xac\x63\xa4\x80\xa4\xa5\x84"
            if len(statues_hex) == 1:
                statue_str += b"\xac"
                statue_str += statues_hex[0]
                statue_str += b"\x4f\xc0"

            else:
                statue_str += b"\xa3\xcb"
                while statues_hex:
                    if len(statues_hex) > 1:
                        statue_str += statues_hex[0]
                        statue_str += b"\x2b\xac"

                    else:
                        statue_str += b"\x80\x8d\x83\xac"
                        statue_str += statues_hex[0]
                        statue_str += b"\x4f\xc0"

                    statues_hex.pop(0)

        self.__write_game_data__("48aab", statue_str, f)

        ##########################################################################
        #                   Randomize Location of Kara Portrait
        #       Sets spoiler in Lance's Letter and places portrait sprite
        ##########################################################################
        # Determine random location ID
        kara_location = random.randint(1, 5)
        # ANGEL_TILESET = b"\x03\x00\x10\x10\x36\x18\xca\x01"
        # ANGEL_PALETTE = b"\x04\x00\x60\xa0\x80\x01\xdf"
        # ANGEL_SPRTESET = b"\x10\x43\x0a\x00\x00\x00\xda"

        # Modify Kara Portrait event
        self.__write_game_data__("6d153", b"\x8a", f)
        self.__write_game_data__("6d169", b"\x02\xd2\x8a\x01\x02\xe0", f)
        self.__write_game_data__("6d25c", b"\x8a", f)
        self.__write_game_data__("6d27e", qt_encode("Hurry boy, she's waiting there for you!") + b"\xc0", f)
        self.__write_game_data__("6d305", qt_encode("Kara's portrait. If only you had Magic Dust...") + b"\xc0", f)

        if kara_location == KARA_ANGEL:
            self.__write_game_data__("39521", b"\x40\x8d\x86\x84\x8b\xac\x66\x88\x8b\x8b\x80\x86\x84", f)  # Set spoiler for Kara's location in Lance's Letter

        else:
            self.__write_game_data__("cb397", b"\x18", f)  # Remove Kara's painting from Ishtar's Studio

            if kara_location == KARA_EDWARDS:  # Underground tunnel exit, map 19 (0x13)
                # Set spoiler for Kara's location in Lance's Letter
                self.__write_game_data__("39521", b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x60\xa2\x88\xa3\x8e\x8d", f)
                # Set map check ID for Magic Dust item event
                self.__write_game_data__("393a9", b"\x13\x00\xD0\x08\x02\x45\x0b\x0b\x0d\x0d", f)
                # Set Kara painting event in appropriate map
                self.__write_game_data__("c8ac5", b"\x0b\x0b\x00\x4e\xd1\x86\xff\xca", f)
                # Adjust sprite palette
                self.__write_game_data__("6d15b", b"\x02\xb6\x30", f)

            elif kara_location == KARA_MINE:
                # Set spoiler for Kara's location in Lance's Letter
                self.__write_game_data__("39521", b"\x43\x88\x80\x8c\x8e\x8d\x83\xac\x4c\x88\x8d\x84", f)
                # Set map check ID for Magic Dust item event
                self.__write_game_data__("393a9", b"\x47\x00\xD0\x08\x02\x45\x0b\x24\x0d\x26", f)
                # Change "Sam" to "Samlet"
                self.__write_game_data__("5fee0", b"\x1a\x00\x10\x02\xc0\x9e\xd2\x02\x0b\x02\xc1\x6b", f)
                self.__write_game_data__("5d2bd", b"\xf0\xd2", f)
                self.__write_game_data__("5d2f0", b"\xd3\xc2\x05" + qt_encode("Samlet: I'll never forget you!") + b"\xc0", f)
                self.__write_game_data__("c9c78", b"\x03\x2a\x00\xe0\xfe\x85", f)
                # Disable Remus
                self.__write_game_data__("5d15e", b"\xe0", f)
                # Assign Kara painting spriteset to appropriate Map
                f.seek(0)
                rom = f.read()
                addr = rom.find(b"\x15\x0C\x00\x49\x00\x02", int("d8000", 16) + rom_offset)
                if addr < 0:
                    print("ERROR: Could not change spriteset for Diamond Mine")
                else:
                    self.__write_game_data__(str(addr), b"\x15\x25", f)

                # Set Kara painting event in appropriate map
                self.__write_game_data__("c9c6a", b"\x0b\x24\x00\x4e\xd1\x86", f)
                # Adjust sprite
                self.__write_game_data__("6d15b", b"\x02\xb6\x30", f)
                # f.seek(int("6d14e",16)+rom_offset)
                # f.write(b"\x2a")

            elif kara_location == KARA_KRESS:
                # Set spoiler for Kara's location in Lance's Letter
                self.__write_game_data__("39521", b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3", f)
                # Set map check ID for Magic Dust item event
                self.__write_game_data__("393a9", b"\xa9\x00\xD0\x08\x02\x45\x12\x06\x14\x08", f)
                # Set Kara painting event in appropriate map
                # Map #169, written into unused Map #104 (Seaside Tunnel)
                self.__write_game_data__("c8152", b"\x42\xad", f)
                self.__write_game_data__("cad42", b"\x05\x0a\x00\x8c\xc3\x82\x00\x00\x00\x00\xed\xea\x80\x00\xdf\xdf\x00\x4d\xe9\x80\x00\x12\x06\x00\x4e\xd1\x86\x00\xff\xca", f)
                # Adjust sprite
                self.__write_game_data__("6d15b", b"\x02\xb6\x30", f)

            elif kara_location == KARA_ANKORWAT:
                # Set spoiler for Kara's location in Lance's Letter
                self.__write_game_data__("39521", b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4", f)
                # Set map check ID for Magic Dust item event
                self.__write_game_data__("393a9", b"\xbf\x00\xD0\x08\x02\x45\x1a\x10\x1c\x12", f)
                # Set Kara painting event in appropriate map (Map #191)
                # Map #191, written into unused Map #104 (Seaside Tunnel)
                self.__write_game_data__("c817e", b"\x42\xad", f)
                self.__write_game_data__("5d15e", b"\x05\x0a\x02\x8c\xc3\x82\x00\x00\x00\x00\xed\xea\x80\x00\x0f\x0b\x00\xa3\x9a\x88\x00\x1a\x10\x00\x4e\xd1\x86\x00\xff\xca", f)
                # Adjust sprite
                self.__write_game_data__("6d15b", b"\x02\xb6\x30", f)

        ##########################################################################
        #                          Have fun with death text
        ##########################################################################
        death_list = [
            b"\x2d\x48\xa4\xac\xd6\xa3\xa3\x8e\xac\x87\x80\xa0\xa0\x84\x8d\xa3\xac\xd6\xd7\xcb\xd6\xfe\x85\xa2\x88\x84\x8d\x83\xac\xd7\x73\x88\xa3\xac\xd7\x89\xcb\x4c\x4e\x63\x64\x4b\x69\xac\x83\x84\x80\x83\x2a\x2e\xcb\xac\xac\x6d\x4c\x88\xa2\x80\x82\x8b\x84\xac\x4c\x80\xa8\xc0",
            b"\x2d\x69\x8e\xa5\xac\xd7\x9e\x80\xac\x83\x84\x82\x84\x8d\xa4\xac\x85\x84\x8b\x8b\x8e\xa7\x2a\xcb\x48\xac\x87\x80\xa4\x84\xac\xa4\x8e\xac\x8a\x88\x8b\x8b\xac\xa9\x8e\xa5\x2a\x2e\xcb\xac\xac\x6d\x48\x8d\x88\x86\x8e\xac\x4c\x8e\x8d\xa4\x8e\xa9\x80\xc0",
            b"\x2d\x64\x8e\xac\x83\x88\x84\xac\xd6\xef\x81\x84\xac\x80\xac\xd6\x95\xcb\x80\x83\xa6\x84\x8d\xa4\xa5\xa2\x84\x2a\x2e\xcb\xac\xac\x6d\x60\x84\xa4\x84\xa2\xac\x41\x80\x8d\x8d\x88\x8d\x86\xc0",
            b"\x2d\x4b\x88\x8a\x84\xac\xd6\x94\xa3\x8b\x84\x84\xa0\xac\x82\x8e\x8c\x84\xa3\xcb\x80\x85\xa4\x84\xa2\xac\x87\x80\xa2\x83\xac\xa7\x8e\xa2\x8a\xab\xac\xd6\x94\xa2\x84\xa3\xa4\xcb\x82\x8e\x8c\x84\xa3\xac\x80\x85\xa4\x84\xa2\xac\x80\x8d\xac\x87\x8e\x8d\x84\xa3\xa4\xcb\x8b\x88\x85\x84\x2a\x2e\xac\xac\xac\xac\x6d\x64\xa5\xa2\x81\x8e\xc0",
            b"\x2d\x45\x8e\x8b\x8b\x8e\xa7\xac\xd6\xfe\x83\xa2\x84\x80\x8c\xa3\x2a\x2a\x2a\xcb\x83\x84\x80\xa4\x87\xac\x88\xa3\xac\x8d\x8e\xa4\x87\x88\x8d\x86\xab\xac\xd6\xb0\x88\xa3\xcb\x84\xa6\x84\xa2\xa9\xa4\x87\x88\x8d\x86\x2a\x2e\xcb\xac\xac\x6d\x63\xa4\x84\x85\x80\x8d\xac\x4a\x80\xa2\x8b\xac\x63\xa4\x84\x85\x80\x8d\xa3\xa3\x8e\x8d\xc0",
            b"\x2d\x40\x8b\x8b\xac\x83\x84\x80\xa4\x87\xa3\xac\x80\xa2\x84\xac\xa3\xa5\x83\x83\x84\x8d\xab\xac\x8d\x8e\xcb\xd6\xb8\x87\x8e\xa7\xac\x86\xa2\x80\x83\xa5\x80\x8b\xac\xa4\x87\x84\xcb\x83\xa9\x88\x8d\x86\xac\x8c\x80\xa9\xac\x81\x84\x2a\x2e\xcb\xac\xac\x6d\x4c\x88\x82\x87\x80\x84\x8b\xac\x4c\x82\x43\x8e\xa7\x84\x8b\x8b\xc0",
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa0\x84\xa2\x87\x80\xa0\xa3\xac\x80\x8d\xcb\x8e\xa2\x83\x84\x80\x8b\xab\xac\x81\xa5\xa4\xac\x88\xa4\xac\x88\xa3\xac\x8d\x8e\xa4\xac\x80\x8d\xcb\x84\xa8\xa0\x88\x80\xa4\x88\x8e\x8d\x2a\x2e\xcb\xac\xac\x6d\x40\x8b\x84\xa8\x80\x8d\x83\xa2\x84\xac\x43\xa5\x8c\x80\xa3\xc0",
            b"\x2d\xd6\x62\xd7\x95\x8c\x80\xa4\xa4\x84\xa2\x84\x83\xac\x88\x8d\xcb\x8b\x88\x85\x84\xab\xac\xd6\xf7\x86\x80\xa6\x84\xac\x88\xa4\xcb\xa7\x84\x88\x86\x87\xa4\xab\xac\xa7\x80\xa3\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x49\x84\x85\x85\xa2\x84\xa9\xac\x44\xa5\x86\x84\x8d\x88\x83\x84\xa3\xc0",
            b"\x2d\x4d\x8e\xac\x8e\x8d\x84\xac\xd7\x6d\x8e\xa5\xa4\xac\x8e\x85\xac\xd6\xd6\xcb\xd6\xf5\x80\x8b\x88\xa6\x84\x2a\x2a\x2a\xac\x84\xa8\x82\x84\xa0\xa4\xcb\x80\xa3\xa4\xa2\x8e\x8d\x80\xa5\xa4\xa3\x2a\x2e\xcb\xac\xac\x6d\x63\xa4\x84\xa7\x80\xa2\xa4\xac\x63\xa4\x80\x85\x85\x8e\xa2\x83\xc0",
            b"\x2d\x44\xa4\xac\xa4\xa5\xac\x41\xa2\xa5\xa4\x84\x0d\x2e\xcb\xac\xac\x6d\x49\xa5\x8b\x88\xa5\xa3\xac\x42\x80\x84\xa3\x80\xa2\xc0",
            b"\x2d\x64\x8e\xac\xa4\x87\x84\xac\xa7\x88\xaa\x80\xa2\x83\xac\x83\x84\x80\xa4\x87\xac\x88\xa3\xcb\x8c\x84\xa2\x84\x8b\xa9\xac\x80\xac\x81\x84\x8b\x88\x84\x85\x2a\x2e\xcb\xac\xac\x6d\x43\x84\x84\xa0\x80\x8a\xac\x42\x87\x8e\xa0\xa2\x80\xc0",
            b"\x2d\x44\xa6\x84\xa2\xa9\xac\xd6\xdf\xa9\x8e\xa5\xac\x83\x88\x84\xab\xac\x88\xa4\xcb\x87\xa5\xa2\xa4\xa3\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\xa3\x87\xac\x47\x84\x8d\x83\x84\xa2\xa3\x8e\x8d\xc0",
            b"\x2d\x48\x85\xac\x48\xac\xd6\x98\xa4\x8e\xac\x83\x88\x84\xab\xac\x8b\x84\xa4\xac\x8c\x84\xcb\x83\x88\x84\xac\x85\x88\x86\x87\xa4\x88\x8d\x86\x2a\x2e\xcb\xac\xac\x6d\x46\x80\x81\xa2\x88\x84\x8b\xac\x46\x80\xa2\x82\x88\x80\xac\x4c\x80\xa2\xa1\xa5\x84\xaa\xc0",
            b"\x2d\x44\x80\x82\x87\xac\x83\x84\x80\xa4\x87\xac\x88\xa3\xac\x80\xa3\xac\xa5\x8d\x88\xa1\xa5\x84\xcb\x80\xa3\xac\x84\x80\x82\x87\xac\x8b\x88\x85\x84\x2a\x2e\xcb\xac\xac\x6d\x4d\x88\x82\x87\x8e\x8b\x80\xa3\xac\x67\x8e\x8b\xa4\x84\xa2\xa3\xa4\x8e\xa2\x85\x85\xc0",
            b"\x2d\x48\x8d\xac\xd6\xb0\xa9\x8e\xa5\xac\xd6\x78\xd6\xb5\xcb\x85\x8e\xa2\xa7\x80\xa2\x83\xac\xd6\xab\x81\x80\x82\x8a\x2a\x2e\xcb\xac\xac\x6d\x4c\x80\xa2\x8a\xac\x4c\x80\xa2\xa3\x8b\x80\x8d\x83\xc0",
            b"\x2d\x48\xac\x82\x80\x8d\xac\xd6\x91\xa4\x87\x84\xac\x83\x80\x88\xa3\x88\x84\xa3\xcb\x86\xa2\x8e\xa7\x88\x8d\x86\xac\xd6\xbe\x8c\x84\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x4a\x84\x80\xa4\xa3\xc0",
            b"\x2d\x40\xac\xa0\x84\xa2\xa3\x8e\x8d\x0e\xa3\xac\x83\x84\xa3\xa4\x88\x8d\xa9\xac\x8e\x85\xa4\x84\x8d\xcb\x84\x8d\x83\xa3\xac\xd6\x74\x87\x88\xa3\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x4c\x88\x8b\x80\x8d\xac\x4a\xa5\x8d\x83\x84\xa2\x80\xc0",
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa4\x87\x84\xac\x83\x84\xa3\xa4\xa2\x8e\xa9\x84\xa2\xcb\x80\x8d\x83\xac\x86\x88\xa6\x84\xa2\xac\x8e\x85\xac\xa3\x84\x8d\xa3\x84\x2a\x2e\xcb\xac\xac\x6d\x40\x8d\x83\xa9\xac\x47\x80\xa2\x86\x8b\x84\xa3\x88\xa3\xc0",
            b"\x2d\x41\x84\xac\x82\x80\x8b\x8c\x2a\xac\x46\x8e\x83\xac\x80\xa7\x80\x88\xa4\xa3\xac\xa9\x8e\xa5\xcb\x80\xa4\xac\xa4\x87\x84\xac\x83\x8e\x8e\xa2\x2a\x2e\xcb\xac\xac\x6d\x46\x80\x81\xa2\x88\x84\x8b\xac\x46\x80\xa2\x82\x88\x80\xac\x4c\x80\xa2\xa1\xa5\x84\xaa\xc0",
            b"\x2d\x67\x84\xac\xd6\x91\xd7\x88\x80\x8b\x88\xa6\x84\xac\xd6\xf6\xcb\xa7\x84\xac\x80\xa2\x84\xac\x82\x8b\x8e\xa3\x84\xa3\xa4\xac\xa4\x8e\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x4d\x84\x8d\x88\x80\xac\x42\x80\x8c\xa0\x81\x84\x8b\x8b\xc0",
            b"\x43\x84\x80\xa4\x87\xac\xa4\xa7\x88\xa4\x82\x87\x84\xa3\xac\x8c\xa9\xac\x84\x80\xa2\x2f\xcb\x2d\x4b\x88\xa6\x84\xab\x2e\xac\x87\x84\xac\xa3\x80\xa9\xa3\x2a\x2a\x2a\xac\x2d\x48\x0e\x8c\xcb\x82\x8e\x8c\x88\x8d\x86\x2a\x2e\xcb\xac\xac\x6d\x66\x88\xa2\x86\x88\x8b\xc0",
            b"\x2d\x47\x84\x80\xa6\x84\x8d\xac\x88\xa3\xac\x80\xac\xd7\x90\xd6\xf4\xcb\x80\x8b\x8b\xac\xa4\x87\x84\xac\x83\x8e\x86\xa3\xac\xa9\x8e\xa5\x0e\xa6\x84\xac\xd7\x5d\xcb\x8b\x8e\xa6\x84\x83\xac\xd6\x79\xa4\x8e\xac\x86\xa2\x84\x84\xa4\xac\xa9\x8e\xa5\x2a\x2e\xcb\xac\xac\x6d\x4e\x8b\x88\xa6\x84\xa2\xac\x46\x80\xa3\xa0\x88\xa2\xa4\xaa\xc0",
            b"\x2d\x44\xa6\x84\xa2\xa9\xac\x8c\x80\x8d\xac\x83\x88\x84\xa3\x2a\xac\x4d\x8e\xa4\xcb\x84\xa6\x84\xa2\xa9\xac\x8c\x80\x8d\xac\xd7\x95\x8b\x88\xa6\x84\xa3\x2a\x2e\xcb\xac\xac\x6d\x67\x88\x8b\x8b\x88\x80\x8c\xac\x67\x80\x8b\x8b\x80\x82\x84\xc0",
            b"\x2d\x40\x8d\x83\xac\x48\xac\xa7\x88\x8b\x8b\xac\xa3\x87\x8e\xa7\xac\xa4\x87\x80\xa4\xcb\x8d\x8e\xa4\x87\x88\x8d\x86\xac\x82\x80\x8d\xac\x87\x80\xa0\xa0\x84\x8d\xac\x8c\x8e\xa2\x84\xcb\x81\x84\x80\xa5\xa4\x88\x85\xa5\x8b\xac\xa4\x87\x80\x8d\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x67\x80\x8b\xa4\xac\x67\x87\x88\xa4\x8c\x80\x8d\xc0",
            b"\x2d\x46\x84\xa4\xac\x81\xa5\xa3\xa9\xac\x8b\x88\xa6\x88\x8d\x0e\x2b\xac\x8e\xa2\xac\x86\x84\xa4\xcb\x81\xa5\xa3\xa9\xac\x83\xa9\x88\x8d\x0e\x2a\x2e\xcb\xac\xac\x6d\x40\x8d\x83\xa9\xac\x43\xa5\x85\xa2\x84\xa3\x8d\x84\xc0",
            b"\x2d\x69\x8e\xa5\x0e\xa2\x84\xac\x8a\x88\x8b\x8b\x88\x8d\x0e\xac\x8c\x84\x2b\xcb\x63\x8c\x80\x8b\x8b\xa3\x4f\x2e\xcb\xac\xac\x6d\x47\x80\x8c\x88\x8b\xa4\x8e\x8d\xac\x60\x8e\xa2\xa4\x84\xa2\xc0",
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x89\xa5\xa3\xa4\xac\x80\x8d\x8e\xa4\x87\x84\xa2\xcb\xa0\x80\xa4\x87\x2a\xac\x4E\x8d\x84\xac\xa4\x87\x80\xa4\xac\xa7\x84\xac\x80\x8b\x8b\xac\x8c\xa5\xa3\xa4\xcb\xa4\x80\x8a\x84\x2a\x2e\xcb\xac\xac\x6d\x46\x80\x8d\x83\x80\x8b\x85\xc0",
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x8d\x8e\xa4\x87\x88\x8d\x86\x2b\xac\x81\xa5\xa4\xac\xa4\x8e\xcb\x8b\x88\xa6\x84\xac\x83\x84\x85\x84\x80\xa4\x84\x83\xac\x80\x8d\x83\xac\x88\x8d\x86\x8b\x8e\xa2\x6d\xcb\x88\x8e\xa5\xa3\xac\x88\xa3\xac\xa4\x8e\xac\x83\x88\x84\xac\x83\x80\x88\x8b\xa9\x2a\x2e\xcb\xac\xac\x6d\x4D\x80\xa0\x8e\x8b\x84\x8e\x8d\xac\x41\x8e\x8d\x80\xa0\x80\xa2\xa4\x84\xc0",
            b"\x2d\x44\xa6\x84\xa2\xa9\xac\xa0\x80\xa2\xa4\x88\x8d\x86\xac\x86\x88\xa6\x84\xa3\xac\x80\xcb\x85\x8e\xa2\x84\xa4\x80\xa3\xa4\x84\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2b\xac\x84\xa6\x84\xa2\xa9\xcb\xa2\x84\xa5\x8d\x88\x8e\x8d\xac\x80\xac\x87\x88\x8d\xa4\xac\x8e\x85\xac\xa4\x87\x84\xac\xa2\x84\x6d\xcb\xa3\xa5\xa2\xa2\x84\x82\xa4\x88\x8e\x8d\x2a\x2e\xac\x6d\x63\x82\x87\x8e\xa0\x84\x8d\x87\x80\xa5\x84\xa2\xc0",
            b"\x2d\x45\x8e\xa2\xac\x8b\x88\x85\x84\xac\x80\x8d\x83\xac\x83\x84\x80\xa4\x87\xac\x80\xa2\x84\xcb\x8e\x8d\x84\x2b\xac\x84\xa6\x84\x8d\xac\x80\xa3\xac\xa4\x87\x84\xac\xa2\x88\xa6\x84\xa2\xac\x80\x8d\x83\xcb\xa4\x87\x84\xac\xa3\x84\x80\xac\x80\xa2\x84\xac\x8e\x8d\x84\x2a\x2e\xcb\xac\x6d\x4A\x87\x80\x8b\x88\x8b\xac\x46\x88\x81\xa2\x80\x8d\xc0",
            b"\x2d\x4B\x88\xa6\x84\xac\xa9\x8e\xa5\xa2\xac\x8b\x88\x85\x84\xac\xa4\x87\x80\xa4\xac\xa4\x87\x84\xcb\x85\x84\x80\xa2\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\xac\x82\x80\x8d\xac\x8d\x84\xa6\x84\xa2\xcb\x84\x8d\xa4\x84\xa2\xac\xa9\x8e\xa5\xa2\xac\x87\x84\x80\xa2\xa4\x2a\x2e\xcb\xac\xac\x6d\x64\x84\x82\xa5\x8c\xa3\x84\x87\xc0",
            b"\x2d\x40\x82\x87\x88\x84\xa6\x88\x8d\x86\xac\x8b\x88\x85\x84\xac\x88\xa3\xac\x8d\x8e\xa4\xac\xa4\x87\x84\xcb\x84\xa1\xa5\x88\xa6\x80\x8b\x84\x8d\xa4\xac\x8e\x85\xac\x80\xa6\x8e\x88\x83\x88\x8d\x86\xcb\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x40\xa9\x8d\xac\x62\x80\x8d\x83\xc0",
            b"\x2d\x48\x85\xac\xa7\x84\xac\x8c\xa5\xa3\xa4\xac\x83\x88\x84\x2b\xac\xa7\x84\xac\x83\x88\x84\xcb\x83\x84\x85\x84\x8d\x83\x88\x8d\x86\xac\x8e\xa5\xa2\xac\xa2\x88\x86\x87\xa4\xa3\x2a\x2e\xcb\xac\xac\x6d\x63\x88\xa4\xa4\x88\x8d\x86\xac\x41\xa5\x8b\x8b\xc0",
            b"\x2d\x64\x87\x84\xac\x82\x8b\x8e\xa3\x84\xa2\xac\xa7\x84\xac\x82\x8e\x8c\x84\xac\xa4\x8e\xac\xa4\x87\x84\xcb\x8d\x84\x86\x80\xa4\x88\xa6\x84\x2b\xac\xa4\x8e\xac\x83\x84\x80\xa4\x87\x2b\xac\xa4\x87\x84\xcb\x8c\x8e\xa2\x84\xac\xa7\x84\xac\x81\x8b\x8e\xa3\xa3\x8e\x8c\x2a\x2e\xcb\xac\xac\x6d\x4C\x8e\x8d\xa4\x86\x8e\x8c\x84\xa2\xa9\xac\x42\x8b\x88\x85\xa4\xc0",
            b"\x2d\x48\x85\xac\xa7\x84\xac\x83\x8e\x8d\x0e\xa4\xac\x8a\x8d\x8e\xa7\xac\x8b\x88\x85\x84\x2b\xcb\x87\x8e\xa7\xac\x82\x80\x8d\xac\xa7\x84\xac\x8a\x8d\x8e\xa7\xac\x83\x84\x80\xa4\x87\x0d\x2e\xcb\xac\xac\x6d\x42\x8e\x8d\x85\xa5\x82\x88\xa5\xa3\xc0",
            b"\x2d\x48\xac\x83\x8e\x8d\x0e\xa4\xac\x87\x80\xa6\x84\xac\x8d\x8e\xac\x85\x84\x80\xa2\xac\x8e\x85\xcb\x83\x84\x80\xa4\x87\x2a\xac\x4C\xa9\xac\x8e\x8d\x8b\xa9\xac\x85\x84\x80\xa2\xac\x88\xa3\xcb\x82\x8e\x8c\x88\x8d\x86\xac\x81\x80\x82\x8a\xac\xa2\x84\x88\x8d\x82\x80\xa2\x8d\x80\xa4\x84\x83\x2a\x2e\xcb\xac\xac\x6d\x64\xa5\xa0\x80\x82\xac\x63\x87\x80\x8a\xa5\xa2\xc0",
            b"\x2d\x4B\x88\x85\x84\xac\x88\xa4\xa3\x84\x8b\x85\xac\x88\xa3\xac\x81\xa5\xa4\xac\xa4\x87\x84\xcb\xa3\x87\x80\x83\x8e\xa7\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2b\xac\x80\x8d\x83\xac\xa3\x8e\xa5\x8b\xa3\xcb\x83\x84\xa0\x80\xa2\xa4\x84\x83\xac\x81\xa5\xa4\xac\xa4\x87\x84\xac\xa3\x87\x80\x83\x8e\xa7\xa3\xcb\x8e\x85\xac\xa4\x87\x84\xac\x8b\x88\xa6\x88\x8d\x86\x2a\x2e\xac\x6d\x64\x2a\xac\x41\xa2\x8e\xa7\x8d\x84\xc0",
            b"\x2d\x63\x8e\x8c\x84\x8e\x8d\x84\xac\x87\x80\xa3\xac\xa4\x8e\xac\x83\x88\x84\xac\x88\x8d\xcb\x8e\xa2\x83\x84\xa2\xac\xa4\x87\x80\xa4\xac\xa4\x87\x84\xac\xa2\x84\xa3\xa4\xac\x8e\x85\xac\xa5\xa3\xcb\xa3\x87\x8e\xa5\x8b\x83\xac\xa6\x80\x8b\xa5\x84\xac\x8b\x88\x85\x84\xac\x8c\x8e\xa2\x84\x2a\x2e\xcb\xac\xac\x6d\x66\x88\xa2\x86\x88\x8d\x88\x80\xac\x67\x8e\x8e\x8b\x85\xc0",
            b"\x2d\x4E\xa5\xa2\xac\x8b\x88\x85\x84\xac\x83\xa2\x84\x80\x8c\xa3\xac\xa4\x87\x84\xcb\x65\xa4\x8e\xa0\x88\x80\x2a\xac\x4E\xa5\xa2\xac\x83\x84\x80\xa4\x87\xac\x80\x82\x87\x88\x84\xa6\x84\xa3\xcb\xa4\x87\x84\xac\x48\x83\x84\x80\x8b\x2a\x2e\xcb\xac\xac\x6d\x66\x88\x82\xa4\x8e\xa2\xac\x47\xa5\x86\x8e\xc0",
            b"\x2d\x48\x85\xac\xa9\x8e\xa5\xac\x83\x88\x84\xac\x88\x8d\xac\x80\x8d\xcb\x84\x8b\x84\xa6\x80\xa4\x8e\xa2\x2b\xac\x81\x84\xac\xa3\xa5\xa2\x84\xac\xa4\x8e\xac\xa0\xa5\xa3\x87\xcb\xa4\x87\x84\xac\x65\xa0\xac\x81\xa5\xa4\xa4\x8e\x8d\x2a\x2e\xcb\xac\xac\x6d\x63\x80\x8c\xac\x4B\x84\xa6\x84\x8d\xa3\x8e\x8d\xc0",
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa6\x84\xa2\xa9\xac\x8e\x85\xa4\x84\x8d\xcb\xa2\x84\x85\x84\xa2\xa2\x84\x83\xac\xa4\x8e\xac\x80\xa3\xac\x80\xac\x86\x8e\x8e\x83\xcb\x82\x80\xa2\x84\x84\xa2\xac\x8c\x8e\xa6\x84\x2a\x2e\xcb\xac\xac\x6d\x41\xa5\x83\x83\xa9\xac\x47\x8e\x8b\x8b\xa9\xc0",
            b"\x2d\x42\x8e\xa5\xa2\x80\x86\x84\xac\x88\xa3\xac\x81\x84\x88\x8d\x86\xac\xa3\x82\x80\xa2\x84\x83\xcb\xa4\x8e\xac\x83\x84\x80\xa4\x87\x2a\x2a\x2a\xac\x80\x8d\x83\xac\xa3\x80\x83\x83\x8b\x88\x8d\x86\xcb\xa5\xa0\xac\x80\x8d\xa9\xa7\x80\xa9\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x67\x80\xa9\x8d\x84\xc0",
            b"\x2d\x48\x8d\x80\x82\xa4\x88\xa6\x88\xa4\xa9\xac\x88\xa3\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x41\x84\x8d\x88\xa4\x8e\xac\x4C\xa5\xa3\xa3\x8e\x8b\x88\x8d\x88\xc0",
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa4\x87\x84\xac\x86\x8e\x8b\x83\x84\x8d\xac\x8a\x84\xa9\xcb\xa4\x87\x80\xa4\xac\x8e\xa0\x84\x8d\xa3\xac\xa4\x87\x84\xac\xa0\x80\x8b\x80\x82\x84\xac\x8e\x85\xcb\x84\xa4\x84\xa2\x8d\x88\xa4\xa9\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x4C\x88\x8b\xa4\x8e\x8d\xc0",
            b"\x2d\x48\xac\x80\x8b\xa7\x80\xa9\xa3\xac\xa3\x80\xa9\x2b\xac\x82\x8e\x8c\xa0\x8b\x80\x82\x84\x8d\x82\xa9\xcb\x88\xa3\xac\xa4\x87\x84\xac\x8a\x88\xa3\xa3\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x63\x87\x80\xa2\x88\xac\x62\x84\x83\xa3\xa4\x8e\x8d\x84\xc0",
            b"\x2d\x48\x8d\xac\xa4\x87\x84\xac\x8b\x8e\x8d\x86\xac\xa2\xa5\x8d\xac\xa7\x84\xac\x80\xa2\x84\xcb\x80\x8b\x8b\xac\x83\x84\x80\x83\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x4C\x80\xa9\x8d\x80\xa2\x83\xac\x4A\x84\xa9\x8d\x84\xa3\xc0",
            b"\x2d\x48\x0e\x8c\xac\x8d\x8e\xa4\xac\x80\x85\xa2\x80\x88\x83\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2b\xcb\x81\xa5\xa4\xac\x48\x0e\x8c\xac\x88\x8d\xac\x8d\x8e\xac\x87\xa5\xa2\xa2\xa9\xac\xa4\x8e\xcb\x83\x88\x84\x2a\xac\x48\xac\x87\x80\xa6\x84\xac\xa3\x8e\xac\x8c\xa5\x82\x87\xac\x48\xac\xa7\x80\x8d\xa4\xcb\xa4\x8e\xac\x83\x8e\xac\x85\x88\xa2\xa3\xa4\x2a\x2e\xac\x6d\x63\x2a\xac\x47\x80\xa7\x8a\x88\x8d\x86\xc0",
            b"\x2d\x45\x8e\xa2\xac\xa4\x88\xa3\xac\x8d\x8e\xa4\xac\x88\x8d\xac\x8c\x84\xa2\x84\xac\x83\x84\x80\xa4\x87\xcb\xa4\x87\x80\xa4\xac\x8c\x84\x8d\xac\x83\x88\x84\xac\x8c\x8e\xa3\xa4\x2a\x2e\xcb\xac\xac\x6d\x44\x8b\x88\xaa\x80\x81\x84\xa4\x87\xac\x41\x80\xa2\xa2\x84\xa4\xa4\xcb\xac\xac\xac\xac\xac\x41\xa2\x8e\xa7\x8d\x88\x8d\x86\xc0",
            b"\x2d\x43\x8e\xac\x8d\x8e\xa4\xac\x85\x84\x80\xa2\xac\x83\x84\x80\xa4\x87\xac\xa3\x8e\xac\x8c\xa5\x82\x87\xcb\x81\xa5\xa4\xac\xa2\x80\xa4\x87\x84\xa2\xac\xa4\x87\x84\xac\x88\x8d\x80\x83\x84\xa1\xa5\x80\xa4\x84\xcb\x8b\x88\x85\x84\x2a\x2e\xcb\xac\xac\x6d\x41\x84\xa2\xa4\x8e\x8b\xa4\xac\x41\xa2\x84\x82\x87\xa4\xc0",
            b"\x2d\x4D\x8e\xa4\x87\x88\x8d\x86\xac\x88\x8d\xac\x8b\x88\x85\x84\xac\x88\xa3\xcb\xa0\xa2\x8e\x8c\x88\xa3\x84\x83\xac\x84\xa8\x82\x84\xa0\xa4\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x4A\x80\x8d\xa9\x84\xac\x67\x84\xa3\xa4\xc0",
            b"\x2d\x4C\xa9\xac\x85\x84\x80\xa2\xac\xa7\x80\xa3\xac\x8d\x8e\xa4\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\xcb\x88\xa4\xa3\x84\x8b\x85\x2b\xac\x81\xa5\xa4\xac\x80\xac\x83\x84\x80\xa4\x87\xac\xa7\x88\xa4\x87\x6d\xcb\x8e\xa5\xa4\xac\x8c\x84\x80\x8d\x88\x8d\x86\x2a\x2e\xcb\xac\xac\x6d\x47\xa5\x84\xa9\xac\x4D\x84\xa7\xa4\x8e\x8d\xc0",
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x89\xa5\xa3\xa4\xac\x8b\x88\x85\x84\x0e\xa3\xac\x8d\x84\xa8\xa4\xcb\x81\x88\x86\xac\x80\x83\xa6\x84\x8d\xa4\xa5\xa2\x84\x2a\x2e\xcb\xac\xac\x6d\x49\x2a\xac\x4A\x2a\xac\x62\x8e\xa7\x8b\x88\x8d\x86\xc0",
            b"\x2d\x41\x84\x82\x80\xa5\xa3\x84\xac\x8e\x85\xac\x88\x8d\x83\x88\x85\x85\x84\xa2\x84\x8d\x82\x84\x2b\xcb\x8e\x8d\x84\xac\x83\x88\x84\xa3\xac\x81\x84\x85\x8e\xa2\x84\xac\x8e\x8d\x84\xcb\x80\x82\xa4\xa5\x80\x8b\x8b\xa9\xac\x83\x88\x84\xa3\x2a\x2e\xcb\xac\xac\x6d\x44\x8b\x88\x84\xac\x67\x88\x84\xa3\x84\x8b\xc0",
            b"\x2d\x4C\xa5\xa3\xa4\xac\x8d\x8e\xa4\xac\x80\x8b\x8b\xac\xa4\x87\x88\x8d\x86\xa3\xac\x80\xa4\xcb\xa4\x87\x84\xac\x8b\x80\xa3\xa4\xac\x81\x84\xac\xa3\xa7\x80\x8b\x8b\x8e\xa7\x84\x83\xac\xa5\xa0\xcb\x88\x8d\xac\x83\x84\x80\xa4\x87\x0d\x2e\xcb\xac\xac\x6d\x60\x8b\x80\xa4\x8e\xc0",
            b"\x2d\x64\x87\x84\xa2\x84\xac\x88\xa3\xac\x8d\x8e\xac\x83\x84\x80\xa4\x87\x2b\xac\x8e\x8d\x8b\xa9\xcb\x80\xac\x82\x87\x80\x8d\x86\x84\xac\x8e\x85\xac\xa7\x8e\xa2\x8b\x83\xa3\x2a\x2e\xcb\xac\xac\x6d\x42\x87\x88\x84\x85\xac\x63\x84\x80\xa4\xa4\x8b\x84\xc0",
            b"\x2d\x48\xac\x87\x80\x83\xac\xa3\x84\x84\x8d\xac\x81\x88\xa2\xa4\x87\xac\x80\x8d\x83\xcb\x83\x84\x80\xa4\x87\xac\x81\xa5\xa4\xac\x87\x80\x83\xac\xa4\x87\x8e\xa5\x86\x87\xa4\xac\xa4\x87\x84\xa9\xcb\xa7\x84\xa2\x84\xac\x83\x88\x85\x85\x84\xa2\x84\x8d\xa4\x2a\x2e\xcb\xac\xac\x6d\x64\x2a\xac\x63\x2a\xac\x44\x8b\x88\x8e\xa4\xc0",
            b"\x2d\x42\xa5\xa2\x88\x8e\xa3\x88\xa4\xa9\xac\x88\xa3\xac\x8b\x88\x85\x84\x2a\xcb\x40\xa3\xa3\xa5\x8c\xa0\xa4\x88\x8e\x8d\xac\x88\xa3\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x4C\x80\xa2\x8a\xac\x60\x80\xa2\x8a\x84\xa2\xc0",
            b"\x2d\x48\xac\x85\x84\x84\x8b\xac\x8c\x8e\x8d\x8e\xa4\x8e\x8d\xa9\xac\x80\x8d\x83\xac\x83\x84\x80\xa4\x87\xcb\xa4\x8e\xac\x81\x84\xac\x80\x8b\x8c\x8e\xa3\xa4\xac\xa4\x87\x84\xac\xa3\x80\x8c\x84\x2a\x2e\xcb\xac\xac\x6d\x42\x87\x80\xa2\x8b\x8e\xa4\xa4\x84\xac\x41\xa2\x8e\x8d\xa4\x84\xc0",
            b"\x2d\x63\x8e\x8c\x84\xac\xa0\x84\x8e\xa0\x8b\x84\xac\x80\xa2\x84\xac\xa3\x8e\xac\x80\x85\xa2\x80\x88\x83\xcb\xa4\x8e\xac\x83\x88\x84\xac\xa4\x87\x80\xa4\xac\xa4\x87\x84\xa9\xac\x8d\x84\xa6\x84\xa2\xcb\x81\x84\x86\x88\x8d\xac\xa4\x8e\xac\x8b\x88\xa6\x84\x2a\x2e\xcb\xac\xac\x6d\x47\x84\x8d\xa2\xa9\xac\x66\x80\x8d\xac\x43\xa9\x8a\x84\xc0",
            b"\x2d\x64\x87\x84\xac\x81\x8e\x83\xa9\xac\x83\x88\x84\xa3\x2b\xac\x81\xa5\xa4\xac\xa4\x87\x84\xcb\xa3\xa0\x88\xa2\x88\xa4\xac\xa4\x87\x80\xa4\xac\xa4\xa2\x80\x8d\xa3\x82\x84\x8d\x83\xa3\xac\x88\xa4\xcb\x82\x80\x8d\x8d\x8e\xa4\xac\x81\x84\xac\xa4\x8e\xa5\x82\x87\x84\x83\xac\x81\xa9\xcb\x83\x84\x80\xa4\x87\x2a\x2e\xac\xac\x6d\x62\x80\x8c\x80\x8d\x80\xac\x4C\x80\x87\x80\xa2\xa3\x87\x88\xc0",
            b"\x2d\x67\x87\x84\xa4\x87\x84\xa2\xac\x85\x8e\xa2\xac\x8b\x88\x85\x84\xac\x8e\xa2\xcb\x83\x84\x80\xa4\x87\x2b\xac\x83\x8e\xac\xa9\x8e\xa5\xa2\xac\x8e\xa7\x8d\xac\xa7\x8e\xa2\x8a\xcb\xa7\x84\x8b\x8b\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x62\xa5\xa3\x8a\x88\x8d\xc0",
            b"\x2d\x64\x87\x84\xac\xa2\x84\xa0\x8e\xa2\xa4\xa3\xac\x8e\x85\xac\x8c\xa9\xac\x83\x84\x80\xa4\x87\xcb\x87\x80\xa6\x84\xac\x81\x84\x84\x8d\xac\x86\xa2\x84\x80\xa4\x8b\xa9\xcb\x84\xa8\x80\x86\x86\x84\xa2\x80\xa4\x84\x83\x2a\x2e\xcb\xac\xac\x6d\x4C\x80\xa2\x8a\xac\x64\xa7\x80\x88\x8d\xc0",
            b"\x2d\x64\x87\x84\xac\xa6\x80\x8b\x88\x80\x8d\xa4\xac\x8d\x84\xa6\x84\xa2\xac\xa4\x80\xa3\xa4\x84\xcb\x8e\x85\xac\x83\x84\x80\xa4\x87\xac\x81\xa5\xa4\xac\x8e\x8d\x82\x84\x2a\x2e\xcb\xac\xac\x6d\x67\x88\x8b\x8b\x88\x80\x8c\xac\x63\x87\x80\x8a\x84\xa3\xa0\x84\x80\xa2\x84\xc0",
            b"\x2d\x67\x84\xac\x8a\x8d\x8e\xa7\xac\xa4\x87\x84\xac\xa2\x8e\x80\x83\xac\xa4\x8e\xcb\x85\xa2\x84\x84\x83\x8e\x8c\xac\x87\x80\xa3\xac\x80\x8b\xa7\x80\xa9\xa3\xac\x81\x84\x84\x8d\xcb\xa3\xa4\x80\x8b\x8a\x84\x83\xac\x81\xa9\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\x6d\x40\x8d\x86\x84\x8b\x80\xac\x43\x80\xa6\x88\xa3\xc0",
            b"\x2d\x43\x84\xa3\xa0\x88\xa3\x84\xac\x8d\x8e\xa4\xac\x83\x84\x80\xa4\x87\x2b\xac\x81\xa5\xa4\xcb\xa7\x84\x8b\x82\x8e\x8c\x84\xac\x88\xa4\x2b\xac\x85\x8e\xa2\xac\x8d\x80\xa4\xa5\xa2\x84\xcb\xa7\x88\x8b\x8b\xa3\xac\x88\xa4\xac\x8b\x88\x8a\x84\xac\x80\x8b\x8b\xac\x84\x8b\xa3\x84\x2a\x2e\xcb\xac\xac\x6d\x4C\x80\xa2\x82\xa5\xa3\xac\x40\xa5\xa2\x84\x8b\x88\xa5\xa3\xc0",
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x8d\x8e\xa4\xac\xa4\x87\x84\xac\xa7\x8e\xa2\xa3\xa4\xcb\xa4\x87\x80\xa4\xac\x82\x80\x8d\xac\x87\x80\xa0\xa0\x84\x8d\xac\xa4\x8e\xac\x8c\x84\x8d\x2a\x2e\xcb\xac\xac\x6d\x60\x8b\x80\xa4\x8e\xc0",
            b"\x2d\x4B\x88\x85\x84\xac\x8b\x84\xa6\x84\x8b\xa3\xac\x80\x8b\x8b\xac\x8c\x84\x8d\x2a\xcb\x43\x84\x80\xa4\x87\xac\xa2\x84\xa6\x84\x80\x8b\xa3\xac\xa4\x87\x84\xcb\x84\x8c\x88\x8d\x84\x8d\xa4\x2a\x2e\xcb\xac\xac\x6d\x46\x84\x8e\xa2\x86\x84\xac\x41\x84\xa2\x8d\x80\xa2\x83\xac\x63\x87\x80\xa7\xc0",
            b"\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa4\x87\x84\xac\xa7\x88\xa3\x87\xac\x8e\x85\xcb\xa3\x8e\x8c\x84\x2b\xac\xa4\x87\x84\xac\xa2\x84\x8b\x88\x84\x85\xac\x8e\x85\xac\x8c\x80\x8d\xa9\x2b\xcb\x80\x8d\x83\xac\xa4\x87\x84\xac\x84\x8d\x83\xac\x8e\x85\xac\x80\x8b\x8b\x2a\x2e\xcb\xac\xac\x6d\x4B\xa5\x82\x88\xa5\xa3\xac\x40\x8d\x8d\x80\x84\xa5\xa3\xac\x63\x84\x8d\x84\x82\x80\xc0",
            b"\x2d\x43\x84\x80\xa4\x87\xac\xa7\x88\x8b\x8b\xac\x81\x84\xac\x80\xac\x86\xa2\x84\x80\xa4\xcb\xa2\x84\x8b\x88\x84\x85\x2a\xac\x4D\x8e\xac\x8c\x8e\xa2\x84\xcb\x88\x8d\xa4\x84\xa2\xa6\x88\x84\xa7\xa3\x2a\x2e\xcb\xac\xac\x6d\x4A\x80\xa4\x87\x80\xa2\x88\x8d\x84\xac\x47\x84\xa0\x81\xa5\xa2\x8d\xc0\xc0"]
        if self.settings.difficulty.value == Difficulty.EXTREME.value:
            death_list.append(b"\x2d\x46\x88\xa4\xac\x86\xa5\x83\xac\xa3\x82\xa2\xa5\x81\x2a\x2e\xcb\xac\xac\x6d\x41\x80\x86\xa5\xc0")

        # Will death text
        self.__write_game_data__("d7c3", death_list[random.randint(0, len(death_list) - 1)], f)
        # f.write(death_list[0])

        # Change Fredan and Shadow death pointers
        self.__write_game_data__("d7b2", b"\xc2\xd7", f)
        self.__write_game_data__("d7b8", b"\xc2\xd7", f)

        ##########################################################################
        #                          Have fun with final text
        ##########################################################################
        superhero_list = [qt_encode("I must go, my people need me!") + b"\xc3\x00\xc0", qt_encode("     Up, up, and away!") + b"\xc3\x00\xc0",
                          qt_encode("       Up and atom!") + b"\xc3\x00\xc0", qt_encode("  It's clobberin' time!") + b"\xc3\x00\xc0",
                          qt_encode("       For Asgard!") + b"\xc3\x00\xc0", qt_encode("    Back in a flash!") + b"\xc3\x00\xc0", qt_encode("      I am GROOT!") + b"\xc3\x00\xc0",
                          qt_encode("Wonder Twin powers activate!") + b"\xc3\x00\xc0", qt_encode("    Titans together!") + b"\xc3\x00\xc0",
                          qt_encode("       HULK SMASH!") + b"\xc3\x00\xc0", qt_encode("        Flame on!") + b"\xc3\x00\xc0", qt_encode("    I have the power!") + b"\xc3\x00\xc0",
                          qt_encode("        Shazam!") + b"\xc3\x00\xc0", qt_encode("     Bite me, fanboy.") + b"\xc3\x00\xc0",
                          qt_encode("  Hi-yo Silver... away!") + b"\xc3\x00\xc0", qt_encode("Here I come to save the day!") + b"\xc3\x00\xc0",
                          qt_encode("    Teen Titans, Go!") + b"\xc3\x00\xc0", qt_encode("       Cowabunga!") + b"\xc3\x00\xc0", qt_encode("       SPOOOOON!!") + b"\xc3\x00\xc0",
                          qt_encode("There better be bacon when I get there...") + b"\xc3\x00\xc0"]

        # Assign final text box
        self.__write_game_data__("98ebe", superhero_list[random.randint(0, len(superhero_list) - 1)], f)

        ##########################################################################
        #                   Randomize item and ability placement
        ##########################################################################
        done = False
        seed_adj = 0
        w = World(self.settings, statues, kara_location, gem, [self.inca_x + 1, self.inca_y + 1], hieroglyph_order)
        while not done:
            if seed_adj > 10:
                print("ERROR: Max number of seed adjustments exceeded")
                return False
            done = w.randomize(seed_adj)
            seed_adj += 1

        # w.print_spoiler()
        w.generate_spoiler(self.output_folder, VERSION, filename)
        w.write_to_rom(f, rom_offset)

        ##########################################################################
        #                        Randomize Ishtar puzzle
        ##########################################################################
        # Add checks for Will's hair in each room
        self.__write_game_data__("6dc53", b"\x4c\x00\xdd\x86", f)
        self.__write_game_data__("6dd00",
                                 b"\x02\x45\x10\x00\x20\x10\x66\xdc\x02\x45\x30\x00\x40\x10\x66\xDC\x02\x45\x50\x00\x60\x10\x66\xdc\x02\x45\x70\x00\x80\x10\x66\xDC\x4c\x66\xdc\x86",
                                 f)

        # Generalize success text boxes
        # Make Rooms 1 and 3 equal to Room 2 text (which is already general)
        self.__write_game_data__("6d978", b"\x2c\xdb", f)  # Room 1
        self.__write_game_data__("6d9ce", b"\x2c\xdb", f)  # Room 3
        # Generalize Room 4 text
        self.__write_game_data__("6d9f8", b"\xc6\xdb", f)
        self.__write_game_data__("6dbc6", b"\xc2\x0a", f)
        # Create temporary map file

        f_ishtarmap = tempfile.TemporaryFile()
        self.__append_file_data__("ishtarmapblank.bin", "0", f_ishtarmap)

        room_offsets = ["6d95e", "6d98a", "6d9b4", "6d9de"]  # ROM addrs for cursor capture, by room
        coord_offsets = [3, 8, 15, 20]  # Offsets for xmin, xmax, ymin, ymax
        changes = [random.randint(1, 8), random.randint(1, 7), random.randint(1, 5), random.randint(1, 7)]

        # Set change for Room 1
        if changes[0] == 1:  # Change right vase to light (vanilla)
            self.__write_game_data__("17b", b"\x7b", f_ishtarmap)
            self.__write_game_data__("18b", b"\x84", f_ishtarmap)
            coords = [b"\xB0\x01", b"\xC0\x01", b"\x70\x00", b"\x90\x00"]

        elif changes[0] == 2:  # Change middle vase to light
            self.__write_game_data__("175", b"\x7b", f_ishtarmap)
            self.__write_game_data__("185", b"\x84", f_ishtarmap)
            coords = [b"\x50\x01", b"\x60\x01", b"\x70\x00", b"\x90\x00"]

        elif changes[0] == 3:  # Change left vase to dark
            self.__write_game_data__("174", b"\x83", f_ishtarmap)
            self.__write_game_data__("184", b"\x87", f_ishtarmap)
            coords = [b"\x40\x01", b"\x50\x01", b"\x70\x00", b"\x90\x00"]

        elif changes[0] == 4:  # Change left shelf to empty
            self.__write_game_data__("165", b"\x74", f_ishtarmap)
            coords = [b"\x50\x01", b"\x60\x01", b"\x58\x00", b"\x70\x00"]

        elif changes[0] == 5:  # Change left shelf to books
            self.__write_game_data__("165", b"\x76", f_ishtarmap)
            coords = [b"\x50\x01", b"\x60\x01", b"\x58\x00", b"\x70\x00"]

        elif changes[0] == 6:  # Change right shelf to jar
            self.__write_game_data__("166", b"\x75", f_ishtarmap)
            coords = [b"\x60\x01", b"\x70\x01", b"\x58\x00", b"\x70\x00"]

        elif changes[0] == 7:  # Change right shelf to empty
            self.__write_game_data__("166", b"\x74", f_ishtarmap)
            coords = [b"\x60\x01", b"\x70\x01", b"\x58\x00", b"\x70\x00"]

        elif changes[0] == 8:  # Will's hair
            self.__write_game_data__("6dd06", b"\x5d", f)
            coords = [b"\xa0\x01", b"\xc0\x01", b"\xb0\x00", b"\xd0\x00"]

        # Update cursor check ranges for Room 1
        for i in range(4):
            self.__write_game_data__(str(int(room_offsets[0], 16) + coord_offsets[i] + rom_offset), coords[i], f)

        # Set change for Room 2
        if changes[1] == 1:  # Change both pots to dark (vanilla)
            self.__write_game_data__("3a3", b"\x7c\x7c", f_ishtarmap)
            self.__write_game_data__("3b3", b"\x84\x84", f_ishtarmap)
            coords = [b"\x30\x03", b"\x50\x03", b"\xa0\x00", b"\xc0\x00"]

        elif changes[1] == 2:  # Remove rock
            self.__write_game_data__("3bd", b"\x73", f_ishtarmap)
            coords = [b"\xd0\x03", b"\xe0\x03", b"\xb0\x00", b"\xc0\x00"]

        elif changes[1] == 3:  # Add round table
            self.__write_game_data__("395", b"\x7d\x7e", f_ishtarmap)
            self.__write_game_data__("3a5", b"\x85\x86", f_ishtarmap)
            self.__write_game_data__("3b5", b"\x8d\x8e", f_ishtarmap)
            coords = [b"\x50\x03", b"\x70\x03", b"\x90\x00", b"\xb0\x00"]

        elif changes[1] == 4:  # Add sconce
            self.__write_game_data__("357", b"\x88\x89", f_ishtarmap)
            self.__write_game_data__("367", b"\x90\x91", f_ishtarmap)
            coords = [b"\x70\x03", b"\x90\x03", b"\x50\x00", b"\x70\x00"]

        elif changes[1] == 5:  # Add rock
            self.__write_game_data__("3b2", b"\x77", f_ishtarmap)
            coords = [b"\x20\x03", b"\x30\x03", b"\xb0\x00", b"\xc0\x00"]

        elif changes[1] == 6:  # Will's hair
            self.__write_game_data__("6dd0e", b"\x5d", f)
            coords = [b"\x90\x03", b"\xb0\x03", b"\xa0\x00", b"\xc0\x00"]

        elif changes[1] == 7:  # Put moss on rock
            self.__write_game_data__("3bd", b"\x8f", f_ishtarmap)
            coords = [b"\xd0\x03", b"\xe0\x03", b"\xb0\x00", b"\xc0\x00"]

        # Update cursor check ranges for Room 2
        for i in range(4):
            self.__write_game_data__(str(int(room_offsets[1], 16) + coord_offsets[i] + rom_offset), coords[i], f)

        # Set change for Room 3
        # Check for chest contents, only change map if contents are the same
        if constants.ITEM_LOCATIONS[80][3] == constants.ITEM_LOCATIONS[81][3]:
            if changes[2] == 1:  # Remove rock
                self.__write_game_data__("5bd", b"\x73", f_ishtarmap)
                coords = [b"\xd0\x05", b"\xe0\x05", b"\xb0\x00", b"\xc0\x00"]

            elif changes[2] == 2:  # Add rock
                self.__write_game_data__("5b2", b"\x77", f_ishtarmap)
                coords = [b"\x20\x05", b"\x30\x05", b"\xb0\x00", b"\xc0\x00"]

            elif changes[2] == 3:  # Add sconce
                self.__write_game_data__("557", b"\x88\x89", f_ishtarmap)
                self.__write_game_data__("567", b"\x90\x91", f_ishtarmap)
                coords = [b"\x70\x05", b"\x90\x05", b"\x50\x00", b"\x70\x00"]

            elif changes[2] == 4:  # Will's hair
                self.__write_game_data__("6dd16", b"\x5d", f)
                coords = [b"\x90\x05", b"\xb0\x05", b"\xa0\x00", b"\xc0\x00"]

            if changes[2] == 5:  # Moss rock
                self.__write_game_data__("5bd", b"\x8f", f_ishtarmap)
                coords = [b"\xd0\x05", b"\xe0\x05", b"\xb0\x00", b"\xc0\x00"]

            # Update cursor check ranges for Room 3 (only if chest contents different)
            for i in range(4):
                self.__write_game_data__(str(int(room_offsets[2], 16) + coord_offsets[i] + rom_offset), coords[i], f)

        # Set change for Room 4
        if changes[3] == 1:  # Will's hair (vanilla)
            self.__write_game_data__("6dd1e", b"\x5d", f)

        else:
            if changes[3] == 2:  # Remove rock
                self.__write_game_data__("7bd", b"\x73", f_ishtarmap)
                coords = [b"\xd0\x07", b"\xe0\x07", b"\xb0\x00", b"\xc0\x00"]

            elif changes[3] == 3:  # Add rock
                self.__write_game_data__("7b2", b"\x77", f_ishtarmap)
                coords = [b"\x20\x07", b"\x30\x07", b"\xb0\x00", b"\xc0\x00"]

            elif changes[3] == 4:  # Add vase L
                self.__write_game_data__("7a3", b"\x7c", f_ishtarmap)
                self.__write_game_data__("7b3", b"\x84", f_ishtarmap)
                coords = [b"\x30\x07", b"\x40\x07", b"\xa0\x00", b"\xc0\x00"]

            elif changes[3] == 5:  # Add vase R
                self.__write_game_data__("7ac", b"\x7c", f_ishtarmap)
                self.__write_game_data__("7bc", b"\x84", f_ishtarmap)
                coords = [b"\xc0\x07", b"\xd0\x07", b"\xa0\x00", b"\xc0\x00"]

            elif changes[3] == 6:  # Crease in floor
                self.__write_game_data__("7b4", b"\x69\x6a", f_ishtarmap)
                coords = [b"\x40\x07", b"\x60\x07", b"\xb0\x00", b"\xc8\x00"]

            if changes[3] == 7:  # Moss rock
                self.__write_game_data__("7bd", b"\x8f", f_ishtarmap)
                coords = [b"\xd0\x07", b"\xe0\x07", b"\xb0\x00", b"\xc0\x00"]

            # Update cursor check ranges for Room 3 (only if not hair)
            for i in range(4):
                self.__write_game_data__(str(int(room_offsets[3], 16) + coord_offsets[i] + rom_offset), coords[i], f)

        # Compress map data and write to file
        f_ishtarmapcomp = tempfile.TemporaryFile()
        f_ishtarmap.seek(0)
        f_ishtarmapcomp.write(qt_compress(f_ishtarmap.read()))
        f_ishtarmapcomp.seek(0)
        f_ishtarmap.close()
        ishtar_data = f_ishtarmapcomp.read()
        f_ishtarmapcomp.close()

        # Insert new compressed map data
        # f.seek(int("193d25",16)+rom_offset)
        self.__write_game_data__("1f4100", b"\x08\x02" + ishtar_data, f)

        # Direct map arrangement pointer to new data - NO LONGER NECESSARY
        # f.seek(int("d977e",16)+rom_offset)
        # f.write(b"\x00\x41")

        ##########################################################################
        #                        Export file and return
        ##########################################################################
        output_path = self.output_folder + filename
        randomized_file = self.__write_randomized_rom__(output_path, f)

        return True

    def __get_required_statues__(self) -> int:
        if self.settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            return 0

        if self.settings.statues.lower() == "random":
            return random.randrange(0, 6)

        return int(self.settings.statues)

    def __append_file_data__(self, data_filename: str, address: str, f: BinaryIO) -> None:
        data_file = __get_data_file__(data_filename)
        data = data_file.read()
        data_file.close()

        f.seek(int(address, 16) + self.offset)
        f.write(data)

    def __write_game_data__(self, address: str, value: bytes, f: BinaryIO) -> None:
        addr = int(address, 16)
        self.logger.debug("Writing " + str(addr.bit_length()) + " bytes.")
        self.total_bytes += addr.bit_length()

        f.seek(addr + self.offset)
        f.write(value)

    def __seek__(self, address: str, f: BinaryIO) -> None:
        f.seek(int(address, 16) + self.offset)

    def __copy_original_rom__(self):
        try:
            f_rom = open(self.rom_path, "rb")
        except:
            raise FileNotFoundError

        f = tempfile.TemporaryFile()
        f_rom.seek(0)
        f.write(f_rom.read())
        f_rom.seek(0)

        rom_data = f_rom.read()
        self.offset = get_offset(rom_data)

        f_rom.close()
        return f

    def __write_randomized_rom__(self, output_path: str, f: BinaryIO) -> BinaryIO:
        output = open(output_path, "wb")
        f.seek(0)
        output.write(f.read())
        f.close()
        output.close()

        self.logger.debug("Total Bytes: " + str(self.total_bytes) + " bytes.")
        return output

    def __build_hash__(self, filename: str):
        hash_str = filename
        h = hmac.new(bytes(self.settings.seed), hash_str.encode())
        digest = h.digest()

        hash_dict = [b"\x20", b"\x21", b"\x28", b"\x29", b"\x2a", b"\x2b", b"\x2c", b"\x2d", b"\x2e", b"\x2f", b"\x30", b"\x31", b"\x32", b"\x33"]
        hash_dict += [b"\x34", b"\x35", b"\x36", b"\x37", b"\x38", b"\x39", b"\x3a", b"\x3b", b"\x3c", b"\x3d", b"\x3e", b"\x3f", b"\x42", b"\x43"]
        hash_dict += [b"\x44", b"\x46", b"\x47", b"\x48", b"\x4a", b"\x4b", b"\x4c", b"\x4d", b"\x4e", b"\x50", b"\x51", b"\x52", b"\x53", b"\x54"]
        hash_dict += [b"\x56", b"\x57", b"\x58", b"\x59", b"\x5a", b"\x5b", b"\x5c", b"\x5d", b"\x5e", b"\x5f", b"\x7c", b"\x80", b"\x81"]

        hash_len = len(hash_dict)

        i = 0
        hash_final = b""
        while i < 6:
            key = digest[i] % hash_len
            hash_final += hash_dict[key]
            i += 1

        return hash_final