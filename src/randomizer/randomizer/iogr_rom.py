import binascii, hashlib, logging, os, random, tempfile, json, copy
from typing import BinaryIO

from .patch import Patch
from .classes import World
from .quintet_comp import compress as qt_compress
from .quintet_text import encode as qt_encode
from .errors import FileNotFoundError, OffsetError
from .models.randomizer_data import RandomizerData
from .models.enums.difficulty import Difficulty
from .models.enums.goal import Goal
from .models.enums.logic import Logic
from .models.enums.enemizer import Enemizer
from .models.enums.start_location import StartLocation

VERSION = "2.5.0"

KARA_EDWARDS = 1
KARA_MINE = 2
KARA_ANGEL = 3
KARA_KRESS = 4
KARA_ANKORWAT = 5

GEMS_EASY = 35
GEMS_NORMAL = 40
GEMS_HARD = 45
GEMS_EXTREME = 50

INV_FULL = b"\x5c\x8e\xc9\x80"
FORCE_CHANGE = b"\x22\x30\xfd\x88"

OUTPUT_FOLDER: str = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + ".." + os.path.sep + ".." + os.path.sep + "data" + os.path.sep + "output" + os.path.sep
BIN_PATH: str = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "bin" + os.path.sep


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

    def getGoal(goal, statues):
        if goal.value is Goal.DARK_GAIA.value:
            return "_DG" + statues[0]
        if goal.value is Goal.RED_JEWEL_HUNT.value:
            return "_RJ"

    def getLogic(logic):
        if logic.value == Logic.COMPLETABLE.value:
            return ""
        if logic.value == Logic.BEATABLE.value:
            return "_L(b)"
        if logic.value == Logic.CHAOS.value:
            return "_L(x)"

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
    filename += getGoal(settings.goal, settings.statues)
    filename += getLogic(settings.logic)
    filename += getStartingLocation(settings.start_location)
    filename += getEnemizer(settings.enemizer)
    filename += getSwitch(settings.boss_shuffle, "b")
    filename += getSwitch(settings.firebird, "f")
    filename += getSwitch(settings.ohko, "ohko")
    filename += getSwitch(settings.allow_glitches, "g")
    filename += getSwitch(settings.red_jewel_madness, "rjm")
    filename += "_" + str(settings.seed)
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
        patch = self.__generate_patch__()
        rom_offset = self.__get_offset__(patch)

        random.seed(settings.seed)
        statues_required = self.__get_required_statues__(settings)
        mode = settings.difficulty.value

        ##########################################################################
        #                             Early Firebird
        ##########################################################################
        # Write new Firebird logic into unused memory location
        f_firebird = open(BIN_PATH + "02f0c0_firebird.bin", "rb")
        patch.seek(int("2f0c0", 16) + rom_offset)
        patch.write(f_firebird.read())
        f_firebird.close()

        if settings.firebird == 1:
            # Change firebird logic
            # Requires Shadow's form, Crystal Ring (switch #$3e) and Kara rescued (switch #$8a)
            patch.seek(int("2cd07", 16) + rom_offset)
            patch.write(b"\x4c\xc0\xf0\xea\xea\xea")
            patch.seek(int("2cd88", 16) + rom_offset)
            patch.write(b"\x4c\xf0\xf0\xea\xea\xea")
            patch.seek(int("2ce06", 16) + rom_offset)
            patch.write(b"\x4c\x20\xf1\xea\xea\xea")
            patch.seek(int("2ce84", 16) + rom_offset)
            patch.write(b"\x4c\x50\xf1\xea\xea\xea")

            # Load firebird assets into every map
            patch.seek(int("3e03a", 16) + rom_offset)
            patch.write(b"\x80\x00")
            patch.seek(int("eaf0", 16) + rom_offset)
            patch.write(b"\x20\xa0\xf4\xea\xea")
            patch.seek(int("f4a0", 16) + rom_offset)
            patch.write(b"\x02\x3b\x71\xb2\xf4\x80\xa9\x00\x10\x04\x12\x60")
            patch.seek(int("f4b0", 16) + rom_offset)
            patch.write(b"\x02\xc1\xad\xd4\x0a\xc9\x02\x00\xf0\x01\x6b\x02\x36\x02\x39\x80\xef")

        ##########################################################################
        #                            Modify ROM Header
        ##########################################################################
        # New game title
        patch.seek(int("ffd1", 16) + rom_offset)
        patch.write(b"\x52\x41\x4E\x44\x4F")

        # Put randomizer hash code on start screen
        patch.seek(int("1da4c", 16) + rom_offset)
        patch.write(b"\x52\x41\x4E\x44\x4F\x90\x43\x4F\x44\x45\x90")

        hash_str = filename
        h = hashlib.sha256()
        h.update(hash_str.encode())
        hash = h.digest()

        hash_dict = [b"\x20", b"\x21", b"\x28", b"\x29", b"\x2a", b"\x2b", b"\x2c", b"\x2d", b"\x2e", b"\x2f", b"\x30", b"\x31", b"\x32", b"\x33"]
        hash_dict += [b"\x34", b"\x35", b"\x36", b"\x37", b"\x38", b"\x39", b"\x3a", b"\x3b", b"\x3c", b"\x3d", b"\x3e", b"\x3f", b"\x42", b"\x43"]
        hash_dict += [b"\x44", b"\x46", b"\x47", b"\x48", b"\x4a", b"\x4b", b"\x4c", b"\x4d", b"\x4e", b"\x50", b"\x51", b"\x52", b"\x53", b"\x54"]
        hash_dict += [b"\x56", b"\x57", b"\x58", b"\x59", b"\x5a", b"\x5b", b"\x5c", b"\x5d", b"\x5e", b"\x5f", b"\x7c", b"\x80", b"\x81"]

        hash_len = len(hash_dict)

        i = 0
        hash_final = b""
        while i < 6:
            key = hash[i] % hash_len
            hash_final += hash_dict[key]
            i += 1

        # print binascii.hexlify(hash_final)
        patch.seek(int("1da57", 16) + rom_offset)
        patch.write(hash_final)

        ##########################################################################
        #                           Negate useless switches
        #                 Frees up switches for the randomizer's use
        ##########################################################################
        patch.seek(int("48a03", 16) + rom_offset)  # Switch 17 - Enter Seth's house
        patch.write(b"\x10")
        patch.seek(int("4bca9", 16) + rom_offset)  # Switch 18 - Enter Will's house (1/2)
        patch.write(b"\x10")
        patch.seek(int("4bccc", 16) + rom_offset)  # Switch 18 - Enter Will's house (2/2)
        patch.write(b"\x10")
        patch.seek(int("4bcda", 16) + rom_offset)  # Switch 19 - Enter Lance's house
        patch.write(b"\x10")
        patch.seek(int("4bce8", 16) + rom_offset)  # Switch 20 - Enter Erik's house
        patch.write(b"\x10")
        patch.seek(int("4be3d", 16) + rom_offset)  # Switch 21 - Enter seaside cave
        patch.write(b"\x10")
        patch.seek(int("4bcf6", 16) + rom_offset)  # Switch 23 - Complete seaside cave events
        patch.write(b"\x10")
        patch.seek(int("9bf95", 16) + rom_offset)  # Switch 58 - First convo with Lilly
        patch.write(b"\x10")
        patch.seek(int("4928a", 16) + rom_offset)  # Switch 62 - First convo with Lola (1/2)
        patch.write(b"\x10")
        patch.seek(int("49873", 16) + rom_offset)  # Switch 62 - First convo with Lola (1/2)
        patch.write(b"\x10")
        patch.seek(int("4e933", 16) + rom_offset)  # Switch 65 - Hear Elder's voice
        patch.write(b"\x10")
        patch.seek(int("58a29", 16) + rom_offset)  # Switch 78 - Talk to Gold Ship queen
        patch.write(b"\x10")
        patch.seek(int("4b067", 16) + rom_offset)
        patch.write(b"\x10\x00")
        patch.seek(int("4b465", 16) + rom_offset)
        patch.write(b"\x10\x00")
        patch.seek(int("4b8b6", 16) + rom_offset)
        patch.write(b"\x10\x00")
        patch.seek(int("686fa", 16) + rom_offset)  # Switch 111 - meet Lilly at Seaside Palace
        patch.write(b"\x10")
        patch.seek(int("78d76", 16) + rom_offset)
        patch.write(b"\x10")
        patch.seek(int("78d91", 16) + rom_offset)
        patch.write(b"\x10")
        patch.seek(int("7d7b1", 16) + rom_offset)  # Switch 159 - Mt. Kress on map
        patch.write(b"\x10")

        ##########################################################################
        #                     Initialize map header dataset
        ##########################################################################
        f_mapdata_orig = open(BIN_PATH + "0d8000_mapdata.bin", "rb")
        f_mapdata = tempfile.TemporaryFile()
        f_mapdata.write(f_mapdata_orig.read())
        f_mapdata_orig.close

        # Insert tutorial map in Easy mode
        if mode == 0:
            f_mapdata.seek(0)
            addr = f_mapdata.read().find(b"\x00\x07\x00\x02\x01")
            f_mapdata.seek(addr)
            f_mapdata.write(b"\x00\x09")

            f_mapdata.seek(0)
            addr = f_mapdata.read().find(b"\x00\x09\x00\x02\x08")
            f_mapdata.seek(addr)
            f_mapdata.write(b"\x00\x07")

        ##########################################################################
        #                        Update treasure chest data
        ##########################################################################
        # Remove fanfares from treasure chests
        f_chests = open(BIN_PATH + "01afa6_chests.bin", "rb")
        patch.seek(int("1afa6", 16) + rom_offset)
        patch.write(f_chests.read())
        f_chests.close

        # Update item acquisition messages and add messages for new items (29-2f)
        f_acquisition = open(BIN_PATH + "01fd24_acquisition.bin", "rb")
        patch.seek(int("1fd24", 16) + rom_offset)
        patch.write(f_acquisition.read())
        f_acquisition.close

        ##########################################################################
        #                            Update item events
        #    Adds new items that increase HP, DEF, STR and improve abilities
        ##########################################################################
        # Add pointers for new items @38491
        patch.seek(int("38491", 16) + rom_offset)
        patch.write(b"\x6f\x9f\x91\x9f\x1d\x88\x3a\x88\x5f\x88\x90\x9d\xd0\x9d")

        # Add start menu descriptions for new items
        f_startmenu = open(BIN_PATH + "01dabf_startmenu.bin", "rb")
        patch.seek(int("1dabf", 16) + rom_offset)
        patch.write(f_startmenu.read())
        f_startmenu.close
        f_itemdesc = open(BIN_PATH + "01e132_itemdesc.bin", "rb")
        patch.seek(int("1e132", 16) + rom_offset)
        patch.write(f_itemdesc.read())
        f_itemdesc.close

        # Update sprites for new items - first new item starts @108052, 7 new items
        # Points all items to unused sprite for item 4c ("76 83" in address table)
        patch.seek(int("108052", 16) + rom_offset)
        patch.write(b"\x76\x83\x76\x83\x76\x83\x76\x83\x76\x83\x76\x83\x76\x83")

        # Update item removal restriction flags
        patch.seek(int("1e12a", 16) + rom_offset)
        patch.write(b"\x9f\xff\x97\x37\xb0\x01")

        # Write STR, Psycho Dash, and Dark Friar upgrade items
        # Replaces code for item 05 - Inca Melody @3881d
        f_item05 = open(BIN_PATH + "03881d_item05.bin", "rb")
        patch.seek(int("3881d", 16) + rom_offset)
        patch.write(f_item05.read())
        f_item05.close

        # Modify Prison Key, now is destroyed when used
        patch.seek(int("385d4", 16) + rom_offset)
        patch.write(b"\x0a\x17\x0c\x18")
        patch.seek(int("385fe", 16) + rom_offset)
        patch.write(b"\x02\xd5\x02\x60")

        # Modify Lola's Melody, now is destroyed when used and only works in Itory
        f_item09 = open(BIN_PATH + "038bf5_item09.bin", "rb")
        patch.seek(int("38bf5", 16) + rom_offset)
        patch.write(f_item09.read())
        f_item09.close
        patch.seek(int("38bbc", 16) + rom_offset)
        patch.write(b"\x00")
        patch.seek(int("38bc1", 16) + rom_offset)
        patch.write(b"\x00")

        # Modify code for Memory Melody to heal Neil's memory
        f_item0d = open(BIN_PATH + "038f17_item0d.bin", "rb")
        patch.seek(int("38f17", 16) + rom_offset)
        patch.write(f_item0d.read())
        f_item0d.close

        # Modify Magic Dust, alters switch set and text
        patch.seek(int("393c3", 16) + rom_offset)
        patch.write(b"\x8a")

        # Modify Blue Journal, functions as an in-game tutorial
        patch.seek(int("3943b", 16) + rom_offset)
        patch.write(b"\xf0\x94")
        patch.seek(int("39440", 16) + rom_offset)
        patch.write(b"\x10\xf2")
        patch.seek(int("39445", 16) + rom_offset)
        patch.write(b"\x00\xf8")
        patch.seek(int("3944a", 16) + rom_offset)
        patch.write(b"\x00\xfb")

        patch.seek(int("3944e", 16) + rom_offset)
        patch.write(b"\xce" + qt_encode("       Welcome to") + b"\xcb\xcb" + qt_encode("  Bagu's Super-Helpful"))
        patch.write(b"\xcb" + qt_encode("  In-Game Tutorial!(TM)|"))
        patch.write(qt_encode("Whadaya wanna know about?") + b"\xcb" + qt_encode(" Beating the Game") + b"\xcb")
        patch.write(qt_encode(" Exploring the World") + b"\xcb" + qt_encode(" What If I'm Stuck?") + b"\xca")

        patch.seek(int("394f0", 16) + rom_offset)
        patch.write(b"\xce" + qt_encode("He closed the journal.") + b"\xc0")

        patch.seek(int("3f210", 16) + rom_offset)
        if settings.goal.value == Goal.DARK_GAIA.value:
            patch.write(b"\xce" + qt_encode("BEATING THE GAME:       You must do three things to beat the game:|"))
            patch.write(qt_encode("1. RESCUE KARA         Kara is trapped in a painting! You need Magic Dust to free her.|"))
            patch.write(qt_encode("She can be in either Edward's Prison, Diamond Mine, Angel Village, Mt. Temple, or Ankor Wat.|"))
            patch.write(qt_encode("You can search for her yourself or find Lance's Letter to learn where she is.|"))
            patch.write(qt_encode("Once you find Kara, use the Magic Dust on her portrait to free her.|"))
            patch.write(qt_encode("2. FIND/USE THE AURA  Using the Aura unlocks Shadow, the form you need to fight Dark Gaia.|"))
            patch.write(qt_encode("3. GATHER MYSTIC STATUES You may be required to gather Mystic Statues.|"))
            patch.write(qt_encode("The teacher in the South Cape classroom can tell you which Statues you need.|"))
            patch.write(qt_encode("STATUE 1: INCA RUINS    You need the Wind Melody, Diamond Block, and both Incan Statues.|"))
            patch.write(qt_encode("STATUE 2: SKY GARDEN    You need all four Crystal Balls to fight the boss Viper.|"))
            patch.write(qt_encode("STATUE 3: MU            You need 2 Statues of Hope and 2 Rama Statues to fight the Vampires.|"))
            patch.write(qt_encode("STATUE 4: GREAT WALL    You need Spin Dash and Dark Friar to face the boss Sand Fanger.|"))
            patch.write(qt_encode("STATUE 5: PYRAMID       You need all six Hieroglyphs as well as your father's journal.|"))
            patch.write(qt_encode("STATUE 6: BABEL TOWER   You need the Aura and the Crystal Ring to get in.|"))
            patch.write(qt_encode("Alternatively, if you collect enough Red Jewels to face Solid Arm, he can also take you there.|"))
            patch.write(qt_encode("Once you've freed Kara and gathered the Statues you need, enter any Dark Space and talk to Gaia.|"))
            patch.write(qt_encode("She will give you the option to face Dark Gaia and beat the game. Good luck, and have fun!") + b"\xc0")
        elif settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            patch.write(b"\xce" + qt_encode("BEATING THE GAME:       It's a Red Jewel hunt! The objective is super simple:|"))
            patch.write(qt_encode("Find the Red Jewels you need, and talk to the Jeweler. That's it!|"))
            patch.write(qt_encode("Check the Jeweler's inventory to find out how many Red Jewels you need to beat the game.|"))
            patch.write(qt_encode("Happy hunting!") + b"\xc0")

        patch.seek(int("3f800", 16) + rom_offset)
        patch.write(b"\xce" + qt_encode("EXPLORING THE WORLD:    When you start the game, you only have access to a few locations.|"))
        patch.write(qt_encode("As you gain more items, you will be able to visit other continents and access more locations.|"))
        patch.write(qt_encode("Here are some of the helpful travel items you can find in the game:|"))
        patch.write(qt_encode("- Lola's Letter         If you find this letter, read it and go see Erik in South Cape.|"))
        patch.write(qt_encode("- The Teapot            If you use the Teapot in the Moon Tribe camp, you can travel by Sky Garden.|"))
        patch.write(qt_encode("- Memory Melody         Play this melody in Neil's Cottage, and he'll fly you in his airplane.|"))
        patch.write(qt_encode("- The Will              Show this document to the stable masters in either Watermia or Euro.|"))
        patch.write(qt_encode("- The Large Roast       Give this to the hungry child in the Natives' Village.|"))
        patch.write(qt_encode("If you're ever stuck in a location, find a Dark Space. Gaia can always return you to South Cape.") + b"\xc0")

        patch.seek(int("3fb00", 16) + rom_offset)
        patch.write(b"\xce" + qt_encode("WHAT IF I'M STUCK?      There are a lot of item locations in this game! It's easy to get stuck.|"))
        patch.write(qt_encode("Here are some resources that might help you:|"))
        patch.write(qt_encode("- Video Tutorial        Search YouTube for a video guide of this randomizer.|"))
        patch.write(qt_encode("- Ask the Community     Find the IoGR community on Discord! Someone will be happy to help you.|"))
        if mode == 0:
            patch.write(qt_encode("- In-Game Tracker       Enter the east-most house in South Cape to check your collection rate.|"))
        else:
            patch.write(qt_encode("- In-Game Tracker       (Easy mode only)|"))
        patch.write(qt_encode("- Check the Spoiler Log Every seed comes with a detailed list of where every item can be found.") + b"\xc0")

        # Modify Lance's Letter
        # Prepare it to spoil Kara location
        f_item16 = open(BIN_PATH + "03950c_item16.bin", "rb")
        patch.seek(int("3950c", 16) + rom_offset)
        patch.write(f_item16.read())
        f_item16.close

        # Modify Teapot
        # Now activates in Moon Tribe camp instead of Euro
        f_item19 = open(BIN_PATH + "03983d_item19.bin", "rb")
        patch.seek(int("3983d", 16) + rom_offset)
        patch.write(f_item19.read())
        f_item19.close

        # Modify Black Glasses, now permanently worn and removed from inventory when used
        patch.seek(int("39981", 16) + rom_offset)
        patch.write(b"\x8a\x99\x02\xcc\xf5\x02\xd5\x1c\x60\xd3\x42\x8e\x8e\x8b\x8d\x84")
        patch.write(b"\xa3\xa3\xac\x88\x8d\xa4\x84\x8d\xa3\x88\x85\x88\x84\xa3\x4f\xc0")

        # Modify Aura, now unlocks Shadow's form when used
        patch.seek(int("39cdc", 16) + rom_offset)
        patch.write(b"\x02\xbf\xe4\x9c\x02\xcc\xb4\x60\xd3")
        patch.write(b"\xd6\x4c\x85\x8e\xa2\x8c\xac\xa5\x8d\x8b\x8e\x82\x8a\x84\x83\x4f\xc0")

        # Write 2 Jewel and 3 Jewel items; Lola's Letter now teaches Morse Code
        # Replaces and modifies code for item 25 - Lola's Letter @39d09
        f_item25 = open(BIN_PATH + "039d09_item25.bin", "rb")
        patch.seek(int("39d09", 16) + rom_offset)
        patch.write(f_item25.read())
        f_item25.close

        # Have fun with text in Item 26 (Father's Journal)
        patch.seek(int("39ea8", 16) + rom_offset)
        patch.write(qt_encode("It reads: ") + b"\x2d" + qt_encode("He who is ") + b"\xcb" + qt_encode("valiant and pure of spirit...") + b"\xcf\x2d")
        patch.write(qt_encode("... may find the Holy Grail in the Castle of... Aauugghh") + b"\x2e\xcf")
        patch.write(qt_encode("Here a page is missing.") + b"\xc0")

        # Modify Crystal Ring, now permanently worn and removed from inventory when used
        patch.seek(int("39f32", 16) + rom_offset)
        patch.write(b"\x3b\x9f\x02\xcc\x3e\x02\xd5\x27\x60\xd3\x41\x8b")
        patch.write(b"\x88\x8d\x86\xac\x81\x8b\x88\x8d\x86\x2a\xc0")

        # Write HP and DEF upgrade items; make the Apple non-consumable
        # Replaces and modifies code for item 28 - Apple @39f5d
        f_item28 = open(BIN_PATH + "039f5d_item28.bin", "rb")
        patch.seek(int("39f5d", 16) + rom_offset)
        patch.write(f_item28.read())
        f_item28.close

        # Update herb HP fill based on difficulty
        patch.seek(int("3889f", 16) + rom_offset)
        if mode == 0:  # Easy mode = full HP
            patch.write(b"\x28")
        elif mode == 2:  # Hard mode = fill 4 HP
            patch.write(b"\x04")
        elif mode == 3:  # Extreme mode = fill 2 HP
            patch.write(b"\x02")

        # Update HP jewel HP fill based on difficulty
        patch.seek(int("39f7a", 16) + rom_offset)
        if mode == 0:  # Easy mode = full HP
            patch.write(b"\x28")

        # Change item functionality for game variants
        patch.seek(int("3fce0", 16) + rom_offset)
        patch.write(qt_encode("Will drops the HP Jewel. It shatters into a million pieces. Whoops.", True))
        patch.seek(int("3fd30", 16) + rom_offset)
        patch.write(qt_encode("As the Jewel disappears, Will feels his strength draining!", True))

        f_rjm = open(BIN_PATH + "03fd70_rjm.bin", "rb")
        patch.seek(int("3fd70", 16) + rom_offset)
        patch.write(f_rjm.read())
        f_rjm.close

        # In OHKO, the HP Jewels do nothing, and start @1HP
        if settings.ohko:
            patch.seek(int("8068", 16) + rom_offset)
            patch.write(b"\x01")
            patch.seek(int("39f71", 16) + rom_offset)
            patch.write(b"\xe0\xfc\x02\xd5\x29\x60")
        # In Red Jewel Madness, start @40 HP, Red Jewels remove -1 HP when used
        elif settings.red_jewel_madness:
            # Start @ 40 HP
            patch.seek(int("8068", 16) + rom_offset)
            patch.write(b"\x28")
            # Red Jewels (item #$01) remove 1 HP when used
            patch.seek(int("384d5", 16) + rom_offset)
            patch.write(b"\x4c\x70\xfd")
            # 2 Red Jewels (item #$2e) removes 2 HP when used
            patch.seek(int("39d99", 16) + rom_offset)
            patch.write(b"\x01\x00\x8D\xB0\x0A\xD8\x4c\x76\xfd")
            # 3 Red Jewels (item #$2f) removes 3 HP when used
            patch.seek(int("39dd9", 16) + rom_offset)
            patch.write(b"\x02\x00\x8D\xB0\x0A\xD8\x4c\x7c\xfd")


        ##########################################################################
        #                  Update overworld map movement scripts
        #   Removes overworld animation and allows free travel within continents
        ##########################################################################
        # Update map choice scripts
        f_mapchoices = open(BIN_PATH + "03b401_mapchoices.bin", "rb")
        patch.seek(int("3b401", 16) + rom_offset)
        patch.write(f_mapchoices.read())
        f_mapchoices.close

        # Update map destination array
        f_mapdest = open(BIN_PATH + "03b955_mapdest.bin", "rb")
        patch.seek(int("3b955", 16) + rom_offset)
        patch.write(f_mapdest.read())
        f_mapdest.close

        ##########################################################################
        #                   Rewrite Red Jewel acquisition event
        #      Makes unique code for each instance (overwrites unused code)
        ##########################################################################
        # Fill block with new item acquisition code (16 items)
        f_redjewel = open(BIN_PATH + "00f500_redjewel.bin", "rb")
        patch.seek(int("f500", 16) + rom_offset)
        patch.write(f_redjewel.read())
        f_redjewel.close

        # Update event table instances to point to new events
        # New pointers include leading zero byte to negate event parameters
        patch.seek(int("c8318", 16) + rom_offset)  # South Cape: bell tower
        patch.write(b"\x00\x00\xf5\x80")
        patch.seek(int("c837c", 16) + rom_offset)  # South Cape: Lance's house
        patch.write(b"\x00\x80\xf5\x80")
        patch.seek(int("c8ac0", 16) + rom_offset)  # Underground Tunnel: barrel
        patch.write(b"\x00\x00\xf6\x80")
        patch.seek(int("c8b50", 16) + rom_offset)  # Itory Village: logs
        patch.write(b"\x00\x80\xf6\x80")
        patch.seek(int("c9546", 16) + rom_offset)  # Diamond Coast: jar
        patch.write(b"\x00\x00\xf7\x80")
        patch.seek(int("c97a6", 16) + rom_offset)  # Freejia: hotel
        patch.write(b"\x00\x80\xf7\x80")
        patch.seek(int("caf60", 16) + rom_offset)  # Angel Village: dance hall
        patch.write(b"\x00\x00\xf8\x80")
        patch.seek(int("cb3a6", 16) + rom_offset)  # Angel Village: Ishtar's room
        patch.write(b"\x00\x80\xf8\x80")
        patch.seek(int("cb563", 16) + rom_offset)  # Watermia: west Watermia
        patch.write(b"\x00\x00\xf9\x80")
        patch.seek(int("cb620", 16) + rom_offset)  # Watermia: gambling house
        patch.write(b"\x00\x80\xf9\x80")
        patch.seek(int("cbf55", 16) + rom_offset)  # Euro: behind house
        patch.write(b"\x00\x00\xfa\x80")
        patch.seek(int("cc17c", 16) + rom_offset)  # Euro: slave room
        patch.write(b"\x00\x80\xfa\x80")
        patch.seek(int("ccb14", 16) + rom_offset)  # Natives' Village: statue room
        patch.write(b"\x00\x00\xfb\x80")
        patch.seek(int("cd440", 16) + rom_offset)  # Dao: east Dao
        patch.write(b"\x00\x80\xfb\x80")
        patch.seek(int("cd57e", 16) + rom_offset)  # Pyramid: east entrance
        patch.write(b"\x00\x00\xfc\x80")
        patch.seek(int("ce094", 16) + rom_offset)  # Babel: pillow
        patch.write(b"\x00\x80\xfc\x80")

        ##########################################################################
        #                         Modify Game Start events
        ##########################################################################
        # Set beginning switches
        patch.seek(int("be51c", 16) + rom_offset)
        patch.write(b"\x80\x00\x12\x4c\x00\xfd")
        f_switches = open(BIN_PATH + "0bfd00_switches.bin", "rb")
        patch.seek(int("bfd00", 16) + rom_offset)
        patch.write(f_switches.read())
        f_switches.close

        ##########################################################################
        #                         Modify South Cape events
        ##########################################################################
        # Teacher sets switch #$38 and spoils Mystic Statues required
        f_teacher = open(BIN_PATH + "048a94_teacher.bin", "rb")
        patch.seek(int("48a94", 16) + rom_offset)
        patch.write(f_teacher.read())
        f_teacher.close

        # Force fisherman to always appear on E side of docks, and fix inventory full
        patch.seek(int("48377", 16) + rom_offset)
        patch.write(b"\x02\xd0\x10\x01\xaa\x83")
        patch.seek(int("48468", 16) + rom_offset)
        patch.write(b"\x02\xBF\x79\x84\x02\xD4\x01\x75\x84\x02\xCC\xD7\x6B" + INV_FULL)

        # Disable Lola Melody cutscene
        patch.seek(int("49985", 16) + rom_offset)
        patch.write(b"\x6b")

        # Set flag 35 at Lola Melody acquisition
        patch.seek(int("499dc", 16) + rom_offset)
        patch.write(b"\xeb\x99\x02\xbf\xe5\x9b\x02\xd4\x09\xf0\x99")
        patch.write(b"\x02\xcc\x35\x6b\x02\xbf\x94\x9d\x6b")
        patch.write(INV_FULL)

        # Erik in Seaside Cave allows player to use Lola's Letter to travel by sea
        f_seaside = open(BIN_PATH + "04b9a5_seaside.bin", "rb")
        patch.seek(int("4b9a5", 16) + rom_offset)
        patch.write(f_seaside.read())
        f_seaside.close
        patch.seek(int("4b8b6", 16) + rom_offset)
        patch.write(b"\x10\x01\x62")
        patch.seek(int("4b96a", 16) + rom_offset)
        patch.write(b"\xa5")

        # Various NPCs can give you a tutorial
        f_tutorial = open(BIN_PATH + "04fb50_tutorial.bin", "rb")
        patch.seek(int("4fb50", 16) + rom_offset)
        patch.write(f_tutorial.read())
        f_tutorial.close
        patch.seek(int("49231", 16) + rom_offset)  # NPC in front of school
        patch.write(b"\x50\xfb")
        # patch.seek(int("49238",16)+rom_offset)   # Grants max stats
        # patch.write(b"\xA9\x28\x00\x8D\xCA\x0A\x8D\xCE\x0A\x8D\xDC\x0A\x8D\xDE\x0A\x02\xBF\x4C\x92\x6B")
        # patch.write(qt_encode("Max stats baby!",True))

        # Turns house in South Cape into item-tracking overworld map (Easy only)
        if mode == 0:
            patch.seek(int("18480", 16) + rom_offset)
            patch.write(b"\x07\x90\x00\xd0\x03\x00\x00\x44")
            patch.seek(int("1854e", 16) + rom_offset)
            patch.write(b"\x00\x3e\x40\x02")
            patch.seek(int("c846c", 16) + rom_offset)
            patch.write(b"\x00\x01\x00\x00\xde\x86\x00\xFF\xCA")

            f_collectioncheck = open(BIN_PATH + "06dd30_collectioncheck.bin", "rb")
            patch.seek(int("6dd30", 16) + rom_offset)
            patch.write(f_collectioncheck.read())
            f_collectioncheck.close
        else:
            patch.seek(int("491ed", 16) + rom_offset)
            patch.write(qt_encode("This room is a lot cooler in Easy mode.", True))

        ##########################################################################
        #                       Modify Edward's Castle events
        ##########################################################################
        # Shorten Edward conversation
        patch.seek(int("4c3d6", 16) + rom_offset)
        patch.write(b"\x06\xc4")
        f_edward = open(BIN_PATH + "04c4fb_edward.bin", "rb")
        patch.seek(int("4c4fb", 16) + rom_offset)
        patch.write(f_edward.read())
        f_edward.close

        patch.seek(int("4c4fb", 16) + rom_offset)
        patch.write(b"\xd3")

        # Talking to Edward doesn't soft lock you
        patch.seek(int("4c746", 16) + rom_offset)
        patch.write(b"\x10")

        # Move guard to allow roast location get
        f_castleguard = open(BIN_PATH + "04d1a0_castleguard.bin", "rb")
        patch.seek(int("4d1a0", 16) + rom_offset)
        patch.write(f_castleguard.read())
        f_castleguard.close
        patch.seek(int("c8551", 16) + rom_offset)
        patch.write(b"\x10")

        #  Update Large Roast event
        patch.seek(int("4d0da", 16) + rom_offset)
        patch.write(b"\x02\xc0\xe1\xd0\x02\xc1\x6b\x02\xd0\x46\x00\xe9\xd0\x02\xe0")
        patch.write(b"\x02\xbf\x41\xd1\x02\xd4\x0a\xf6\xd0\x02\xcc\x46\x6b")
        patch.write(INV_FULL)

        # Fix hidden guard text box
        patch.seek(int("4c297", 16) + rom_offset)
        patch.write(b"\xc0")
        patch.seek(int("4c20e", 16) + rom_offset)
        patch.write(b"\x02\xBF\x99\xC2\x02\xD4\x00\x1B\xC2\x02\xCC\xD8\x6B" + INV_FULL)

        ##########################################################################
        #                   Modify Edward's Prison/Tunnel events
        ##########################################################################
        # Skip long cutscene in prison
        patch.seek(int("4d209", 16) + rom_offset)
        patch.write(b"\x34\xd2")
        patch.seek(int("4d234", 16) + rom_offset)
        patch.write(b"\x02\xd0\x23\x00\xcf\xd2\x02\xe0")
        patch.seek(int("4d335", 16) + rom_offset)
        patch.write(b"\x6b")

        # Move Dark Space, allows player to exit area without key
        # Set new X/Y coordinates in exit table
        patch.seek(int("18614", 16) + rom_offset)
        patch.write(b"\x12\x07")
        # Set new X/Y coordinates in event table
        patch.seek(int("C8635", 16) + rom_offset)
        patch.write(b"\x12\x08")

        # Progression triggers when Lilly is with you
        patch.seek(int("9aa45", 16) + rom_offset)
        patch.write(b"\x6f\x00")
        patch.seek(int("9aa4b", 16) + rom_offset)
        patch.write(b"\x02")
        patch.seek(int("9be74", 16) + rom_offset)
        patch.write(b"\xd7\x18")

        # Give appearing Dark Space the option of handling an ability
        patch.seek(int("9bf7f", 16) + rom_offset)
        patch.write(b"\xAC\xD6\x88\xA8\x00\xC0\x04\x00\x0B\x4c\x10\xf7")
        patch.seek(int("9f710", 16) + rom_offset)
        patch.write(b"\xA5\x0E\x85\x24\xA9\x00\x20\x85\x0E\x02\xE0")
        patch.seek(int("c8aa2", 16) + rom_offset)
        patch.write(b"\x03")

        # Fix forced form change
        patch.seek(int("9c037", 16) + rom_offset)
        patch.write(FORCE_CHANGE + b"\x02\xe0")

        ##########################################################################
        #                            Modify Itory events
        ##########################################################################
        # Lilly event becomes Lola's Melody handler
        f_itory = open(BIN_PATH + "04e2a3_itory.bin", "rb")
        patch.seek(int("4e2a3", 16) + rom_offset)
        patch.write(f_itory.read())
        f_itory.close

        # Lilly now joins if you give her the Necklace
        f_lilly = open(BIN_PATH + "04e5ff_lilly.bin", "rb")
        patch.seek(int("4e5ff", 16) + rom_offset)
        patch.write(f_lilly.read())
        f_lilly.close
        patch.seek(int("4e5a6", 16) + rom_offset)
        patch.write(b"\x6f")
        patch.seek(int("4e5ac", 16) + rom_offset)
        patch.write(b"\xff\xe5\x02\x0b\x6b")

        # Shorten Inca Statue get
        patch.seek(int("4f37b", 16) + rom_offset)
        patch.write(b"\x02\xbf\x8d\xf3\x6b")

        # For elder to always give spoiler
        patch.seek(int("4e933", 16) + rom_offset)
        patch.write(b"\x10\x01")
        patch.seek(int("4e97a", 16) + rom_offset)
        patch.write(b"\x02\xbf\xff\xe9\x6b")

        ##########################################################################
        #                          Modify Moon Tribe events
        ##########################################################################
        # Allows player to use Teapot to travel by Sky Garden
        f_moontribe = open(BIN_PATH + "09d11e_moontribe.bin", "rb")
        patch.seek(int("9d11e", 16) + rom_offset)
        patch.write(f_moontribe.read())
        f_moontribe.close

        # Lilly event serves as an overworld exit
        patch.seek(int("4f441", 16) + rom_offset)
        patch.write(b"\x00\x00\x30\x02\x45\x14\x1c\x17\x1d\x4d\xf4\x6b")
        patch.write(b"\x02\x40\x00\x04\x54\xf4\x6b\x02\x66\x90\x00\x60\x02\x01\x02\xC1\x6b")

        # Adjust timer by mode
        timer = 20
        if mode == 0:
            timer += 5
        if settings.enemizer.value != Enemizer.NONE.value:
            timer += 5
            if settings.enemizer.value != Enemizer.LIMITED.value:
                timer += 5
        patch.seek(int("4f8b8", 16) + rom_offset)
        patch.write(binascii.unhexlify(str(timer)))

        # Shorten Inca Statue get
        patch.seek(int("4fae7", 16) + rom_offset)
        patch.write(b"\x02\xbf\xf9\xfa\x6b")

        ##########################################################################
        #                          Modify Inca events
        ##########################################################################
        # Fix forced form change
        patch.seek(int("9cfaa", 16) + rom_offset)
        patch.write(FORCE_CHANGE + b"\xA9\xF0\xEF\x1C\x5A\x06\x02\xe0")

        # Put Gold Ship captain at Inca entrance
        patch.seek(int("c8c9c", 16) + rom_offset)
        patch.write(b"\x19\x1c\x00\x4e\x85\x85\x00")

        ##########################################################################
        #                          Modify Gold Ship events
        ##########################################################################
        # Move Seth from deserted ship to gold ship, allows player to acquire item
        # Write pointer to Seth event in new map
        patch.seek(int("c945c", 16) + rom_offset)
        patch.write(b"\x0b\x24\x00\x3e\x96\x85\x00\xff\xca")
        patch.seek(int("c805a", 16) + rom_offset)
        patch.write(b"\x65")
        # Modify Seth event to ignore switch conditions
        patch.seek(int("59643", 16) + rom_offset)
        patch.write(b"\x10\x00")
        # Add in inventory full text
        patch.seek(int("59665", 16) + rom_offset)
        patch.write(INV_FULL)

        # Entering Gold Ship doesn't lock out Castoth
        patch.seek(int("58188", 16) + rom_offset)
        patch.write(b"\x02\xc1\x02\xc1")
        patch.seek(int("18a09", 16) + rom_offset)
        patch.write(b"\xd0\x00\x40\x02\x03")

        # Have ladder NPC move aside only if Mystic Statue has been acquired
        patch.seek(int("583cb", 16) + rom_offset)
        patch.write(b"\x10")

        # Modify queen switches
        patch.seek(int("58a04", 16) + rom_offset)
        patch.write(b"\x10\x00")
        patch.seek(int("58a1f", 16) + rom_offset)
        patch.write(b"\x10")

        # Have crow's nest NPC warp directly to Diamond Coast
        # Also checks for Castoth being defeated
        f_goldship = open(BIN_PATH + "0584a9_goldship.bin", "rb")
        patch.seek(int("584a9", 16) + rom_offset)
        patch.write(f_goldship.read())
        f_goldship.close

        # Sleeping sends player to Diamond Coast
        patch.seek(int("586a3", 16) + rom_offset)
        patch.write(b"\x02\x26\x30\x48\x00\x20\x00\x03\x00\x21")

        ##########################################################################
        #                        Modify Diamond Coast events
        ##########################################################################
        # Allow Turbo to contact Seth
        patch.seek(int("c953e", 16) + rom_offset)
        patch.write(b"\x01")
        patch.seek(int("5aa76", 16) + rom_offset)
        patch.write(b"\x00\xff")
        patch.seek(int("5ff00", 16) + rom_offset)
        patch.write(b"\x02\xCC\x01\x02\xD0\x11\x01\x0E\xFF\x02\xBF\x60\xFF\x6B\x02\xD0\x12\x01\x1B\xFF")
        patch.write(b"\x02\xcc\x12\x02\xBF\x1F\xFF\x5C\xBD\xB9\x84")
        patch.write(b"\xd3" + qt_encode("Woof woof!") + b"\xcb")
        patch.write(qt_encode("(Oh good, you know Morse Code. Let's see what Seth's up to:)") + b"\xc0")
        patch.write(b"\xd3" + qt_encode("Woof woof!") + b"\xcb")
        patch.write(qt_encode("(You don't happen to know Morse Code, do you?)") + b"\xc0")

        # Kara event serves as an overworld exit
        patch.seek(int("5aa9e", 16) + rom_offset)
        patch.write(b"\x00\x00\x30\x02\x45\x03\x00\x06\x01\xaa\xaa\x6b")
        patch.write(b"\x02\x40\x00\x08\xb1\xaa\x6b\x02\x66\x50\x02\x50\x03\x07\x02\xC1\x6b")

        ##########################################################################
        #                           Modify Freejia events
        ##########################################################################
        # Trash can 1 gives you an item instead of a status upgrade
        # NOTE: This cannibalizes the following event @5cfbc (locked door)
        f_freejia = open(BIN_PATH + "05cf85_freejia.bin", "rb")
        patch.seek(int("5cf85", 16) + rom_offset)
        patch.write(f_freejia.read())
        f_freejia.close

        # Give full inventory text to trash can 2
        patch.seek(int("5cf37", 16) + rom_offset)
        patch.write(b"\x02\xBF\x49\xCF\x02\xD4\x12\x44\xCF\x02\xCC\x53\x6B" + INV_FULL)

        # Redirect event table to bypass deleted event
        # Changes locked door to a normal door
        patch.seek(int("c95bb", 16) + rom_offset)
        patch.write(b"\xf3\xc5\x80")

        # Update NPC dialogue to acknowledge change
        patch.seek(int("5c331", 16) + rom_offset)
        patch.write(b"\x42\xa2\x80\xa0\x2b\xac\x48\xac\xd6\xae\xa4\x87\x84\xac\xd7\x58\xcb\xa5")
        patch.write(b"\x8d\x8b\x8e\x82\x8a\x84\x83\xac\x80\x86\x80\x88\x8d\x2a\x2a\x2a\xc0")

        # Add inventory full option to Creepy Guy event
        patch.seek(int("5b6df", 16) + rom_offset)
        patch.write(INV_FULL)

        # Alter laborer text
        patch.seek(int("5bfdb", 16) + rom_offset)
        patch.write(b"\xde\xbf")

        # Have some fun with snitch item text
        patch.seek(int("5b8bc", 16) + rom_offset)
        patch.write(b"\x62")
        patch.seek(int("5b925", 16) + rom_offset)
        patch.write(b"\x88\xa4\x84\x8c\x2a\xcb\xac\x69\x84\xa3\x2b\xac\x48\x0e\x8c\xac\x80\xac\x81")
        patch.write(b"\x80\x83\xac\xa0\x84\xa2\xa3\x8e\x8d\xcb\xac\x63\x8d\x88\xa4\x82\x87\x84\xa3")
        patch.write(b"\xac\x86\x84\xa4\xac\xa3\xa4\x88\xa4\x82\x87\x84\xa3\x2b\xac\xa9\x8e\xca")

        ##########################################################################
        #                        Modify Diamond Mine events
        ##########################################################################
        # Trapped laborer gives you an item instead of sending Jewels to Jeweler
        patch.seek(int("5d739", 16) + rom_offset)
        patch.write(b"\x4c\x5d\xd8\x85")
        f_trappedlaborer = open(BIN_PATH + "05d7e2_trappedlaborer.bin", "rb")
        patch.seek(int("5d7e2", 16) + rom_offset)
        patch.write(f_trappedlaborer.read())
        f_trappedlaborer.close

        # Shorten laborer items
        patch.seek(int("aa753", 16) + rom_offset)
        patch.write(b"\xef\xa7")
        patch.seek(int("aa75a", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("aa773", 16) + rom_offset)
        patch.write(b"\x5c\xa8")
        patch.seek(int("aa77a", 16) + rom_offset)
        patch.write(b"\x6b")

        # Shorten morgue item get
        patch.seek(int("5d4d8", 16) + rom_offset)
        patch.write(b"\x02\xbf\xeb\xd4\x02\xe0")

        # Cut out Sam's song
        patch.seek(int("5d24f", 16) + rom_offset)
        patch.write(b"\x6b")

        # Give appearing Dark Space the option of handling an ability
        patch.seek(int("5d62f", 16) + rom_offset)
        patch.write(b"\xAC\xD6\x88\x00\x2B\xA5\x0E\x85\x24\xA9\x00\x20\x85\x0E\x02\xE0")

        ##########################################################################
        #                       Modify Neil's Cottage events
        ##########################################################################
        # Allow travel by plane with the Memory Melody
        f_neilscottage = open(BIN_PATH + "05d89a_neilscottage.bin", "rb")
        patch.seek(int("5d89a", 16) + rom_offset)
        patch.write(f_neilscottage.read())
        f_neilscottage.close

        # Invention event serves as an overworld exit
        patch.seek(int("5e305", 16) + rom_offset)
        patch.write(b"\x00\x00\x30\x02\x45\x07\x0d\x0a\x0e\x11\xe3\x6b")
        patch.write(b"\x02\x40\x00\x04\x18\xe3\x6b\x02\x66\x70\x02\x70\x02\x07\x02\xC1\x6b")

        ##########################################################################
        #                            Modify Nazca events
        ##########################################################################
        # Speedup warp sequence to Sky Garden
        f_nazca = open(BIN_PATH + "05e647_nazca.bin", "rb")
        patch.seek(int("5e647", 16) + rom_offset)
        patch.write(f_nazca.read())
        f_nazca.close

        # Allow exit to world map
        patch.seek(int("5e80c", 16) + rom_offset)
        patch.write(b"\x02\x66\x10\x03\x90\x02\x07\x02\xC1\x6B")

        ##########################################################################
        #                          Modify Sky Garden events
        ##########################################################################
        # Allow travel from Sky Garden to other locations
        f_skygarden = open(BIN_PATH + "05f356_skygarden.bin", "rb")
        patch.seek(int("5f356", 16) + rom_offset)
        patch.write(f_skygarden.read())
        f_skygarden.close

        # Instant form change & warp to Seaside Palace if Viper is defeated
        patch.seek(int("ace9b", 16) + rom_offset)
        patch.write(b"\x4c\x90\xfd")
        patch.seek(int("acecb", 16) + rom_offset)
        patch.write(b"\x01\x02\x26\x5a\x90\x00\x70\x00\x83\x00\x14\x02\xc1\x6b")

        f_viperchange = open(BIN_PATH + "0afd90_viperchange.bin", "rb")
        patch.seek(int("afd90", 16) + rom_offset)
        patch.write(f_viperchange.read())
        f_viperchange.close

        ##########################################################################
        #                       Modify Seaside Palace events
        ##########################################################################
        # Add exit from Mu passage to Angel Village @191de
        patch.seek(int("191de", 16) + rom_offset)
        patch.write(b"\x04\x06\x02\x03\x69\xa0\x02\x38\x00\x00\x00\x13")  # Temporarily put exit one tile south
        # patch.write(b"\x04\x05\x02\x03\x69\xa0\x02\x38\x00\x00\x00\x13")  # Change to this if map is ever updated

        # Replace Mu Passage map with one that includes a door to Angel Village
        f_mupassage = open(BIN_PATH + "1e28a5_mupassage.bin", "rb")
        patch.seek(int("1e28a5", 16) + rom_offset)
        patch.write(f_mupassage.read())
        f_mupassage.close

        # Shorten NPC item get
        patch.seek(int("68b01", 16) + rom_offset)
        patch.write(b"\x6b")

        # Purification event won't softlock if you don't have Lilly
        patch.seek(int("69406", 16) + rom_offset)
        patch.write(b"\x10")
        patch.seek(int("6941a", 16) + rom_offset)
        patch.write(b"\x01\x02\xc1\x02\xc1")

        # Remove Lilly text when Mu door opens
        patch.seek(int("39174", 16) + rom_offset)
        patch.write(b"\x60")
        patch.seek(int("391d7", 16) + rom_offset)
        patch.write(b"\xc0")

        # Allow player to open Mu door from the back
        f_mudoor = open(BIN_PATH + "069739_mudoor.bin", "rb")
        patch.seek(int("69739", 16) + rom_offset)
        patch.write(f_mudoor.read())
        f_mudoor.close

        # Remove fanfare from coffin item get
        patch.seek(int("69232", 16) + rom_offset)
        patch.write(b"\x9e\x93\x4c\x61\x92")
        patch.seek(int("69267", 16) + rom_offset)
        patch.write(b"\x80\x04")

        # Make coffin spoiler re-readable
        patch.seek(int("68ff3", 16) + rom_offset)
        patch.write(b"\xf5\x8f")
        patch.seek(int("68ffb", 16) + rom_offset)
        patch.write(b"\x70\xe5")
        patch.seek(int("69092", 16) + rom_offset)
        patch.write(b"\x02\xce\x01\x02\x25\x2F\x0A\x4c\xfd\x8f")
        patch.seek(int("6e570", 16) + rom_offset)
        patch.write(b"\x02\xD1\x3A\x01\x01\x8A\xE5\x02\xD0\x6F\x01\x82\xE5\x02\xBF\xA7\x90\x6B")
        patch.write(b"\x02\xBF\xCF\x90\x02\xCC\x01\x6B\x02\xBF\x67\x91\x6B")

        ##########################################################################
        #                             Modify Mu events
        ##########################################################################
        # Add "inventory full" option to Statue of Hope items
        patch.seek(int("698cd", 16) + rom_offset)
        patch.write(INV_FULL)

        # Shorten Statue of Hope get
        patch.seek(int("698b8", 16) + rom_offset)
        patch.write(b"\x02\xBF\xD2\x98\x02\xD4\x28\xCD\x98\x02\xCC\x79\x6B")
        patch.seek(int("69960", 16) + rom_offset)
        patch.write(b"\x02\xBF\x75\x99\x02\xD4\x1E\xCD\x98\x02\xCC\x7F\x6B")

        # Shorten Rama statue event
        patch.seek(int("69e50", 16) + rom_offset)
        patch.write(b"\x10")
        patch.seek(int("69f26", 16) + rom_offset)
        patch.write(b"\x00")

        # Text in Hope Room
        patch.seek(int("69baa", 16) + rom_offset)
        patch.write(qt_encode("Hey.", True))

        # Spirits in Rama statue room can't lock you
        patch.seek(int("6a07a", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("6a082", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("6a08a", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("6a092", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("6a09a", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("6a0a2", 16) + rom_offset)
        patch.write(b"\x6b")

        # Move exits around to make Vampires required for Statue
        patch.seek(int("193ea", 16) + rom_offset)
        patch.write(b"\x5f\x80\x00\x50\x00\x03\x00\x44")
        patch.seek(int("193f8", 16) + rom_offset)
        patch.write(b"\x65\xb8\x00\x80\x02\x03\x00\x44")
        patch.seek(int("69c62", 16) + rom_offset)
        patch.write(b"\x67\x78\x01\xd0\x01\x80\x01\x22")
        patch.seek(int("6a4c9", 16) + rom_offset)
        patch.write(b"\x02\x26\x66\xf8\x00\xd8\x01\x00\x00\x22\x02\xc1\x6b")

        # Instant form change after Vamps are defeated
        patch.seek(int("6a43b", 16) + rom_offset)
        patch.write(b"\x4c\x00\xe5")

        f_vampchange = open(BIN_PATH + "06e500_vampchange.bin", "rb")
        patch.seek(int("6e500", 16) + rom_offset)
        patch.write(f_vampchange.read())
        f_vampchange.close

        ##########################################################################
        #                       Modify Angel Village events
        ##########################################################################
        # Add exit from Angel Village to Mu passage @1941a
        patch.seek(int("1941a", 16) + rom_offset)
        patch.write(b"\x2a\x05\x01\x01\x5e\x48\x00\x90\x00\x01\x00\x14")  # Temporarily put exit one tile south
        # patch.write(b"\x2a\x05\x01\x01\x5e\x48\x00\x80\x00\x01\x00\x14")  # Change to this if map is ever updated

        # Update sign to read "Passage to Mu"
        f_angelsign = open(BIN_PATH + "06ba36_angelsign.bin", "rb")
        patch.seek(int("6ba36", 16) + rom_offset)
        patch.write(f_angelsign.read())
        f_angelsign.close

        # Entering this area clears your enemy defeat count and forces change to Will
        patch.seek(int("6bff7", 16) + rom_offset)
        patch.write(b"\x00\x00\x30\x02\x40\x01\x0F\x01\xC0\x6b")
        patch.write(b"\xA0\x00\x00\xA9\x00\x00\x99\x80\x0A\xC8\xC8\xC0\x20\x00\xD0\xF6")
        patch.write(FORCE_CHANGE + b"\x02\xE0")

        # Insert new arrangement for map 109, takes out rock to prevent spin dash softlock
        f_angelmap = open(BIN_PATH + "1a5a37_angelmap.bin", "rb")
        patch.seek(int("1a5a37", 16) + rom_offset)
        patch.write(f_angelmap.read())
        f_angelmap.close

        # Ishtar's game never closes
        patch.seek(int("6d9fc", 16) + rom_offset)
        patch.write(b"\x10")
        patch.seek(int("6cede", 16) + rom_offset)
        patch.write(b"\x9c\xa6\x0a\x6b")
        patch.seek(int("6cef6", 16) + rom_offset)
        patch.write(b"\x40\x86\x80\x88\x8d\x4f\xc0")

        ##########################################################################
        #                           Modfy Watermia events
        ##########################################################################
        # Allow NPC to contact Seth
        patch.seek(int("78542", 16) + rom_offset)
        patch.write(b"\x50\xe9")
        patch.seek(int("7e950", 16) + rom_offset)
        patch.write(b"\x02\xD0\x11\x01\x5B\xE9\x02\xBF\xb8\xe9\x6B\x02\xD0\x12\x01\x68\xE9")
        patch.write(b"\x02\xcc\x12\x02\xBF\x6c\xE9\x5C\xBD\xB9\x84")
        patch.write(b"\xd3" + qt_encode("Oh, you know Bagu? Then I can help you cross.") + b"\xcb")
        patch.write(qt_encode("(And by Bagu I mean Morse Code.)") + b"\xc0")
        patch.write(b"\xd3" + qt_encode("Only town folk may cross this river!") + b"\xcb")
        patch.write(qt_encode("(Or, if you can talk to fish, I guess.)") + b"\xc0")

        # Allow for travel from  Watermia to Euro
        # Update address pointer
        patch.seek(int("78544", 16) + rom_offset)
        patch.write(b"\x69")

        # Update event address pointers
        f_watermia1 = open(BIN_PATH + "078569_watermia1.bin", "rb")
        patch.seek(int("78569", 16) + rom_offset)
        patch.write(f_watermia1.read())
        f_watermia1.close

        # Change textbox contents
        f_watermia2 = open(BIN_PATH + "0786c1_watermia2.bin", "rb")
        patch.seek(int("786c1", 16) + rom_offset)
        patch.write(f_watermia2.read())
        f_watermia2.close

        # Russian Glass NPC just gives you the item
        f_russianglass = open(BIN_PATH + "079237_russianglass.bin", "rb")
        patch.seek(int("79237", 16) + rom_offset)
        patch.write(f_russianglass.read())
        f_russianglass.close

        # Fix Lance item get text
        patch.seek(int("7ad28", 16) + rom_offset)
        patch.write(INV_FULL)

        ##########################################################################
        #                          Modify Great Wall events
        ##########################################################################
        # Rewrite Necklace Stone acquisition event
        # Fill block with new item acquisition code (2 items)
        f_necklace = open(BIN_PATH + "07b59e_necklace.bin", "rb")
        patch.seek(int("7b59e", 16) + rom_offset)
        patch.write(f_necklace.read())
        f_necklace.close

        # Update event table instance to point to new events
        # New pointers include leading zero byte to negate event parameters
        patch.seek(int("cb822", 16) + rom_offset)  # First stone, map 130
        patch.write(b"\x00\x9e\xb5\x87")
        patch.seek(int("cb94a", 16) + rom_offset)  # Second stone, map 131
        patch.write(b"\x00\xfe\xb5\x87")

        # Entering wrong door in 2nd map area doesn't softlock you
        patch.seek(int("19a4c", 16) + rom_offset)
        patch.write(b"\x84")

        # Give appearing Dark Space the option of handling an ability
        patch.seek(int("7be0b", 16) + rom_offset)
        patch.write(b"\xAC\xD6\x88\xC8\x01\x80\x02\x00\x2B\xA5\x0E\x85\x24\xA9\x00\x20\x85\x0E\x02\xE0")
        patch.seek(int("cbc60", 16) + rom_offset)
        patch.write(b"\x03")

        # Exit after Sand Fanger takes you back to start
        patch.seek(int("19c84", 16) + rom_offset)
        patch.write(b"\x82\x10\x00\x90\x00\x07\x00\x18")

        ##########################################################################
        #                            Modify Euro events
        ##########################################################################
        # Allow travel from Euro to Watermia
        # Update event address pointers
        f_euro1 = open(BIN_PATH + "07c432_euro1.bin", "rb")
        patch.seek(int("7c432", 16) + rom_offset)
        patch.write(f_euro1.read())
        f_euro1.close
        # Change textbox contents
        f_euro2 = open(BIN_PATH + "07c4d0_euro2.bin", "rb")
        patch.seek(int("7c4d0", 16) + rom_offset)
        patch.write(f_euro2.read())
        f_euro2.close
        patch.seek(int("7c482", 16) + rom_offset)
        patch.write(qt_encode("A moose once bit my sister.", True))

        # Neil in Euro
        f_euroneil = open(BIN_PATH + "07e398_euroneil.bin", "rb")
        patch.seek(int("7e398", 16) + rom_offset)
        patch.write(f_euroneil.read())
        f_euroneil.close
        patch.seek(int("7e37f", 16) + rom_offset)
        patch.write(b"\x14\x00")
        patch.seek(int("7e394", 16) + rom_offset)
        patch.write(b"\x10\x00")

        # Hidden house replaces STR upgrade with item acquisition
        f_euroitem = open(BIN_PATH + "07e517_euroitem.bin", "rb")
        patch.seek(int("7e517", 16) + rom_offset)
        patch.write(f_euroitem.read())
        f_euroitem.close

        # Speed up store line
        patch.seek(int("7d5e1", 16) + rom_offset)
        patch.write(b"\x00\x01")

        # Change vendor event, allows for only one item acquisition
        # Note: this cannibalizes the following event
        patch.seek(int("7c0a7", 16) + rom_offset)
        patch.write(b"\x02\xd0\x9a\x01\xba\xc0\x02\xbf\xf3\xc0\x02\xd4\x28\xbf\xc0")
        patch.write(b"\x02\xcc\x9a\x6b\x02\xbf\xdd\xc0\x6b")
        patch.write(INV_FULL)
        # Change pointer for cannibalized event
        patch.seek(int("7c09b", 16) + rom_offset)
        patch.write(b"\xc4")

        # Store replaces status upgrades with item acquisition
        patch.seek(int("7cd03", 16) + rom_offset)  # HP upgrade
        patch.write(b"\x02\xd0\xf0\x01\x32\xcd\x02\xc0\x10\xcd\x02\xc1\x6b")
        patch.write(b"\x02\xd4\x29\x20\xcd\x02\xcc\xf0\x02\xbf\x39\xcd\x02\xe0")
        patch.seek(int("7cdf7", 16) + rom_offset)  # Dark Friar upgrade
        patch.write(b"\x02\xd4\x2d\x05\xce\x02\xcc\xf1\x02\xbf\x28\xce\x02\xe0")
        patch.write(b"\x02\xbf\x3e\xce\x6b")

        # Old men text no longer checks for Teapot
        patch.seek(int("7d60a", 16) + rom_offset)
        patch.write(b"\x14\xd6")
        patch.seek(int("7d7a5", 16) + rom_offset)
        patch.write(b"\xbd\xd7")

        # Various NPC dialogue
        patch.seek(int("7d6db", 16) + rom_offset)
        patch.write(b"\x2A\xD0\xC8\xC9\x1E\xC2\x0B\xC2\x03" + qt_encode("It could be carried by an African swallow!"))
        patch.write(b"\xCF\xC2\x03\xC2\x04" + qt_encode("Oh yeah, an African swallow maybe, but not a European swallow, that's my point!") + b"\xc0")
        patch.seek(int("7d622", 16) + rom_offset)
        patch.write(qt_encode("Rofsky: Wait a minute, supposing two swallows carried it together?...") + b"\xc0")
        patch.seek(int("7c860", 16) + rom_offset)
        patch.write(b"\xce" + qt_encode("Nobody expects the Spanish Inquisition!") + b"\xc0")
        patch.seek(int("7c142", 16) + rom_offset)
        patch.write(qt_encode("I am no longer infected.", True))
        patch.seek(int("7c160", 16) + rom_offset)
        patch.write(qt_encode("My hovercraft is full of eels.", True))
        patch.seek(int("7c182", 16) + rom_offset)
        patch.write(qt_encode("... w-i-i-i-i-ith... a herring!!", True))
        patch.seek(int("7c1b6", 16) + rom_offset)
        patch.write(qt_encode("It's only a wafer-thin mint, sir...", True))
        patch.seek(int("7c1dc", 16) + rom_offset)
        patch.write(b"\xd3" + qt_encode("The mill's closed. There's no more work. We're destitute.|"))
        patch.write(qt_encode("I've got no option but to sell you all for scientific experiments.") + b"\xc0")
        patch.seek(int("7c3d4", 16) + rom_offset)
        patch.write(qt_encode("You're a looney.", True))

        ##########################################################################
        #                        Modify Native Village events
        ##########################################################################
        # Native can guide you to Dao if you give him the roast
        f_natives = open(BIN_PATH + "088fc4_natives.bin", "rb")
        patch.seek(int("88fc4", 16) + rom_offset)
        patch.write(f_natives.read())
        f_natives.close

        # Change event pointers for cannibalized NPC code
        patch.seek(int("cca93", 16) + rom_offset)
        patch.write(b"\x88\x8f\x88")

        ##########################################################################
        #                         Modify Ankor Wat events
        ##########################################################################
        # Modify Gorgon Flower event, make it a simple item get
        f_ankorwat1 = open(BIN_PATH + "089abf_ankorwat.bin", "rb")
        patch.seek(int("89abf", 16) + rom_offset)
        patch.write(f_ankorwat1.read())
        f_ankorwat1.close

        # Shorten black glasses get
        patch.seek(int("89fa9", 16) + rom_offset)
        patch.write(b"\x02\xe0")

        # Bright room looks at switch 4f rather than equipment
        f_ankorwat2 = open(BIN_PATH + "089a31_ankorwat.bin", "rb")
        patch.seek(int("89a31", 16) + rom_offset)
        patch.write(f_ankorwat2.read())
        f_ankorwat2.close

        ##########################################################################
        #                            Modify Dao events
        ##########################################################################
        # Snake game grants an item instead of sending Jewels to the Jeweler
        f_snakegame = open(BIN_PATH + "08b010_snakegame.bin", "rb")
        patch.seek(int("8b010", 16) + rom_offset)
        patch.write(f_snakegame.read())
        f_snakegame.close

        # Neil in Dao
        f_daoneil = open(BIN_PATH + "08a5bd_daoneil.bin", "rb")
        patch.seek(int("8a5bd", 16) + rom_offset)
        patch.write(f_daoneil.read())
        f_daoneil.close
        patch.seek(int("8a5b3", 16) + rom_offset)
        patch.write(b"\x14\x00")

        # Allow travel back to Natives' Village
        patch.seek(int("8b16d", 16) + rom_offset)
        patch.write(b"\x4c\x50\xfe")
        patch.seek(int("8fe50", 16) + rom_offset)
        patch.write(b"\x02\xBF\x71\xFE\x02\xBE\x02\x01\x5A\xFE\x60\xFE\x60\xFE\x65\xFE")
        patch.write(b"\x02\xBF\x93\xFE\x6B\x02\x26\xAC\xC0\x01\xD0\x01\x06\x00\x22\x02\xC5")
        patch.write(b"\xd3" + qt_encode("Go to Natives' Village?") + b"\xcb\xac")
        patch.write(qt_encode("No") + b"\xcb\xac" + qt_encode("Yes") + b"\xca")
        patch.write(b"\xce" + qt_encode("Come back anytime!") + b"\xc0")

        # Modify two-item acquisition event
        patch.seek(int("8b1bb", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("8b189", 16) + rom_offset)
        patch.write(b"\xe0\xfd")
        patch.seek(int("8fde0", 16) + rom_offset)
        patch.write(b"\xD3\x4b\x8e\x8b\x80\x0e\xa3\xac\x4b\x84\xa4\xa4\x84\xa2\xCB")
        patch.write(b"\x49\x8e\xa5\xa2\x8d\x80\x8b\xac\xac\xac\xac\xac\xac\xCF\xCE")
        patch.write(qt_encode("If you want a guide to take you to the Natives' Village, I can get one for you.") + b"\xc0")

        # Spirit appears only after you defeat Mummy Queen or Solid Arm
        patch.seek(int("980cb", 16) + rom_offset)
        patch.write(b"\x4c\xb0\xf6")
        patch.seek(int("9f6b0", 16) + rom_offset)
        patch.write(b"\x02\xd0\xf6\x01\xd1\x80\x02\xd1\x79\x01\x01\xd1\x80\x02\xe0")

        ##########################################################################
        #                           Modify Pyramid events
        ##########################################################################
        # Can give journal to the guide in hieroglyph room
        patch.seek(int("8c207", 16) + rom_offset)
        patch.write(b"\x0E\xC2\x02\x0B\x02\xC1\x6B\x02\xD0\xEF\x01\x1E\xC2\x02\xD6\x26\x22\xC2")
        patch.write(b"\x02\xBF\x2D\xC2\x6B\x5C\x08\xF2\x83\x02\xCC\xEF\x02\xD5\x26\x02\xBF\x7F\xC2\x6B")
        patch.write(qt_encode("If you have any information about the pyramid, I'd be happy to hold onto it for you.", True))
        patch.write(qt_encode("I'll hold onto that journal for you. Come back anytime if you want to read it.", True))
        patch.seek(int("3f208", 16) + rom_offset)
        patch.write(b"\x02\xbf\x1a\x9e\x6b")

        # Shorten hieroglyph get
        patch.seek(int("8c7b8", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("8c87f", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("8c927", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("8c9cf", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("8ca77", 16) + rom_offset)
        patch.write(b"\x6b")
        patch.seek(int("8cb1f", 16) + rom_offset)
        patch.write(b"\x6b")

        ##########################################################################
        #                            Modify Babel events
        ##########################################################################
        # Move Dark Space in Babel Tower from map 224 to map 223
        # Allows player to exit Babel without crystal ring
        # Modify address pointer for Maps 224 in exit table
        patch.seek(int("183f4", 16) + rom_offset)
        patch.write(b"\xea")
        # Move Dark Space exit data to Map 223
        f_babel1 = open(BIN_PATH + "01a7c2_babel.bin", "rb")
        patch.seek(int("1a7c2", 16) + rom_offset)
        patch.write(f_babel1.read())
        f_babel1.close
        # Modify address pointer for Maps 224-227 in event table
        patch.seek(int("c81c0", 16) + rom_offset)
        patch.write(b"\xa2\xe0\xe3\xe0\x0f\xe1\x2d\xe1")
        # Assign new Dark Space correct overworld name
        patch.seek(int("bf8c4", 16) + rom_offset)
        patch.write(b"\x47\xfa")
        # Move Dark Space event data to Map 223
        # Also move spirits for entrance warp
        f_babel2 = open(BIN_PATH + "0ce099_babel.bin", "rb")
        patch.seek(int("ce099", 16) + rom_offset)
        patch.write(f_babel2.read())
        f_babel2.close

        # Spirits can warp you back to start
        patch.seek(int("99b69", 16) + rom_offset)
        patch.write(b"\x76\x9B\x76\x9B\x76\x9B\x76\x9B")
        patch.seek(int("99b7a", 16) + rom_offset)
        patch.write(b"\x02\xBE\x02\x01\x80\x9B\x86\x9B\x86\x9B\x16\x9D\x02\xBF\x95\x9C\x6B")
        patch.seek(int("99c1e", 16) + rom_offset)
        patch.write(b"\xd3" + qt_encode("What'd you like to do?") + b"\xcb\xac")
        patch.write(qt_encode("Git gud") + b"\xcb\xac" + qt_encode("Run away!") + b"\xca")
        patch.seek(int("99c95", 16) + rom_offset)
        patch.write(b"\xce" + qt_encode("Darn straight.") + b"\xc0")
        patch.seek(int("99d16", 16) + rom_offset)
        patch.write(b"\x02\x26\xDE\x78\x00\xC0\x00\x00\x00\x11\x02\xC5")

        # Change switch conditions for Crystal Ring item
        patch.seek(int("9999b", 16) + rom_offset)
        patch.write(b"\x4c\xd0\xf6")
        patch.seek(int("9f6d0", 16) + rom_offset)
        patch.write(b"\x02\xd0\xdc\x00\xa0\x99\x02\xd0\x3e\x00\xa0\x99\x02\xd0\xb4\x01\x9a\x99\x4c\xa0\x99")
        patch.seek(int("999aa", 16) + rom_offset)
        patch.write(b"\x4c\xf0\xf6")
        patch.seek(int("9f6f0", 16) + rom_offset)
        patch.write(b"\x02\xd0\xdc\x01\x9a\x99\x4c\xaf\x99")
        patch.seek(int("99a49", 16) + rom_offset)
        patch.write(b"\x02\xbf\xe4\x9a\x02\xd4\x27\x57\x9a\x02\xcc\xdc\x02\xe0" + INV_FULL)
        # Change text
        patch.seek(int("99a70", 16) + rom_offset)
        patch.write(qt_encode("Well, lookie there.", True))

        # Olman event no longer warps you out of the room
        patch.seek(int("98891", 16) + rom_offset)
        patch.write(b"\x02\x0b\x6b")

        # Shorten Olman text boxes, also check for conditions before giving up Statue
        patch.seek(int("9884c", 16) + rom_offset)
        patch.write(b"\x01\x00")
        patch.seek(int("988d2", 16) + rom_offset)
        patch.write(b"\x4c\x30\xf7")
        patch.seek(int("9f730", 16) + rom_offset)
        patch.write(b"\x02\xD1\x79\x01\x01\x42\xF7\x02\xD0\xF6\x01\x42\xF7")
        patch.write(b"\x02\xBF\x4A\xF7\x6B\x02\xBF\x03\x89\x02\xCC\x01\x6B")
        patch.write(qt_encode("heya.|you look frustrated about something.|guess i'm pretty good at my job, huh?", True))
        patch.seek(int("98903", 16) + rom_offset)
        patch.write(qt_encode("heya.", True))
        patch.seek(int("989a2", 16) + rom_offset)
        patch.write(qt_encode("you've been busy, huh?", True))

        # Speed up roof sequence
        patch.seek(int("98fad", 16) + rom_offset)
        patch.write(b"\x02\xcc\x0e\x02\xcc\x0f\x6b")

        # Update "Return to Dao" spirit text
        patch.seek(int("98055", 16) + rom_offset)
        patch.write(qt_encode("I'd tell you my story, but I'd hate to Babylon.|Thank you! I'm here all week!"))
        patch.write(b"\xcb\xac\xd6\x42\xcb\xac")
        patch.write(qt_encode("Go to Dao") + b"\xca")

        # Fun with other text
        patch.seek(int("99866", 16) + rom_offset)
        patch.write(qt_encode("Don't worry, I won't sink my talons TOO far into your back.", True))
        patch.seek(int("9974e", 16) + rom_offset)
        patch.write(qt_encode("Oh yeah, we're not evil anymore... OR AREN'T WE?? >.>", True))
        #patch.write(qt_encode("Oh yeah, we're not evil anymore. Didn't you get the memo?", True))

        ##########################################################################
        #                      Modify Jeweler's Mansion events
        ##########################################################################
        # Set exit warp to Dao
        patch.seek(int("8fcb2", 16) + rom_offset)
        patch.write(b"\x02\x26\xc3\x40\x01\x88\x00\x00\x00\x23")

        # Set flag when Solid Arm is killed
        patch.seek(int("8fa25", 16) + rom_offset)
        patch.write(b"\x4c\x20\xfd")
        patch.seek(int("8fd20", 16) + rom_offset)
        patch.write(b"\x02\xcc\xf6\x02\x26\xe3\x80\x02\xa0\x01\x80\x10\x23\x02\xe0")

        # Solid Arm text
        patch.seek(int("8fa32", 16) + rom_offset)
        patch.write(qt_encode("Weave a circle round him") + b"\xcb" + qt_encode("  thrice,"))
        patch.write(b"\xcb" + qt_encode("And close your eyes with") + b"\xcb" + qt_encode("  holy dread,"))
        patch.write(b"\xcf" + qt_encode("For he on honey-dew hath") + b"\xcb" + qt_encode("  fed,"))
        patch.write(b"\xcb" + qt_encode("And drunk the milk of ") + b"\xcb" + qt_encode("  Paradise.") + b"\xc0")

        patch.seek(int("8fbc9", 16) + rom_offset)
        patch.write(b"\xd5\x02" + qt_encode("Ed, what an ugly thing to say... does this mean we're not friends anymore?|"))
        patch.write(qt_encode("You know, Ed, if I thought you weren't my friend, I just don't think I could bear it.") + b"\xc0")

        ##########################################################################
        #                           Modify Ending cutscene
        ##########################################################################
        # Custom credits
        str_endpause = b"\xC9\xB4\xC8\xCA"
        patch.seek(int("bd566", 16) + rom_offset)
        patch.write(b"\xCB" + qt_encode("    Thanks a million.") + str_endpause)
        patch.seek(int("bd5ac", 16) + rom_offset)
        patch.write(b"\xCB" + qt_encode(" Extra special thanks to") + b"\xCB" + qt_encode("       manafreak"))
        patch.write(b"\xC9\x78\xCE\xCB" + qt_encode(" This project would not") + b"\xCB" + qt_encode("  exist without his work."))
        patch.write(b"\xC9\x78\xCE\xCB" + qt_encode("     gaiathecreator") + b"\xCB" + qt_encode("      .blogspot.com") + str_endpause)
        patch.seek(int("bd71c", 16) + rom_offset)
        patch.write(qt_encode("    Created by") + b"\xCB" + qt_encode("       DontBaguMe") + str_endpause)
        patch.seek(int("bd74f", 16) + rom_offset)
        patch.write(qt_encode("Additional Development By") + b"\xCB" + qt_encode("    bryon w and Raeven0"))
        patch.write(b"\xCB" + qt_encode("  EmoTracker by Apokalysme"))
        patch.write(b"\xC9\x78\xCE\xCB" + qt_encode("   Thanks to all the") + b"\xCB" + qt_encode("  amazing playtesters!") + str_endpause)
        patch.seek(int("bdee2", 16) + rom_offset)
        # patch.write(b"\xCB" + qt_encode("  Thanks RPGLimitBreak!") + str_endpause)
        patch.write(b"\xCB" + qt_encode(" That's it, show's over.") + str_endpause)
        patch.seek(int("bda09", 16) + rom_offset)
        patch.write(b"\xCB" + qt_encode("   Thanks for playing!") + str_endpause)
        patch.seek(int("bdca5", 16) + rom_offset)
        patch.write(qt_encode("Wait a minute...") + b"\xCB" + qt_encode("what happened to Hamlet?") + str_endpause)
        patch.seek(int("bdd48", 16) + rom_offset)
        patch.write(qt_encode("Um...") + b"\xCB" + qt_encode("I wouldn't worry about") + b"\xCB" + qt_encode("that too much...") + str_endpause)
        patch.seek(int("bddf6", 16) + rom_offset)
        patch.write(qt_encode("Well, but...") + str_endpause)
        patch.seek(int("bde16", 16) + rom_offset)
        patch.write(qt_encode("Shh... here,") + b"\xCB" + qt_encode("have some bacon.") + str_endpause)

        # Thank the playtesters
        patch.seek(int("be056", 16) + rom_offset)
        patch.write(b"\x80\xfa")
        patch.seek(int("bfa80", 16) + rom_offset)
        patch.write(b"\xD3\xD2\x00\xD5\x00" + qt_encode("Contributors and Testers:") + b"\xCB")
        patch.write(qt_encode("-Alchemic   -Austin21300") + b"\xCB")
        patch.write(qt_encode("-Atlas      -BOWIEtheHERO") + b"\xCB")
        patch.write(qt_encode("-Bonzaibier -BubbaSWalter") + b"\xC9\xB4\xCE")

        patch.write(qt_encode("-Crazyhaze  -DerTolleIgel") + b"\xCB")
        patch.write(qt_encode("-DoodSF     -djtifaheart") + b"\xCB")
        patch.write(qt_encode("-Eppy37     -Keypaladin") + b"\xCB")
        patch.write(qt_encode("-Lassic") + b"\xC9\xB4\xCE")

        patch.write(qt_encode("-Le Hulk    -Neomatamune") + b"\xCB")
        patch.write(qt_encode("-manafreak  -NYRambler") + b"\xCB")
        patch.write(qt_encode("-Mikan      -Plan") + b"\xCB")
        patch.write(qt_encode("-Mr Freet   -Pozzum Senpai") + b"\xC9\xB4\xCE")

        patch.write(qt_encode("-roeya      -Skipsy") + b"\xCB")
        patch.write(qt_encode("-Scheris    -SmashManiac") + b"\xCB")
        patch.write(qt_encode("-SDiezal    -solarcell007") + b"\xCB")
        patch.write(qt_encode("-Skarsnik   -steve hacks") + b"\xC9\xB4\xCE")

        patch.write(qt_encode("-Sye990     -Verallix") + b"\xCB")
        patch.write(qt_encode("-Tsurana    -Volor") + b"\xCB")
        patch.write(qt_encode("-Tymekeeper -Veetorp") + b"\xC9\xB4\xCE")

        patch.write(qt_encode("-Voranthe   -Xyrcord") + b"\xCB")
        patch.write(qt_encode("-Wilddin    -Z4t0x") + b"\xCB")
        patch.write(qt_encode("-wormsofcan -ZockerStu") + b"\xC9\xB4\xCE")

        patch.write(b"\xCB" + qt_encode("  Thank you all so much!"))
        patch.write(b"\xCB" + qt_encode("     This was so fun!"))

        patch.write(b"\xC9\xF0\xC8\xCA")

        ##########################################################################
        #                           Modify Jeweler event
        ##########################################################################
        # Replace status upgrades with item acquisitions
        f_jeweler = open(BIN_PATH + "08cec9_jeweler.bin", "rb")
        patch.seek(int("8cec9", 16) + rom_offset)
        patch.write(f_jeweler.read())
        f_jeweler.close

        # Allow jeweler to take 2- and 3-jewel items
        # Also, jewel turn-in reduces health in RJM variant
        if settings.red_jewel_madness:
            patch.seek(int("8cf97", 16) + rom_offset)
            patch.write(b"\x4c\xc9\xfd")
            f_jeweler2 = open(BIN_PATH + "08fd80_jeweler2_rjm.bin", "rb")
        else:
            f_jeweler2 = open(BIN_PATH + "08fd80_jeweler2.bin", "rb")
        patch.seek(int("8fd80", 16) + rom_offset)
        patch.write(f_jeweler2.read())
        f_jeweler2.close


        # Jeweler doesn't disappear when defeated
        patch.seek(int("8cea5", 16) + rom_offset)
        patch.write(b"\x10\x00")

        # Jeweler warps you to credits for Red Jewel hunts
        if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            patch.seek(int("8d32a", 16) + rom_offset)
            patch.write(b"\xE5\x00\x00\x00\x00\x00\x00\x11")
            patch.seek(int("8d2d8", 16) + rom_offset)
            patch.write(qt_encode("Beat the game"))

        ##########################################################################
        #                          Update dark space code
        ##########################################################################
        # Allow player to return to South Cape at any time
        # Also, checks for end game state and warps to final boss
        f_darkspace = open(BIN_PATH + "08db07_darkspace.bin", "rb")
        patch.seek(int("8db07", 16) + rom_offset)
        patch.write(f_darkspace.read())
        f_darkspace.close

        # Shorten ability acquisition text
        patch.seek(int("8eb81", 16) + rom_offset)
        patch.write(b"\xc0")

        # Cut out ability explanation text
        patch.seek(int("8eb15", 16) + rom_offset)
        patch.write(b"\xa4\x26\xa9\x00\x00\x99\x24\x00\x02\x04\x16")
        patch.write(b"\x02\xda\x01\xa9\xf0\xff\x1c\x5a\x06\x02\xe0")

        # Remove abilities from all Dark Spaces
        patch.seek(int("c8b34", 16) + rom_offset)  # Itory Village (Psycho Dash)
        patch.write(b"\x01")
        patch.seek(int("c9b49", 16) + rom_offset)  # Diamond Mine (Dark Friar)
        patch.write(b"\x03")
        patch.seek(int("caa99", 16) + rom_offset)  # Mu (Psycho Slide)
        patch.write(b"\x03")
        patch.seek(int("cbb80", 16) + rom_offset)  # Great Wall (Spin Dash)
        patch.write(b"\x03")
        patch.seek(int("cc7b8", 16) + rom_offset)  # Mt. Temple (Aura Barrier)
        patch.write(b"\x03")
        patch.seek(int("cd0a2", 16) + rom_offset)  # Ankor Wat (Earthquaker)
        patch.write(b"\x03")

        # Insert subroutine that can force change back to Will
        f_forcechange = open(BIN_PATH + "08fd30_forcechange.bin", "rb")
        patch.seek(int("8fd30", 16) + rom_offset)
        patch.write(f_forcechange.read())
        f_forcechange.close

        ##########################################################################
        #                          Fix special attacks
        ##########################################################################
        # Earthquaker no longer charges; Aura Barrier can be used w/o Friar
        patch.seek(int("2b871", 16) + rom_offset)
        patch.write(b"\x30")

        # Insert new code to explicitly check for Psycho Dash and Friar
        patch.seek(int("2f090", 16) + rom_offset)
        patch.write(b"\xAD\xA2\x0A\x89\x01\x00\xF0\x06\xA9\xA0\xBE\x20\x26\xB9\x4C\x01\xB9")  # Psycho Dash @2f090
        patch.write(b"\xAD\xA2\x0A\x89\x10\x00\xF0\x06\xA9\x3B\xBB\x20\x26\xB9\x4C\x01\xB9")  # Dark Friar @2f0a1

        # Insert jumps to new code
        patch.seek(int("2b858", 16) + rom_offset)  # Psycho Dash
        patch.write(b"\x4c\x90\xf0")
        patch.seek(int("2b8df", 16) + rom_offset)  # Dark Friar
        patch.write(b"\x4c\xa1\xf0")

        ##########################################################################
        #                      Disable NPCs in various maps
        ##########################################################################
        # School
        patch.seek(int("48d25", 16) + rom_offset)  # Lance
        patch.write(b"\xe0\x6b")
        patch.seek(int("48d72", 16) + rom_offset)  # Seth
        patch.write(b"\xe0\x6b")
        patch.seek(int("48d99", 16) + rom_offset)  # Erik
        patch.write(b"\xe0\x6b")

        # Seaside cave
        patch.seek(int("4afb6", 16) + rom_offset)  # Playing cards
        patch.write(b"\xe0\x6b")
        patch.seek(int("4b06c", 16) + rom_offset)  # Lance
        patch.write(b"\xe0\x6b")
        patch.seek(int("4b459", 16) + rom_offset)  # Seth
        patch.write(b"\xe0\x6b")

        # Edward's Castle
        patch.seek(int("4cb5e", 16) + rom_offset)  # Kara
        patch.write(b"\xe0\x6b")
        patch.seek(int("9bc37", 16) + rom_offset)  # Lilly's flower
        patch.write(b"\x02\xe0\x6b")

        # Itory Village
        patch.seek(int("4e06e", 16) + rom_offset)  # Kara
        patch.write(b"\xe0\x6b")
        patch.seek(int("4f0a7", 16) + rom_offset)  # Lola
        patch.write(b"\xe0\x6b")
        patch.seek(int("4ef78", 16) + rom_offset)  # Bill
        patch.write(b"\xe0\x6b")

        # Lilly's House
        patch.seek(int("4e1b7", 16) + rom_offset)  # Kara
        patch.write(b"\xe0\x6b")

        # Moon Tribe
        # patch.seek(int("4f445",16)+rom_offset)   # Lilly
        # patch.write(b"\xe0\x6b")

        # Inca Ruins Entrance
        patch.seek(int("9ca03", 16) + rom_offset)  # Lilly
        patch.write(b"\xe0\x6b")
        patch.seek(int("9cea7", 16) + rom_offset)  # Kara
        patch.write(b"\xe0\x6b")

        # Diamond Coast
        # patch.seek(int("5aaa2",16)+rom_offset)   # Kara
        # patch.write(b"\xe0\x6b")

        # Freejia Hotel
        patch.seek(int("5c782", 16) + rom_offset)  # Lance
        patch.write(b"\xe0\x6b")
        patch.seek(int("5cb34", 16) + rom_offset)  # Erik
        patch.write(b"\xe0\x6b")
        patch.seek(int("5c5b7", 16) + rom_offset)  # Lilly??
        patch.write(b"\xe0\x6b")
        patch.seek(int("5c45a", 16) + rom_offset)  # Kara??
        patch.write(b"\xe0\x6b")

        # Nazca Plain
        patch.seek(int("5e845", 16) + rom_offset)
        patch.write(b"\xe0\x6b")
        patch.seek(int("5ec8f", 16) + rom_offset)
        patch.write(b"\xe0\x6b")
        patch.seek(int("5eea5", 16) + rom_offset)
        patch.write(b"\xe0\x6b")
        patch.seek(int("5efed", 16) + rom_offset)
        patch.write(b"\xe0\x6b")
        patch.seek(int("5f1fd", 16) + rom_offset)
        patch.write(b"\xe0\x6b")

        # Seaside Palace
        patch.seek(int("68689", 16) + rom_offset)  # Lilly
        patch.write(b"\xe0\x6b")

        # Mu
        patch.seek(int("6a2cc", 16) + rom_offset)  # Erik
        patch.write(b"\xe0\x6b")

        # Watermia
        patch.seek(int("7a871", 16) + rom_offset)  # Lilly
        patch.write(b"\xe0\x6b")

        # Euro
        patch.seek(int("7d989", 16) + rom_offset)  # Kara
        patch.write(b"\xe0\x6b")
        patch.seek(int("7daa1", 16) + rom_offset)  # Erik
        patch.write(b"\xe0\x6b")
        patch.seek(int("7db29", 16) + rom_offset)  # Neil
        patch.write(b"\xe0\x6b")

        # Natives' Village
        # patch.seek(int("8805d",16)+rom_offset)   # Kara
        # patch.write(b"\xe0\x6b")
        # patch.seek(int("8865f",16)+rom_offset)   # Hamlet
        # patch.write(b"\xe0\x6b")
        # patch.seek(int("8854a",16)+rom_offset)   # Erik
        # patch.write(b"\xe0\x6b")

        # Dao
        patch.seek(int("8a4af", 16) + rom_offset)  # Kara
        patch.write(b"\xe0\x6b")
        patch.seek(int("8a56b", 16) + rom_offset)  # Erik
        patch.write(b"\xe0\x6b")
        # patch.seek(int("980cc",16)+rom_offset)   # Spirit
        # patch.write(b"\xe0\x6b")

        # Pyramid
        patch.seek(int("8b7a1", 16) + rom_offset)  # Kara
        patch.write(b"\xe0\x6b")
        patch.seek(int("8b822", 16) + rom_offset)  # Jackal
        patch.write(b"\xe0\x6b")

        # Babel
        patch.seek(int("99e90", 16) + rom_offset)  # Kara 1
        patch.write(b"\xe0\x6b")
        patch.seek(int("98519", 16) + rom_offset)  # Kara 2
        patch.write(b"\xe0\x6b")

        ##########################################################################
        #                Prepare Room/Boss Rewards for Randomization
        ##########################################################################
        # Remove existing rewards
        f_roomrewards = open(BIN_PATH + "01aade_roomrewards.bin", "rb")
        patch.seek(int("1aade", 16) + rom_offset)
        patch.write(f_roomrewards.read())
        f_roomrewards.close

        # Make room-clearing HP rewards grant +3 HP each
        patch.seek(int("e041", 16) + rom_offset)
        patch.write(b"\x03")

        # Make boss rewards also grant +3 HP per unclaimed reward
        patch.seek(int("c381", 16) + rom_offset)
        patch.write(b"\x20\x90\xf4")
        patch.seek(int("f490", 16) + rom_offset)
        patch.write(b"\xee\xca\x0a\xee\xca\x0a\xee\xca\x0a\x60")

        # Change boss room ranges
        patch.seek(int("c31a", 16) + rom_offset)
        patch.write(b"\x67\x5A\x73\x00\x8A\x82\xA8\x00\xDD\xCC\xDD\x00\xF6\xB0\xBF\x00")
        # patch.write(b"\xEA\xB0\xBF\x00")   # If Solid Arm ever grants Babel rewards

        # Add boss reward events to Babel and Jeweler Mansion
        # patch.seek(int("ce3cb",16)+rom_offset)  # Solid Arm
        # patch.write(b"\x00\x01\x01\xDF\xA5\x8B\x00\x00\x01\x01\xBB\xC2\x80\x00\xFF\xCA")
        patch.seek(int("ce536", 16) + rom_offset)  # Mummy Queen (Babel)
        patch.write(b"\x00\x01\x01\xBB\xC2\x80\x00\xFF\xCA")

        # Black Glasses allow you to "see" which upgrades are available
        f_startmenu = open(BIN_PATH + "03fdc0_startmenu.bin", "rb")
        patch.seek(int("3fdc0", 16) + rom_offset)
        patch.write(f_startmenu.read())
        f_startmenu.close
        patch.seek(int("381d6", 16) + rom_offset)
        patch.write(b"\x4C\xC0\xFD")

        # Change start menu "FORCE" text
        patch.seek(int("1ff70", 16) + rom_offset)
        patch.write(b"\x01\xC6\x01\x03\x14\x2D\x33\x48\x50\x00")  # "+3HP"
        patch.seek(int("1ff80", 16) + rom_offset)
        patch.write(b"\x01\xC6\x01\x03\x14\x2D\x31\x53\x54\x52\x00")  # "+1STR"
        patch.seek(int("1ff90", 16) + rom_offset)
        patch.write(b"\x01\xC6\x01\x03\x14\x2D\x31\x44\x45\x46\x00")  # "+1DEF"

        ##########################################################################
        #                        Balance Enemy Stats
        ##########################################################################
        # Determine enemy stats, by difficulty
        if mode == 0:
            f_enemies = open(BIN_PATH + "01abf0_enemieseasy.bin", "rb")
        elif mode == 1:
            f_enemies = open(BIN_PATH + "01abf0_enemiesnormal.bin", "rb")
        elif mode == 2:
            f_enemies = open(BIN_PATH + "01abf0_enemieshard.bin", "rb")
        elif mode == 3:
            f_enemies = open(BIN_PATH + "01abf0_enemiesextreme.bin", "rb")

        if mode < 4:
            patch.seek(int("1abf0", 16) + rom_offset)
            patch.write(f_enemies.read())
            f_enemies.close

        ##########################################################################
        #                            Randomize Inca tile
        ##########################################################################
        # Prepare file for uncompressed map data
        f_incamapblank = open(BIN_PATH + "incamapblank.bin", "rb")
        f_incamap = tempfile.TemporaryFile()
        f_incamap.write(f_incamapblank.read())
        f_incamapblank.close

        # Set random X/Y for new Inca tile
        inca_x = random.randint(0, 11)
        inca_y = random.randint(0, 5)

        # Modify coordinates in event data
        inca_str = format(2 * inca_x + 4, "02x") + format(15 + 2 * inca_y, "02x")
        inca_str = inca_str + format(7 + 2 * inca_x, "02x") + format(18 + 2 * inca_y, "02x")
        patch.seek(int("9c683", 16) + rom_offset)
        patch.write(binascii.unhexlify(inca_str))

        # Remove Wind Melody when door opens
        patch.seek(int("9c660", 16) + rom_offset)
        patch.write(b"\x02\xcd\x12\x01\x02\xd5\x08\x02\xe0")
        patch.seek(int("9c676", 16) + rom_offset)
        patch.write(b"\x67")
        patch.seek(int("9c6a3", 16) + rom_offset)
        patch.write(b"\x02\xd0\x10\x01\x60\xc6")

        # Determine address location for new tile in uncompressed map data
        row = 32 + 2 * inca_y + 16 * int(inca_x / 6)
        column = 2 * ((inca_x + 2) % 8)
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
        f_incamap.close

        # Insert new compressed map data
        # patch.seek(int("1f38db",16)+rom_offset)
        patch.seek(int("1f3ea0", 16) + rom_offset)
        patch.write(b"\x02\x02")
        patch.write(f_incamapcomp.read())
        f_incamapcomp.close

        # Direct map arrangement pointer to new data - NO LONGER NECESSARY
        # patch.seek(int("d8703",16)+rom_offset)
        # patch.write(b"\xa0\x3e")

        ##########################################################################
        #                       Randomize heiroglyph order
        ##########################################################################
        # Determine random order
        hieroglyph_order = [1, 2, 3, 4, 5, 6]
        random.shuffle(hieroglyph_order)

        # Update Father's Journal with correct order
        patch.seek(int("39e9a", 16) + rom_offset)
        for x in hieroglyph_order:
            if x == 1:
                patch.write(b"\xc0\xc1")
            elif x == 2:
                patch.write(b"\xc2\xc3")
            elif x == 3:
                patch.write(b"\xc4\xc5")
            elif x == 4:
                patch.write(b"\xc6\xc7")
            elif x == 5:
                patch.write(b"\xc8\xc9")
            elif x == 6:
                patch.write(b"\xca\xcb")

        # Update RAM switches with correct order (for autotracker)
        h_addrs = ["bfd01","bfd02","bfd07","bfd08","bfd0d","bfd0e"]
        i = 0
        while i < 6:
            patch.seek(int(h_addrs[i], 16) + rom_offset)
            if hieroglyph_order[i] == 1:
                patch.write(b"\x01")
            if hieroglyph_order[i] == 2:
                patch.write(b"\x02")
            if hieroglyph_order[i] == 3:
                patch.write(b"\x03")
            if hieroglyph_order[i] == 4:
                patch.write(b"\x04")
            if hieroglyph_order[i] == 5:
                patch.write(b"\x05")
            if hieroglyph_order[i] == 6:
                patch.write(b"\x06")
            i += 1

        # Update sprite pointers for hieroglyph items, Item 1e is @10803c
        patch.seek(int("10803c", 16) + rom_offset)
        for x in hieroglyph_order:
            if x == 1:
                patch.write(b"\xde\x81")
            if x == 2:
                patch.write(b"\xe4\x81")
            if x == 3:
                patch.write(b"\xea\x81")
            if x == 4:
                patch.write(b"\xf0\x81")
            if x == 5:
                patch.write(b"\xf6\x81")
            if x == 6:
                patch.write(b"\xfc\x81")

        # Update which tiles are called when hieroglyph is placed
        i = 0
        for x in hieroglyph_order:
            patch.seek(int("39b89", 16) + 5 * i + rom_offset)
            if x == 1:
                patch.write(b"\x84")
            elif x == 2:
                patch.write(b"\x85")
            elif x == 3:
                patch.write(b"\x86")
            elif x == 4:
                patch.write(b"\x8c")
            elif x == 5:
                patch.write(b"\x8d")
            elif x == 6:
                patch.write(b"\x8e")
            i += 1

        # Update which tiles are called from placement flags
        patch.seek(int("8cb94", 16) + rom_offset)
        for x in hieroglyph_order:
            if x == 1:
                patch.write(b"\x84")
            elif x == 2:
                patch.write(b"\x85")
            elif x == 3:
                patch.write(b"\x86")
            elif x == 4:
                patch.write(b"\x8c")
            elif x == 5:
                patch.write(b"\x8d")
            elif x == 6:
                patch.write(b"\x8e")

        ##########################################################################
        #                          Randomize Snake Game
        ##########################################################################
        # Randomize snake game duration/goal
        snakes_per_sec = [0.85, 0.85, 1.175, 1.50]         # By difficulty (mode)
        snake_adj = random.uniform(0.9, 1.1)               # Varies snakes per second by +/-10%
        snake_timer = 5 * random.randint(2,12)             # Timer between 10 and 60 sec (inc 5)
        snake_target = int(snake_timer * snakes_per_sec[mode] * snake_adj)

        snake_frames_str = format((60 * snake_timer) % 256, "02x") + format(int((60 * snake_timer) / 256), "02x")
        snake_target_str = format(int(snake_target / 10), "x") + format(snake_target % 10, "x")

        # Update snake game logic with new values
        patch.seek(int("8afe6", 16) + rom_offset)   # Timer, in frames (vanilla b"\x10\x0e")
        patch.write(binascii.unhexlify(snake_frames_str))
        patch.seek(int("8aff7", 16) + rom_offset)   # Snake target BCD (vanilla b"\x51")
        patch.write(binascii.unhexlify(snake_target_str))

        # Update text to reflect changes
        patch.seek(int("8af2e", 16) + rom_offset)
        patch.write(qt_encode("Hit " + str(snake_target) + " snakes in " + str(snake_timer) + " seconds."))
        patch.write(b"\xcb\xac\xac\xac\xac\xac\xac\xac\xac\xac\xac\xac\xac\xac")

        ##########################################################################
        #                    Randomize Jeweler Reward amounts
        ##########################################################################
        # Randomize jeweler reward values
        gem = []
        gem.append(random.randint(1, 3))
        gem.append(random.randint(4, 6))
        gem.append(random.randint(7, 9))
        gem.append(random.randint(10, 14))
        gem.append(random.randint(16, 24))
        gem.append(random.randint(26, 34))
        gem.append(random.randint(36, 50))

        if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            if mode == 0:
                gem[6] = GEMS_EASY
            elif mode == 1:
                gem[6] = GEMS_NORMAL
            elif mode == 2:
                gem[6] = GEMS_HARD
            elif mode == 3:
                gem[6] = GEMS_EXTREME

        gem_str = []

        # Write new values into reward check code (BCD format)
        gem_str.append(format(int(gem[0] / 10), "x") + format(gem[0] % 10, "x"))
        patch.seek(int("8cee0", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[0]))

        gem_str.append(format(int(gem[1] / 10), "x") + format(gem[1] % 10, "x"))
        patch.seek(int("8cef1", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[1]))

        gem_str.append(format(int(gem[2] / 10), "x") + format(gem[2] % 10, "x"))
        patch.seek(int("8cf02", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[2]))

        gem_str.append(format(int(gem[3] / 10), "x") + format(gem[3] % 10, "x"))
        patch.seek(int("8cf13", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[3]))

        gem_str.append(format(int(gem[4] / 10), "x") + format(gem[4] % 10, "x"))
        patch.seek(int("8cf24", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[4]))

        gem_str.append(format(int(gem[5] / 10), "x") + format(gem[5] % 10, "x"))
        patch.seek(int("8cf35", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[5]))

        gem_str.append(format(int(gem[6] / 10), "x") + format(gem[6] % 10, "x"))
        patch.seek(int("8cf40", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[6]))

        # Update RAM switches with correct BCD jewel reward amounts (for autotracker)
        gem_addrs = ["bfd32","bfd37","bfd38","bfd3d","bfd3e","bfd43","bfd44"]
        i = 0
        while i < 7:
            patch.seek(int(gem_addrs[i], 16) + rom_offset)
            patch.write(binascii.unhexlify(gem_str[i]))
            i += 1

        # Write new values into inventory table (Quintet text table format)
        # NOTE: Hard-coded for 1st, 2nd and 3rd rewards each < 10
        gem_str[0] = format(2, "x") + format(gem[0] % 10, "x")
        patch.seek(int("8d26f", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[0]))

        gem_str[1] = format(2, "x") + format(gem[1] % 10, "x")
        patch.seek(int("8d283", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[1]))

        gem_str[2] = format(2, "x") + format(gem[2] % 10, "x")
        patch.seek(int("8d297", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[2]))

        gem_str[3] = format(2, "x") + format(int(gem[3] / 10), "x")
        gem_str[3] = gem_str[3] + format(2, "x") + format(gem[3] % 10, "x")
        patch.seek(int("8d2aa", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[3]))

        gem_str[4] = format(2, "x") + format(int(gem[4] / 10), "x")
        gem_str[4] = gem_str[4] + format(2, "x") + format(gem[4] % 10, "x")
        patch.seek(int("8d2be", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[4]))

        gem_str[5] = format(2, "x") + format(int(gem[5] / 10), "x")
        gem_str[5] = gem_str[5] + format(2, "x") + format(gem[5] % 10, "x")
        patch.seek(int("8d2d2", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[5]))

        gem_str[6] = format(2, "x") + format(int(gem[6] / 10), "x")
        gem_str[6] = gem_str[6] + format(2, "x") + format(gem[6] % 10, "x")
        patch.seek(int("8d2e6", 16) + rom_offset)
        patch.write(binascii.unhexlify(gem_str[6]))

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
                patch.seek(int("8dd19", 16) + rom_offset)
                patch.write(b"\xf8")

                # Put statue requirements into RAM (for autotracker)
                patch.seek(int("bfd1a", 16) + rom_offset)
                patch.write(b"\xf8\x02")

            if statueOrder[i] == 2:
                statues.append(2)
                statues_hex.append(b"\x22")

                # Check for Mystic Statue possession at end game state
                patch.seek(int("8dd1f", 16) + rom_offset)
                patch.write(b"\xf9")

                # Put statue requirements into RAM (for autotracker)
                patch.seek(int("bfd1e", 16) + rom_offset)
                patch.write(b"\xf9\x02")

            if statueOrder[i] == 3:
                statues.append(3)
                statues_hex.append(b"\x23")

                # Check for Mystic Statue possession at end game state
                patch.seek(int("8dd25", 16) + rom_offset)
                patch.write(b"\xfa")

                # Put statue requirements into RAM (for autotracker)
                patch.seek(int("bfd22", 16) + rom_offset)
                patch.write(b"\xfa\x02")

                # Restrict removal of Rama Statues from inventory
                patch.seek(int("1e12c", 16) + rom_offset)
                patch.write(b"\x9f")

            if statueOrder[i] == 4:
                statues.append(4)
                statues_hex.append(b"\x24")

                # Check for Mystic Statue possession at end game state
                patch.seek(int("8dd2b", 16) + rom_offset)
                patch.write(b"\xfb")

                # Put statue requirements into RAM (for autotracker)
                patch.seek(int("bfd26", 16) + rom_offset)
                patch.write(b"\xfb\x02")

            if statueOrder[i] == 5:
                statues.append(5)
                statues_hex.append(b"\x25")

                # Check for Mystic Statue possession at end game state
                patch.seek(int("8dd31", 16) + rom_offset)
                patch.write(b"\xfc")

                # Put statue requirements into RAM (for autotracker)
                patch.seek(int("bfd2a", 16) + rom_offset)
                patch.write(b"\xfc\x02")

                # Restrict removal of Hieroglyphs from inventory
                patch.seek(int("1e12d", 16) + rom_offset)
                patch.write(b"\xf7\xff")

            if statueOrder[i] == 6:
                statues.append(6)
                statues_hex.append(b"\x26")

                # Check for Mystic Statue possession at end game state
                patch.seek(int("8dd37", 16) + rom_offset)
                patch.write(b"\xfd")

                # Put statue requirements into RAM (for autotracker)
                patch.seek(int("bfd2e", 16) + rom_offset)
                patch.write(b"\xfd\x02")

            i += 1

        # Can't face Dark Gaia in Red Jewel hunts
        if settings.goal.value != Goal.DARK_GAIA.value:
            patch.seek(int("8dd0d", 16) + rom_offset)
            patch.write(b"\x10\x01")

        statues.sort()
        statues_hex.sort()

        # Teacher at start spoils required Mystic Statues
        statue_str = ""
        if len(statues_hex) == 0:
            statue_str = b"\xd3\x4d\x8e\xac\xd6\xd2\x80\xa2\x84\xac"
            statue_str += b"\xa2\x84\xa1\xa5\x88\xa2\x84\x83\x4f\xc0"

        else:
            statue_str = b"\xd3\x69\x8e\xa5\xac\x8d\x84\x84\x83\xac"
            statue_str += b"\x4c\xa9\xa3\xa4\x88\x82\xac\x63\xa4\x80\xa4\xa5\x84"
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

        patch.seek(int("48aab", 16) + rom_offset)
        patch.write(statue_str)

        ##########################################################################
        #                           Determine Boss Order
        ##########################################################################
        boss_order = [1,2,3,4,5,6,7]
        if settings.boss_shuffle:
            # Determine statue order for shuffle
            if mode == 3:
                random.shuffle(boss_order)
            else:
                boss_order.remove(5)
                boss_order.remove(7)
                random.shuffle(boss_order)
                non_will_dungeons = [0,1,2,4]
                random.shuffle(non_will_dungeons)
                boss_order.insert(non_will_dungeons[0],5)
                boss_order += [7]

            # Define music map headers
            dungeon_music = [b"\x11\x07\x00\x0f\x67\xd4"]       # Inca Ruins
            dungeon_music.append(b"\x11\x08\x00\xda\x71\xd3")   # Sky Garden
            dungeon_music.append(b"\x11\x09\x00\x00\x00\xd2")   # Mu
            dungeon_music.append(b"\x11\x0a\x00\x17\x30\xd4")   # Great Wall
            dungeon_music.append(b"\x11\x0c\x00\xa0\x71\xd0")   # Pyramid
            dungeon_music.append(b"\x11\x06\x00\x90\x42\xd4")   # Babel
            dungeon_music.append(b"\x11\x06\x00\x90\x42\xd4")   # Mansion

            # Find all music header locations in map data file
            music_header_addrs = [[],[],[],[],[]]
            i = 0
            while i < 5:
                done = False
                addr = 0
                while not done:
                    f_mapdata.seek(0)
                    addr = f_mapdata.read().find(dungeon_music[i], addr + 1)
                    if addr < 0:
                        done = True
                    else:
                        music_header_addrs[i].append(addr)
                i += 1

            # Patch music headers into new dungeons (easy and normal modes)
            if mode <= 1:
                i = 0
                while i < 5:
                    boss = boss_order[i]
                    while music_header_addrs[i]:
                        addr = music_header_addrs[i].pop(0)
                        f_mapdata.seek(addr)
                        f_mapdata.write(dungeon_music[boss-1])
                    i += 1

                # Special case for Mansion
                f_mapdata.seek(0)
                addr = 27 + f_mapdata.read().find(b"\x00\xE9\x00\x02\x22")
                if addr < 27:
                    print("ERROR: Couldn't find Mansion map header")
                else:
                    f_mapdata.seek(addr)
                    f_mapdata.write(dungeon_music[boss_order[6]-1])

        # Change conditions and text for Pyramid boss portal
        pyramid_boss = boss_order[4]
        patch.seek(int("8cd71", 16) + rom_offset)
        if pyramid_boss == 5:
            patch.write(b"\xfc")
        elif pyramid_boss == 7:
            patch.write(b"\xf6")
        else:
            patch.write(b"\x10\x00")

        # Change "Return to Dao" Babel spirit text
        babel_boss = boss_order[5]
        patch.seek(int("980a6", 16) + rom_offset)
        if babel_boss == 1:
            patch.write(b"\x42\x8e\x80\xa3\xa4\xca")
        elif babel_boss == 2:
            patch.write(b"\x63\x84\x80\xac\x60\x80\x8b\x80\x82\x84\xca")
        elif babel_boss == 3:
            patch.write(b"\x4c\xa5\xca")
        elif babel_boss == 4:
            patch.write(b"\xd6\x16\x67\x80\x8b\x8b\xca")
        elif babel_boss == 5:
            patch.write(b"\xd6\x3f\xca")

        patch.seek(int("8cddb", 16) + rom_offset)
        patch.write(b"\x47\x84\x84\x84\x84\x84\x84\x84\x84\x84\x84\x84\x84\x84\x84\xa2\x84\x0e\xa3\xac\xcb")
        if pyramid_boss == 1:
            patch.write(b"\x42\x80\xa3\xa4\x8e\xa4\x87\x4f\xac\xac\xac\xac\xac\xac\xac\xac")
        elif pyramid_boss == 2:
            patch.write(b"\x66\x88\xa0\x84\xa2\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac\xac")
        elif pyramid_boss == 3:
            patch.write(b"\x66\x80\x8c\xa0\x88\xa2\x84\xa3\x4f\xac\xac\xac\xac\xac\xac\xac")
        elif pyramid_boss == 4:
            patch.write(b"\x63\x80\x8d\x83\xac\x45\x80\x8d\x86\x84\xa2\x4f\xac\xac\xac\xac")
        elif pyramid_boss == 5:
            patch.write(b"\x4c\xa5\x8c\x8c\xa9\xac\x61\xa5\x84\x84\x8d\x4f\xac\xac\xac\xac")
        elif pyramid_boss == 6:
            patch.write(b"\x4c\xa5\x8c\x8c\xa9\xac\x61\xa5\x84\x84\x8d\xac\x22\x2a\x20\x4f")
        elif pyramid_boss == 7:
            patch.write(b"\x63\x8e\x8b\x88\x83\xac\x40\xa2\x8c\x4f\xac\xac\xac\xac\xac\xac")

        # Update item removal restrictions based on required dungeons
        if boss_order[2] in statues:
            # Restrict removal of Rama Statues from inventory
            patch.seek(int("1e12c", 16) + rom_offset)
            patch.write(b"\x9f")
        if boss_order[4] in statues:
            # Restrict removal of Hieroglyphs from inventory
            patch.seek(int("1e12d", 16) + rom_offset)
            patch.write(b"\xf7\xff")

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
        patch.seek(int("6d153", 16) + rom_offset)
        patch.write(b"\x8a")
        patch.seek(int("6d169", 16) + rom_offset)
        patch.write(b"\x02\xd2\x8a\x01\x02\xe0")
        patch.seek(int("6d25c", 16) + rom_offset)
        patch.write(b"\x8a")
        patch.seek(int("6d27e", 16) + rom_offset)
        patch.write(qt_encode("Hurry boy, she's waiting there for you!") + b"\xc0")
        patch.seek(int("6d305", 16) + rom_offset)
        patch.write(qt_encode("Kara's portrait. If only you had Magic Dust...") + b"\xc0")

        if kara_location == KARA_ANGEL:
            # Set spoiler for Kara's location in Lance's Letter
            patch.seek(int("39521", 16) + rom_offset)
            patch.write(b"\x40\x8d\x86\x84\x8b\xac\x66\x88\x8b\x8b\x80\x86\x84")

        else:
            # Remove Kara's painting from Ishtar's Studio
            patch.seek(int("cb397", 16) + rom_offset)
            patch.write(b"\x18")

            if kara_location == KARA_EDWARDS:  # Underground tunnel exit, map 19 (0x13)
                # Set spoiler for Kara's location in Lance's Letter
                patch.seek(int("39521", 16) + rom_offset)
                patch.write(b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x60\xa2\x88\xa3\x8e\x8d")

                # Set Kara's location in RAM switches (for autotracker)
                patch.seek(int("bfd13", 16) + rom_offset)
                patch.write(b"\x01")

                # Set map check ID for Magic Dust item event
                patch.seek(int("393a9", 16) + rom_offset)
                patch.write(b"\x13\x00\xD0\x08\x02\x45\x0b\x0b\x0d\x0d")

                # Set Kara painting event in appropriate map
                patch.seek(int("c8ac5", 16) + rom_offset)
                patch.write(b"\x0b\x0b\x00\x4e\xd1\x86\xff\xca")  # this is correct

                # Adjust sprite palette
                patch.seek(int("6d15b", 16) + rom_offset)
                patch.write(b"\x02\xb6\x30")

            elif kara_location == KARA_MINE:
                # Set spoiler for Kara's location in Lance's Letter
                patch.seek(int("39521", 16) + rom_offset)
                patch.write(b"\x43\x88\x80\x8c\x8e\x8d\x83\xac\x4c\x88\x8d\x84")

                # Set Kara's location in RAM switches (for autotracker)
                patch.seek(int("bfd13", 16) + rom_offset)
                patch.write(b"\x02")

                # Set map check ID for Magic Dust item event
                patch.seek(int("393a9", 16) + rom_offset)
                patch.write(b"\x47\x00\xD0\x08\x02\x45\x0b\x24\x0d\x26")

                # Change "Sam" to "Samlet"
                patch.seek(int("5fee0", 16) + rom_offset)
                patch.write(b"\x1a\x00\x10\x02\xc0\x9e\xd2\x02\x0b\x02\xc1\x6b")
                patch.seek(int("5d2bd", 16) + rom_offset)
                patch.write(b"\xf0\xd2")
                patch.seek(int("5d2f0", 16) + rom_offset)
                patch.write(b"\xd3\xc2\x05" + qt_encode("Samlet: I'll never forget you!") + b"\xc0")
                patch.seek(int("c9c78", 16) + rom_offset)
                patch.write(b"\x03\x2a\x00\xe0\xfe\x85")

                # Disable Remus
                patch.seek(int("5d15e", 16) + rom_offset)
                patch.write(b"\xe0")

                # Assign Kara painting spriteset to appropriate Map
                f_mapdata.seek(0)
                addr = f_mapdata.read().find(b"\x15\x0C\x00\x49\x00\x02")
                if addr < 0:
                    self.logger.error("ERROR: Could not change spriteset for Diamond Mine")
                else:
                    f_mapdata.seek(addr)
                    f_mapdata.write(b"\x15\x25")

                # Set Kara painting event in appropriate map
                patch.seek(int("c9c6a", 16) + rom_offset)
                patch.write(b"\x0b\x24\x00\x4e\xd1\x86")

                # Adjust sprite
                # patch.seek(int("6d14e",16)+rom_offset)
                # patch.write(b"\x2a")
                patch.seek(int("6d15b", 16) + rom_offset)
                patch.write(b"\x02\xb6\x30")

            elif kara_location == KARA_KRESS:

                # Set spoiler for Kara's location in Lance's Letter
                patch.seek(int("39521", 16) + rom_offset)
                patch.write(b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3")

                # Set Kara's location in RAM switches (for autotracker)
                patch.seek(int("bfd13", 16) + rom_offset)
                patch.write(b"\x04")

                # Set map check ID for Magic Dust item event
                patch.seek(int("393a9", 16) + rom_offset)
                patch.write(b"\xa9\x00\xD0\x08\x02\x45\x12\x06\x14\x08")

                # Set Kara painting event in appropriate map
                # Map #169, written into unused Map #104 (Seaside Tunnel)
                patch.seek(int("c8152", 16) + rom_offset)
                patch.write(b"\x42\xad")
                patch.seek(int("cad42", 16) + rom_offset)
                patch.write(b"\x05\x0a\x00\x8c\xc3\x82\x00\x00\x00\x00\xed\xea\x80\x00\xdf")
                patch.write(b"\xdf\x00\x4d\xe9\x80\x00\x12\x06\x00\x4e\xd1\x86\x00\xff\xca")

                # Adjust sprite
                patch.seek(int("6d15b", 16) + rom_offset)
                patch.write(b"\x02\xb6\x30")

            elif kara_location == KARA_ANKORWAT:
                # Set spoiler for Kara's location in Lance's Letter
                patch.seek(int("39521", 16) + rom_offset)
                patch.write(b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4")

                # Set Kara's location in RAM switches (for autotracker)
                patch.seek(int("bfd13", 16) + rom_offset)
                patch.write(b"\x05")

                # Set map check ID for Magic Dust item event
                patch.seek(int("393a9", 16) + rom_offset)
                patch.write(b"\xbf\x00\xD0\x08\x02\x45\x1a\x10\x1c\x12")

                # Set Kara painting event in appropriate map (Map #191)
                # Map #191, written into unused Map #104 (Seaside Tunnel)
                patch.seek(int("c817e", 16) + rom_offset)
                patch.write(b"\x42\xad")
                patch.seek(int("cad42", 16) + rom_offset)
                patch.write(b"\x05\x0a\x02\x8c\xc3\x82\x00\x00\x00\x00\xed\xea\x80\x00\x0f")
                patch.write(b"\x0b\x00\xa3\x9a\x88\x00\x1a\x10\x00\x4e\xd1\x86\x00\xff\xca")

                # Adjust sprite
                patch.seek(int("6d15b", 16) + rom_offset)
                patch.write(b"\x02\xb6\x30")

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
        if mode == 3:
            death_list.append(b"\x2d\x46\x88\xa4\xac\x86\xa5\x83\xac\xa3\x82\xa2\xa5\x81\x2a\x2e\xcb\xac\xac\x6d\x41\x80\x86\xa5\xc0")

        # Will death text
        patch.seek(int("d7c3", 16) + rom_offset)
        patch.write(death_list[random.randint(0, len(death_list) - 1)])
        # patch.write(death_list[0])

        # Change Fredan and Shadow death pointers
        patch.seek(int("d7b2", 16) + rom_offset)
        patch.write(b"\xc2\xd7")
        patch.seek(int("d7b8", 16) + rom_offset)
        patch.write(b"\xc2\xd7")

        ##########################################################################
        #                          Have fun with final text
        ##########################################################################
        superhero_list = []
        superhero_list.append(qt_encode("I must go, my people need me!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("     Up, up, and away!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       Up and atom!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("  It's clobberin' time!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       For Asgard!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("    Back in a flash!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("      I am GROOT!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("Wonder Twin powers activate!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("    Titans together!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       HULK SMASH!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("        Flame on!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("    I have the power!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("        Shazam!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("     Bite me, fanboy.") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("  Hi-yo Silver... away!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("Here I come to save the day!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("    Teen Titans, Go!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       Cowabunga!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       SPOOOOON!!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("There better be bacon when I get there...") + b"\xc3\x00\xc0")

        # Assign final text box
        patch.seek(int("98ebe", 16) + rom_offset)
        patch.write(superhero_list[random.randint(0, len(superhero_list) - 1)])

        ##########################################################################
        #                   Randomize item and ability placement
        ##########################################################################
        done = False
        seed_adj = 0
        self.w = World(settings, statues, kara_location, gem, [inca_x + 1, inca_y + 1], hieroglyph_order, boss_order)
        while not done:
            if seed_adj > 10:
                self.logger.error("ERROR: Max number of seed adjustments exceeded")
                raise RecursionError
            self.w = World(settings, statues, kara_location, gem, [inca_x + 1, inca_y + 1], hieroglyph_order, boss_order)
            done = self.w.randomize(seed_adj)
            seed_adj += 1

        self.w.generate_spoiler(VERSION)
        self.w.write_to_rom(patch, rom_offset)

        ##########################################################################
        #                   Update map dataset after Enemizer
        ##########################################################################
        for map_patch in self.w.map_patches:
            f_mapdata.seek(0)
            addr = f_mapdata.read().find(map_patch[0])
            if addr < 0:
                print("ERROR: Couldn't find header: ", binascii.hexlify(map_patch[0]))
            else:
                f_mapdata.seek(addr + map_patch[2])
                f_mapdata.write(map_patch[1])

        ##########################################################################
        #                        Randomize Ishtar puzzle
        ##########################################################################
        # Add checks for Will's hair in each room
        patch.seek(int("6dc53", 16) + rom_offset)
        patch.write(b"\x4c\x00\xdd\x86")
        patch.seek(int("6dd00", 16) + rom_offset)
        patch.write(b"\x02\x45\x10\x00\x20\x10\x66\xdc\x02\x45\x30\x00\x40\x10\x66\xDC")
        patch.write(b"\x02\x45\x50\x00\x60\x10\x66\xdc\x02\x45\x70\x00\x80\x10\x66\xDC")
        patch.write(b"\x4c\x66\xdc\x86")

        # Generalize success text boxes
        # Make Rooms 1 and 3 equal to Room 2 text (which is already general)
        patch.seek(int("6d978", 16) + rom_offset)  # Room 1
        patch.write(b"\x2c\xdb")
        patch.seek(int("6d9ce", 16) + rom_offset)  # Room 3
        patch.write(b"\x2c\xdb")
        # Generalize Room 4 text
        patch.seek(int("6d9f8", 16) + rom_offset)
        patch.write(b"\xc6\xdb")
        patch.seek(int("6dbc6", 16) + rom_offset)
        patch.write(b"\xc2\x0a")

        # Create temporary map file
        f_ishtarmapblank = open(BIN_PATH + "ishtarmapblank.bin", "rb")
        f_ishtarmap = tempfile.TemporaryFile()
        f_ishtarmap.write(f_ishtarmapblank.read())
        f_ishtarmapblank.close()

        room_offsets = ["6d95e", "6d98a", "6d9b4", "6d9de"]  # ROM addrs for cursor capture, by room
        coord_offsets = [3, 8, 15, 20]  # Offsets for xmin, xmax, ymin, ymax
        changes = [random.randint(1, 8), random.randint(1, 7), random.randint(1, 5), random.randint(1, 7)]

        # Set change for Room 1
        if changes[0] == 1:  # Change right vase to light (vanilla)
            f_ishtarmap.seek(int("17b", 16))
            f_ishtarmap.write(b"\x7b")
            f_ishtarmap.seek(int("18b", 16))
            f_ishtarmap.write(b"\x84")
            coords = [b"\xB0\x01", b"\xC0\x01", b"\x70\x00", b"\x90\x00"]

        elif changes[0] == 2:  # Change middle vase to light
            f_ishtarmap.seek(int("175", 16))
            f_ishtarmap.write(b"\x7b")
            f_ishtarmap.seek(int("185", 16))
            f_ishtarmap.write(b"\x84")
            coords = [b"\x50\x01", b"\x60\x01", b"\x70\x00", b"\x90\x00"]

        elif changes[0] == 3:  # Change left vase to dark
            f_ishtarmap.seek(int("174", 16))
            f_ishtarmap.write(b"\x83")
            f_ishtarmap.seek(int("184", 16))
            f_ishtarmap.write(b"\x87")
            coords = [b"\x40\x01", b"\x50\x01", b"\x70\x00", b"\x90\x00"]

        elif changes[0] == 4:  # Change left shelf to empty
            f_ishtarmap.seek(int("165", 16))
            f_ishtarmap.write(b"\x74")
            coords = [b"\x50\x01", b"\x60\x01", b"\x58\x00", b"\x70\x00"]

        elif changes[0] == 5:  # Change left shelf to books
            f_ishtarmap.seek(int("165", 16))
            f_ishtarmap.write(b"\x76")
            coords = [b"\x50\x01", b"\x60\x01", b"\x58\x00", b"\x70\x00"]

        elif changes[0] == 6:  # Change right shelf to jar
            f_ishtarmap.seek(int("166", 16))
            f_ishtarmap.write(b"\x75")
            coords = [b"\x60\x01", b"\x70\x01", b"\x58\x00", b"\x70\x00"]

        elif changes[0] == 7:  # Change right shelf to empty
            f_ishtarmap.seek(int("166", 16))
            f_ishtarmap.write(b"\x74")
            coords = [b"\x60\x01", b"\x70\x01", b"\x58\x00", b"\x70\x00"]

        elif changes[0] == 8:  # Will's hair
            patch.seek(int("6dd06", 16) + rom_offset)
            patch.write(b"\x5d")
            coords = [b"\xa0\x01", b"\xc0\x01", b"\xb0\x00", b"\xd0\x00"]

        # Update cursor check ranges for Room 1
        for i in range(4):
            patch.seek(int(room_offsets[0], 16) + coord_offsets[i] + rom_offset)
            patch.write(coords[i])

        # Set change for Room 2
        if changes[1] == 1:  # Change both pots to dark (vanilla)
            f_ishtarmap.seek(int("3a3", 16))
            f_ishtarmap.write(b"\x7c\x7c")
            f_ishtarmap.seek(int("3b3", 16))
            f_ishtarmap.write(b"\x84\x84")
            coords = [b"\x30\x03", b"\x50\x03", b"\xa0\x00", b"\xc0\x00"]

        elif changes[1] == 2:  # Remove rock
            f_ishtarmap.seek(int("3bd", 16))
            f_ishtarmap.write(b"\x73")
            coords = [b"\xd0\x03", b"\xe0\x03", b"\xb0\x00", b"\xc0\x00"]

        elif changes[1] == 3:  # Add round table
            f_ishtarmap.seek(int("395", 16))
            f_ishtarmap.write(b"\x7d\x7e")
            f_ishtarmap.seek(int("3a5", 16))
            f_ishtarmap.write(b"\x85\x86")
            f_ishtarmap.seek(int("3b5", 16))
            f_ishtarmap.write(b"\x8d\x8e")
            coords = [b"\x50\x03", b"\x70\x03", b"\x90\x00", b"\xb0\x00"]

        elif changes[1] == 4:  # Add sconce
            f_ishtarmap.seek(int("357", 16))
            f_ishtarmap.write(b"\x88\x89")
            f_ishtarmap.seek(int("367", 16))
            f_ishtarmap.write(b"\x90\x91")
            coords = [b"\x70\x03", b"\x90\x03", b"\x50\x00", b"\x70\x00"]

        elif changes[1] == 5:  # Add rock
            f_ishtarmap.seek(int("3b2", 16))
            f_ishtarmap.write(b"\x77")
            coords = [b"\x20\x03", b"\x30\x03", b"\xb0\x00", b"\xc0\x00"]

        elif changes[1] == 6:  # Will's hair
            patch.seek(int("6dd0e", 16) + rom_offset)
            patch.write(b"\x5d")
            coords = [b"\x90\x03", b"\xb0\x03", b"\xa0\x00", b"\xc0\x00"]

        elif changes[1] == 7:  # Put moss on rock
            f_ishtarmap.seek(int("3bd", 16))
            f_ishtarmap.write(b"\x8f")
            coords = [b"\xd0\x03", b"\xe0\x03", b"\xb0\x00", b"\xc0\x00"]

        # Update cursor check ranges for Room 2
        for i in range(4):
            patch.seek(int(room_offsets[1], 16) + coord_offsets[i] + rom_offset)
            patch.write(coords[i])

        # Set change for Room 3
        # Check for chest contents, only change map if contents are the same
        if self.w.item_locations[80][3] == self.w.item_locations[81][3]:
            if changes[2] == 1:  # Remove rock
                f_ishtarmap.seek(int("5bd", 16))
                f_ishtarmap.write(b"\x73")
                coords = [b"\xd0\x05", b"\xe0\x05", b"\xb0\x00", b"\xc0\x00"]

            elif changes[2] == 2:  # Add rock
                f_ishtarmap.seek(int("5b2", 16))
                f_ishtarmap.write(b"\x77")
                coords = [b"\x20\x05", b"\x30\x05", b"\xb0\x00", b"\xc0\x00"]

            elif changes[2] == 3:  # Add sconce
                f_ishtarmap.seek(int("557", 16))
                f_ishtarmap.write(b"\x88\x89")
                f_ishtarmap.seek(int("567", 16))
                f_ishtarmap.write(b"\x90\x91")
                coords = [b"\x70\x05", b"\x90\x05", b"\x50\x00", b"\x70\x00"]

            elif changes[2] == 4:  # Will's hair
                patch.seek(int("6dd16", 16) + rom_offset)
                patch.write(b"\x5d")
                coords = [b"\x90\x05", b"\xb0\x05", b"\xa0\x00", b"\xc0\x00"]

            if changes[2] == 5:  # Moss rock
                f_ishtarmap.seek(int("5bd", 16))
                f_ishtarmap.write(b"\x8f")
                coords = [b"\xd0\x05", b"\xe0\x05", b"\xb0\x00", b"\xc0\x00"]

            # Update cursor check ranges for Room 3 (only if chest contents different)
            for i in range(4):
                patch.seek(int(room_offsets[2], 16) + coord_offsets[i] + rom_offset)
                patch.write(coords[i])

        # Set change for Room 4
        if changes[3] == 1:  # Will's hair (vanilla)
            patch.seek(int("6dd1e", 16) + rom_offset)
            patch.write(b"\x5d")

        else:
            if changes[3] == 2:  # Remove rock
                f_ishtarmap.seek(int("7bd", 16))
                f_ishtarmap.write(b"\x73")
                coords = [b"\xd0\x07", b"\xe0\x07", b"\xb0\x00", b"\xc0\x00"]

            elif changes[3] == 3:  # Add rock
                f_ishtarmap.seek(int("7b2", 16))
                f_ishtarmap.write(b"\x77")
                coords = [b"\x20\x07", b"\x30\x07", b"\xb0\x00", b"\xc0\x00"]

            elif changes[3] == 4:  # Add vase L
                f_ishtarmap.seek(int("7a3", 16))
                f_ishtarmap.write(b"\x7c")
                f_ishtarmap.seek(int("7b3", 16))
                f_ishtarmap.write(b"\x84")
                coords = [b"\x30\x07", b"\x40\x07", b"\xa0\x00", b"\xc0\x00"]

            elif changes[3] == 5:  # Add vase R
                f_ishtarmap.seek(int("7ac", 16))
                f_ishtarmap.write(b"\x7c")
                f_ishtarmap.seek(int("7bc", 16))
                f_ishtarmap.write(b"\x84")
                coords = [b"\xc0\x07", b"\xd0\x07", b"\xa0\x00", b"\xc0\x00"]

            elif changes[3] == 6:  # Crease in floor
                f_ishtarmap.seek(int("7b4", 16))
                f_ishtarmap.write(b"\x69\x6a")
                coords = [b"\x40\x07", b"\x60\x07", b"\xb0\x00", b"\xc8\x00"]

            if changes[3] == 7:  # Moss rock
                f_ishtarmap.seek(int("7bd", 16))
                f_ishtarmap.write(b"\x8f")
                coords = [b"\xd0\x07", b"\xe0\x07", b"\xb0\x00", b"\xc0\x00"]

            # Update cursor check ranges for Room 3 (only if not hair)
            for i in range(4):
                patch.seek(int(room_offsets[3], 16) + coord_offsets[i] + rom_offset)
                patch.write(coords[i])

        # Compress map data and write to file
        f_ishtarmapcomp = tempfile.TemporaryFile()
        f_ishtarmap.seek(0)
        f_ishtarmapcomp.write(qt_compress(f_ishtarmap.read()))
        f_ishtarmapcomp.seek(0)
        f_ishtarmap.close()

        # Insert new compressed map data
        # patch.seek(int("193d25",16)+rom_offset)
        patch.seek(int("1f4100", 16) + rom_offset)
        patch.write(b"\x08\x02")
        patch.write(f_ishtarmapcomp.read())
        f_ishtarmapcomp.close()

        # Direct map arrangement pointer to new data - NO LONGER NECESSARY
        # patch.seek(int("d977e",16)+rom_offset)
        # patch.write(b"\x00\x41")

        ##########################################################################
        #                Finalize map headers and return patch data
        ##########################################################################
        f_mapdata.seek(0)
        patch.seek(int("d8000", 16) + rom_offset)
        patch.write(f_mapdata.read())

        return json.dumps(patch.patch_data)

    def generate_spoiler(self) -> str:
        return json.dumps(self.w.spoiler)

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
