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
from .models.enums.enemizer import Enemizer
from .models.enums.start_location import StartLocation

VERSION = "4.4.9"

MAX_RANDO_RETRIES = 9
PRINT_LOG = False

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

FORCE_CHANGE = b"\x22\x30\xfd\x88"
CLEAR_ENEMIES = b"\x22\x9B\xFF\x81"

OUTPUT_FOLDER: str = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + ".." + os.path.sep + ".." + os.path.sep + "data" + os.path.sep + "output" + os.path.sep
BIN_PATH: str = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + "bin" + os.path.sep
AG_PLUGIN_PATH: str = BIN_PATH + "plugins" + os.path.sep + "AG" + os.path.sep


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
        patch = self.__generate_patch__()
        rom_offset = self.__get_offset__(patch)

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

        # todo: pass hash_len in as !RandoTitleScreenHashScreen
        

        ##########################################################################
        #                            Update item events
        #    Adds new items that increase HP, DEF, STR and improve abilities
        ##########################################################################
        #patch.seek(int("3944e", 16) + rom_offset)
        #patch.write(b"\xce" + qt_encode("       Welcome to") + b"\xcb\xcb" + qt_encode("  Bagu's Super-Helpful"))
        #patch.write(b"\xcb" + qt_encode("  In-Game Tutorial!(TM)|"))
        #patch.write(qt_encode("Whadaya wanna know about?") + b"\xcb" + qt_encode(" Beating the Game") + b"\xcb")
        #patch.write(qt_encode(" Exploring the World") + b"\xcb" + qt_encode(" What If I'm Stuck?") + b"\xca")
        #
        #patch.seek(int("394f0", 16) + rom_offset)
        #patch.write(b"\xce" + qt_encode("He closed the journal.") + b"\xc0")
        #
        #patch.seek(int("3f210", 16) + rom_offset)
        #if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
        #    patch.write(b"\xce" + qt_encode("BEATING THE GAME:       It's a Red Jewel hunt! The objective is super simple:|"))
        #    patch.write(qt_encode("Find the Red Jewels you need, and talk to the Jeweler. That's it!|"))
        #    patch.write(qt_encode("Check the Jeweler's inventory to find out how many Red Jewels you need to beat the game.|"))
        #    patch.write(qt_encode("Happy hunting!") + b"\xc0")
        #else:
        #    patch.write(b"\xce" + qt_encode("BEATING THE GAME:       You must do three things to beat the game:|"))
        #    patch.write(qt_encode("1. RESCUE KARA         Kara is trapped in a painting! You need Magic Dust to free her.|"))
        #    patch.write(qt_encode("She can be in either Edward's Prison, Diamond Mine, Angel Village, Mt. Temple, or Ankor Wat.|"))
        #    patch.write(qt_encode("You can search for her yourself or find Lance's Letter to learn where she is.|"))
        #    patch.write(qt_encode("Once you find Kara, use the Magic Dust on her portrait to free her.|"))
        #    patch.write(qt_encode("2. FIND/USE THE AURA  Using the Aura unlocks Shadow, the form you need to fight Dark Gaia.|"))
        #    patch.write(qt_encode("3. GATHER MYSTIC STATUES You may be required to gather Mystic Statues.|"))
        #    patch.write(qt_encode("The teacher in the South Cape classroom can tell you which Statues you need.|"))
        #    patch.write(qt_encode("STATUE 1: INCA RUINS    You need the Wind Melody, Diamond Block, and both Incan Statues.|"))
        #    patch.write(qt_encode("STATUE 2: SKY GARDEN    You need all four Crystal Balls to fight the boss Viper.|"))
        #    patch.write(qt_encode("STATUE 3: MU            You need 2 Statues of Hope and 2 Rama Statues to fight the Vampires.|"))
        #    patch.write(qt_encode("STATUE 4: GREAT WALL    You need Spin Dash and Dark Friar to face the boss Sand Fanger.|"))
        #    patch.write(qt_encode("STATUE 5: PYRAMID       You need all six Hieroglyphs as well as your father's journal.|"))
        #    patch.write(qt_encode("STATUE 6: BABEL TOWER   You need the Aura and the Crystal Ring to get in.|"))
        #    patch.write(qt_encode("Alternatively, if you collect enough Red Jewels to face Solid Arm, he can also take you there.|"))
        #    patch.write(qt_encode("Once you've freed Kara and gathered the Statues you need, enter any Dark Space and talk to Gaia.|"))
        #    patch.write(qt_encode("She will give you the option to face the final boss and beat the game. Good luck, and have fun!") + b"\xc0")
        #
        #patch.seek(int("3f800", 16) + rom_offset)
        #patch.write(b"\xce" + qt_encode("EXPLORING THE WORLD:    When you start the game, you only have access to a few locations.|"))
        #patch.write(qt_encode("As you gain more items, you will be able to visit other continents and access more locations.|"))
        #patch.write(qt_encode("Here are some of the helpful travel items you can find in the game:|"))
        #patch.write(qt_encode("- Lola's Letter         If you find this letter, read it and go see Erik in South Cape.|"))
        #patch.write(qt_encode("- The Teapot            If you use the Teapot in the Moon Tribe camp, you can travel by Sky Garden.|"))
        #patch.write(qt_encode("- Memory Melody         Play this melody in Neil's Cottage, and he'll fly you in his airplane.|"))
        #patch.write(qt_encode("- The Will              Show this document to the stable masters in either Watermia or Euro.|"))
        #patch.write(qt_encode("- The Large Roast       Give this to the hungry child in the Natives' Village.|"))
        #patch.write(qt_encode("If you're ever stuck in a location, find a Dark Space. Gaia can always return you to South Cape.") + b"\xc0")
        #
        #patch.seek(int("3fb00", 16) + rom_offset)
        #patch.write(b"\xce" + qt_encode("WHAT IF I'M STUCK?      There are a lot of item locations in this game! It's easy to get stuck.|"))
        #patch.write(qt_encode("Here are some resources that might help you:|"))
        #patch.write(qt_encode("- Video Tutorial        Search YouTube for a video guide of this randomizer.|"))
        #patch.write(qt_encode("- EmoTracker            Download the IoGR package. Includes a map tracker!|"))
        #patch.write(qt_encode("- Ask the Community     Find the IoGR community on Discord! Someone will be happy to help you.|"))
        #patch.write(qt_encode("- Map House             Enter the east-most house in South Cape to check your collection rate.|"))
        #patch.write(qt_encode("- Spoiler Log           Every seed comes with a detailed list of where every item can be found.") + b"\xc0")

        ##########################################################################
        #                           Special Settings
        ##########################################################################
        ## Z3 Mode - write subroutines to available space
        #patch.seek(int("3faee", 16) + rom_offset)     # DEF halves damage subroutine
        #patch.write(b"\xDA\xAE\xDC\x0A\xE0\x00\x00\xF0\x04\x4A\xCA\x80\xF7\xFA\xC9\x00\x00\x60")
        #
        #if settings.z3:
        #    # Start with 6 HP
        #    patch.seek(int("8068", 16) + rom_offset)
        #    patch.write(b"\x06")
        #
        #    # Double damage on jump slash
        #    patch.seek(int("2cf58", 16) + rom_offset)
        #    patch.write(b"\xAD\xDE\x0A")
        #
        #    # Each DEF upgrade halves damage received
        #    patch.seek(int("3c464", 16) + rom_offset)
        #    patch.write(b"\x20\xEE\xFA")
        #
        #    # Update herb/HP upgrade fill values
        #    patch.seek(int("3fe5c", 16) + rom_offset)  # Expert #$08
        #    patch.write(b"\x08")
        #    patch.seek(int("3fe61", 16) + rom_offset)  # Advanced #$0E
        #    patch.write(b"\x0E")
        #    patch.seek(int("3fe66", 16) + rom_offset)  # Intermediate #$28
        #    patch.write(b"\x28")
        #
        #    # Call item upgrade subroutines
        #    patch.seek(int("3f01c", 16) + rom_offset)  # HP upgrade
        #    patch.write(b"\x20\xa1\xf7")
        #    patch.seek(int("3f042", 16) + rom_offset)  # STR upgrade
        #    patch.write(b"\x20\xc1\xf7")
        #    patch.seek(int("3f061", 16) + rom_offset)  # DEF upgrade
        #    patch.write(b"\x20\xe3\xf7")
        #
        ## In OHKO, the HP Jewels do nothing, and start @1HP
        #if settings.ohko:
        #    patch.seek(int("8068", 16) + rom_offset)  # Start 1 HP
        #    patch.write(b"\x01")
        #    patch.seek(int("3f7b1", 16) + rom_offset) # HP upgrade
        #    patch.write(b"\x00")
        #    patch.seek(int("3f7b7", 16) + rom_offset) # HP upgrade
        #    patch.write(b"\x00")
        #    patch.seek(int("3ffac", 16) + rom_offset) # heart piece
        #    patch.write(b"\x60")
#       #     patch.seek(int("39f71", 16) + rom_offset)
#       #     patch.write(b"\x00\xff\x02\xd5\x29\x60")
        #    # Also, herbs suck
        #    patch.seek(int("388e9", 16) + rom_offset)
        #    patch.write(b"\xce" + qt_encode("I mean... okay.") + b"\xc0")
        #
        ## In Red Jewel Madness, start @40 HP, Red Jewels remove -1 HP when used
        #elif settings.red_jewel_madness:
        #    # Start @ 40 HP
        #    patch.seek(int("8068", 16) + rom_offset)
        #    patch.write(b"\x28")
        #    # Red Jewels (item #$01) remove 1 HP when used
        #    patch.seek(int("384d5", 16) + rom_offset)
        #    patch.write(b"\x4c\x70\xfd")
        #    # 2 Red Jewels (item #$2e) removes 2 HP when used
        #    patch.seek(int("39d99", 16) + rom_offset)
        #    patch.write(b"\x01\x00\x8D\xB0\x0A\xD8\x4c\x76\xfd")
        #    # 3 Red Jewels (item #$2f) removes 3 HP when used
        #    patch.seek(int("39dd9", 16) + rom_offset)
        #    patch.write(b"\x02\x00\x8D\xB0\x0A\xD8\x4c\x7c\xfd")
        #
        ## Fluteless - prepare subroutines
        #patch.seek(int("2f845", 16) + rom_offset)
        #patch.write(b"\xa9\x00\x00\xcd\xd4\x0a\xf0\x03\xa9\x00\x01\x60"     # disable blocking for Will, $2f845
        #    + b"\xa9\x00\x04\x04\x10\xa9\x00\x02\x14\x10\x60"               # disable attack damage for Will, $2f851
        #    + b"\xad\x44\x06\xc9\xc6\x00\xf0\x0a\xad\xae\x09\x89\x08\x00\xf0\x02\x02\xe0\x4c\xbd\xb7")  # allow charge in snake game, $2f85c
        #if settings.fluteless:
        #    # Change melody sprite to Will whistling
        #    f_fluteless = open(BIN_PATH + "0f8fa4_fluteless.bin", "rb")
        #    patch.seek(int("f8fa4", 16) + rom_offset)
        #    patch.write(f_fluteless.read())
        #    f_fluteless.close
        #
        #    # Disable blocking for Will
        #    patch.seek(int("2ca63", 16) + rom_offset)
        #    patch.write(b"\x20\x45\xf8")
        #
        #    # Disable attack damage for Will
        #    patch.seek(int("2cefd", 16) + rom_offset)
        #    patch.write(b"\xad\xd4\x0a\xf0\x09\xa9\x00\x01\x14\x10\x02\x06\x02\x60\x4c\x51\xf8")
        #
        #    # Allow charging in snake game
        #    patch.seek(int("2b7b3", 16) + rom_offset)
        #    patch.write(b"\x4c\x5c\xf8")
        #
        #    # Y-shift certain enemy positions so they can be hit without a flute
        #    enemy_shift = [
        #        [b"\x5c\xbb\x8b", 1],    # Tunnel: Canal Worms up 1
        #        [b"\x5c\xbb\x8b",-1],    # Ankor Wat: Wall Bugs up 1
        #        [b"\x66\xbb\x8b",-1]]    # Ankor Wat: Wall Bugs up 1
        #    for [enemy_str,yshift] in enemy_shift:
        #        done = False
        #        addr = int("c8200", 16) + rom_offset
        #        while not done:
        #            addr = self.original_rom_data.find(enemy_str, addr+1)
        #            if addr < 0 or addr > int("ce5e4", 16) + rom_offset:
        #                done = True
        #            else:
        #                patch.seek(addr-2)
        #                patch.write((self.original_rom_data[addr-2]-yshift).to_bytes(1,byteorder="little"))

        ##########################################################################
        #                          Modify Moon Tribe events
        ##########################################################################
        ## Adjust timer for enemizer
        #timer = 20
#       # if settings.level.value == 0:
#       #     timer += 5
#       # elif settings.level.value >= 3:
#       #     timer -= 5
        #if settings.enemizer.value != Enemizer.NONE.value:
        #    timer += 5
        #    if settings.enemizer.value != Enemizer.LIMITED.value:
        #        timer += 5
        #patch.seek(int("4f8b8", 16) + rom_offset)
        #patch.write(binascii.unhexlify(str(timer)))

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

        ##########################################################################
        #                           Modify Freejia events
        ##########################################################################
        # Update NPC dialogue to acknowledge change
        patch.seek(int("5c331", 16) + rom_offset)
        patch.write(b"\x42\xa2\x80\xa0\x2b\xac\x48\xac\xd6\xae\xa4\x87\x84\xac\xd7\x58\xcb\xa5")
        patch.write(b"\x8d\x8b\x8e\x82\x8a\x84\x83\xac\x80\x86\x80\x88\x8d\x2a\x2a\x2a\xc0")

        # Woman on roof can warp you to prevent softlocks
        patch.seek(int("5b683", 16) + rom_offset) #four bytes
        patch.write(b"\x20\xa0\xff\xea")
        patch.seek(int("5ffa0", 16) + rom_offset)
        patch.write(b"\x02\xBF\xC3\xFF\x02\xBE\x02\x01\xAA\xFF\xB0\xFF\xB0\xFF\xB5\xFF")
        patch.write(b"\x02\xBF\xC0\xFF\x60\x02\x26\x32\x60\x03\x70\x01\x00\x00\x45\x60\xCE\xC8\xC0")
        patch.write(b"\xd3" + qt_encode("Stuck?") + b"\xcb\xac" + qt_encode("No") + b"\xcb\xac" + qt_encode("Yes") + b"\xca")

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

        # Give appearing Dark Space the option of handling an ability
        patch.seek(int("5d62f", 16) + rom_offset)
        patch.write(b"\xAC\xD6\x88\x00\x2B\xA5\x0E\x85\x24\xA9\x00\x20\x85\x0E\x02\xE0")

        ##########################################################################
        #                            Modify Nazca events
        ##########################################################################
        # Put a Moon Tribe where the warp point is
        patch.seek(int("5f2f1", 16) + rom_offset)
        patch.write(b"\x10\x80\x0B")
        patch.seek(int("5f30c", 16) + rom_offset)
        patch.write(b"\x02\xC0\xAD\xE6\x80\xF5")
        patch.seek(int("c9d29", 16) + rom_offset)
        patch.write(b"\x1D\x2C")

        ##########################################################################
        #                          Modify Sky Garden events
        ##########################################################################
        # Instant form change & warp to Seaside Palace if Viper is defeated
        patch.seek(int("ace9b", 16) + rom_offset)
        patch.write(b"\x4c\x99\xff")
        patch.seek(int("acecb", 16) + rom_offset)
        patch.write(b"\x01\x02\x26\x5a\x90\x00\x70\x00\x83\x00\x14\x02\xc1\x6b")

        f_viperchange = open(BIN_PATH + "0aff99_viperchange.bin", "rb")
        patch.seek(int("aff99", 16) + rom_offset)
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

        # Speed up purification sequence
        patch.seek(int("69450", 16) + rom_offset)
        patch.write(b"\x20")
        patch.seek(int("69456", 16) + rom_offset)
        patch.write(b"\x04")
        patch.seek(int("6945d", 16) + rom_offset)
        patch.write(b"\x01")
        patch.seek(int("6946f", 16) + rom_offset)
        patch.write(b"\x03")
        patch.seek(int("69486", 16) + rom_offset)
        patch.write(b"\x80\x10")

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

        # Shorten scene, text in Hope Room
        f_mu = open(BIN_PATH + "0699dc_mu.bin", "rb")
        patch.seek(int("699dc", 16) + rom_offset)
        patch.write(f_mu.read())
        f_mu.close
        patch.seek(int("69baa", 16) + rom_offset)
        patch.write(qt_encode("Hey.", True))

        # Move exits around to make Vampires required for Statue
        patch.seek(int("193ea", 16) + rom_offset)
        patch.write(b"\x5f\x80\x00\x50\x00\x03\x00\x44")
        patch.seek(int("193f8", 16) + rom_offset)
        patch.write(b"\x65\xb8\x00\x80\x02\x03\x00\x44")
        patch.seek(int("69c62", 16) + rom_offset)
        patch.write(b"\x67\x78\x01\xd0\x01\x80\x01\x22")
        patch.seek(int("afa51", 16) + rom_offset)
        patch.write(b"\x67\x78\x01\xd0\x01\x80\x01\x22")
        patch.seek(int("6a4c9", 16) + rom_offset)
        patch.write(b"\x02\x26\x66\xf8\x00\xd8\x01\x00\x00\x22\x02\xc1\x6b")

        ##########################################################################
        #                       Modify Angel Village events
        ##########################################################################
        # Add exit from Angel Village to Mu passage @1941a
        patch.seek(int("1941a", 16) + rom_offset)
        patch.write(b"\x2a\x05\x01\x01\x5e\x48\x00\x90\x00\x01\x00\x14")  # Temporarily put exit one tile south
        # patch.write(b"\x2a\x05\x01\x01\x5e\x48\x00\x80\x00\x01\x00\x14")  # Change to this if map is ever updated

        # Entering this area clears your enemy defeat count and forces change to Will
        patch.seek(int("6bff7", 16) + rom_offset)
        patch.write(b"\x00\x00\x30\x02\x40\x01\x0F\x01\xC0\x6b")
        #patch.write(b"\xA0\x00\x00\xA9\x00\x00\x99\x80\x0A\xC8\xC8\xC0\x20\x00\xD0\xF6")
        patch.write(CLEAR_ENEMIES + FORCE_CHANGE + b"\x02\xE0")

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

        # Reset Ishtar's puzzle upon entry (better solution than above)
        patch.seek(int("6d8c6", 16) + rom_offset)
        patch.write(b"\x0B\x02\x48\x3A\xD0\x03\x9C\xA6\x0A\x4C\x0C\xDA\xEA\xEA\xEA\xEA\xEA\xEA")
        patch.write(b"\xEA\xEA\xEA\xEA\xEA\xEA\xEA\xEA\xEA\xAD\x29\x0A\x29\x01\xFE\x8D\x29\x0A")

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

        # Fix Lance item get text
        patch.seek(int("7ad28", 16) + rom_offset)
        patch.write(INV_FULL)

        ##########################################################################
        #                          Modify Great Wall events
        ##########################################################################
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

        # Make Fanger's detection areas cover the arena, in case player moves during quake
        patch.seek(0x0b81a0 + rom_offset)
        patch.write(b"\x01\x19\x3f\x3f")
        patch.seek(0x0b81b7 + rom_offset)
        patch.write(b"\x01\x2c\x3f\x3f")

        ##########################################################################
        #                            Modify Euro events
        ##########################################################################
        patch.seek(int("7c482", 16) + rom_offset)
        patch.write(qt_encode("A moose once bit my sister.", True))

        # Neil in Euro
        patch.seek(int("7e37f", 16) + rom_offset)
        patch.write(b"\x14\x00")
        patch.seek(int("7e392", 16) + rom_offset)
        patch.write(b"\x5C\xBE\xD8\x85")

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

        # Euro shopkeeper can warp you to start in entrance shuffle (prevents softlocks)
        if settings.entrance_shuffle.value != EntranceShuffle.NONE.value:
            patch.seek(int("7cbba", 16) + rom_offset) #four bytes
            patch.write(b"\x4c\x27\xe9")
            patch.seek(int("7e927", 16) + rom_offset)
            patch.write(b"\x02\xBF\x0A\xCC\x02\xBE\x02\x01\x31\xE9\x37\xE9\x37\xE9\x3E\xE9")
            patch.write(b"\x02\xBF\x24\xCC\x4C\xBE\xCB\x5C\xE8\xDB\x88")
            patch.seek(int("7cc0c", 16) + rom_offset)
            patch.write(qt_encode("Warp to start?") + b"\xcb\xac" + qt_encode("No") + b"\xcb\xac" + qt_encode("Yes") + b"\xca")
            patch.write(b"\xce" + qt_encode("NO SOUP FOR YOU!") + b"\xc0")

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
        # Change event pointers for cannibalized NPC code
        patch.seek(int("cca93", 16) + rom_offset)
        patch.write(b"\x88\x8f\x88")

        ##########################################################################
        #                            Modify Dao events
        ##########################################################################
        # Neil in Dao
        patch.seek(int("8a5bf", 16) + rom_offset)
        patch.write(b"\x10")
        patch.seek(int("8a5f1", 16) + rom_offset)
        patch.write(b"\x14\x01\xFE\xA5\x02\xD0\x14\x01\xFE\xA5\x02\xE0\x6B\x5C\xBE\xD8\x85")
        patch.seek(int("8a5b3", 16) + rom_offset)
        patch.write(b"\x14\x00")

        # Allow travel back to Natives' Village
        patch.seek(int("8b16d", 16) + rom_offset)
        patch.write(b"\x4c\x50\xfe")
        patch.seek(int("8fe50", 16) + rom_offset)
        patch.write(b"\x02\xBF\x78\xFE\x02\xBE\x02\x01\x5A\xFE\x60\xFE\x60\xFE\x65\xFE\x02\xBF\x9A\xFE\x6B")
        patch.write(b"\x02\x26\xAC\xC0\x01\xD0\x01\x06\x00\x22\x22\x9B\xFF\x81\x9C\xD4\x0A\x02\xC5")
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
        patch.write(b"\x49\x8e\xa5\xa2\x8d\x80\x8b\xac\xac\xac\xac\xac\xac\xc9\x0a\xCF\xCE")
        patch.write(qt_encode("If you want a guide to take you to the Natives' Village, I can get one for you.") + b"\xc0")

        # Spirit appears only after you defeat Mummy Queen or Solid Arm
        patch.seek(int("980cb", 16) + rom_offset)
        patch.write(b"\x4c\xb0\xf6")
        patch.seek(int("9f6b0", 16) + rom_offset)
        patch.write(b"\x02\xd0\xf6\x01\xd1\x80\x02\xd1\x79\x01\x01\xd1\x80\x02\xe0")

        # Force single overworld map exit
        patch.seek(int("cd12", 16) + rom_offset)
        patch.write(b"\x80\x04")

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

        # Speed up Room 3 elevator
        patch.seek(int("8c55b", 16) + rom_offset)
        patch.write(b"\x20\x70\xff\xea\xea\xea")
        patch.seek(int("8c56c", 16) + rom_offset)
        patch.write(b"\x20\x76\xff\xea\xea\xea")
        patch.seek(int("8ff70", 16) + rom_offset)
        patch.write(b"\x3a\x3a\x3a\x3a\x80\x04\x1a\x1a\x1a\x1a")
        patch.write(b"\x99\x26\x00\xc6\x26\xc6\x26\xc6\x26\xc6\x26\x60")

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
        patch.write(CLEAR_ENEMIES + b"\x02\xd0\xdc\x00\xa0\x99\x02\xd0\x3e\x00\xa0\x99\x02\xd0\xb4\x01\x9a\x99\x4c\xa0\x99")
        patch.seek(int("999aa", 16) + rom_offset)
        patch.write(b"\x4c\xf0\xf6")
        patch.seek(int("9f6f0", 16) + rom_offset)
        patch.write(b"\x02\xd0\xdc\x01\x9a\x99\x4c\xaf\x99")
        patch.seek(int("99a49", 16) + rom_offset)
        patch.write(b"\x02\xbf\xe4\x9a\x02\xd4\x27\x57\x9a\x02\xcc\xdc\x02\xe0" + INV_FULL)
        # Change text
        patch.seek(int("99a70", 16) + rom_offset)
        patch.write(qt_encode("Well, lookie there.", True))

        # Speed up warp sequences
        patch.seek(int("995a9", 16) + rom_offset)
        patch.write(b"\x01\x00")
        patch.seek(int("995b0", 16) + rom_offset)
        patch.write(b"\x01\x00")
        patch.seek(int("996ab", 16) + rom_offset)
        patch.write(b"\x03")
        patch.seek(int("996fd", 16) + rom_offset)
        patch.write(b"\x10")
        patch.seek(int("9982a", 16) + rom_offset)
        patch.write(b"\x10")
        patch.seek(int("99848", 16) + rom_offset)
        patch.write(b"\x04")

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

        # Dao spirit forces form change
        patch.seek(int("98045", 16) + rom_offset)
        patch.write(b"\x20\xc0\xf6")
        patch.seek(int("9f6c0", 16) + rom_offset)
        patch.write(b"\x8D\x48\x06" + CLEAR_ENEMIES + FORCE_CHANGE + b"\x60")

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
        patch.write(qt_encode(" Devs: Raeven0, Bryon W") + b"\xCB" + qt_encode("    and Neomatamune"))
        patch.write(b"\xCB" + qt_encode(" EmoTracker by Apokalysme"))
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

        # Test for infinite death loop
        patch.seek(int("bd32b", 16) + rom_offset)
        patch.write(b"\x4c\xe0\xff")
        f_infdeath = open(BIN_PATH + "0bfe40_infdeath.bin", "rb")
        patch.seek(int("bfe40", 16) + rom_offset)
        patch.write(f_infdeath.read())
        f_infdeath.close

        # Thank the playtesters
        patch.seek(int("be056", 16) + rom_offset)
        patch.write(b"\x74\xfa")
        patch.seek(int("bfa74", 16) + rom_offset)
        patch.write(b"\xD3\xD2\x00\xD5\x00" + qt_encode("Contributors and Testers:") + b"\xCB")
        patch.write(qt_encode("-Alchemic -Atlas") + b"\xCB")
        patch.write(qt_encode("-ChaozJoe -BOWIEtheHERO") + b"\xCB")
        patch.write(qt_encode("-HirosofT -BubbaSWalter") + b"\xC9\xB4\xCE")

        patch.write(qt_encode("-Austin21300 -DerTolleIgel") + b"\xCB")
        patch.write(qt_encode("-djtifaheart -DoodSF") + b"\xCB")
        patch.write(qt_encode("-SmashManiac -Eppy37") + b"\xCB")
        patch.write(qt_encode("-Tymekeeper  -Lassic") + b"\xC9\xB4\xCE")

        patch.write(qt_encode("-BonzaiBier -GliitchWiitch") + b"\xCB")
        patch.write(qt_encode("-Keypaladin -LeHulk") + b"\xCB")
        patch.write(qt_encode("-QueenAnneB -Mikan") + b"\xCB")
        patch.write(qt_encode("-stevehacks -Nemo") + b"\xC9\xB4\xCE")

        patch.write(qt_encode("-Crazyhaze -Plan") + b"\xCB")
        patch.write(qt_encode("-NYRambler -PozzumSenpai") + b"\xCB")
        patch.write(qt_encode("-wildfang1 -roeya") + b"\xCB")
        patch.write(qt_encode("-ZekeStarr -Skipsy") + b"\xC9\xB4\xCE")

        patch.write(qt_encode("-MrFreet -solarcell007") + b"\xCB")
        patch.write(qt_encode("-Scheris -SO5Z") + b"\xCB")
        patch.write(qt_encode("-SDiezal -Sye990") + b"\xC9\xB4\xCE")

        patch.write(qt_encode("-Skarsnik -Veetorp") + b"\xCB")
        patch.write(qt_encode("-Verallix -Volor") + b"\xCB")
        patch.write(qt_encode("-Voranthe -wormsofcan") + b"\xC9\xB4\xCE")

        patch.write(qt_encode("-Tsurana -xIceblue") + b"\xCB")
        patch.write(qt_encode("-Wilddin -ZockerStu") + b"\xCB")
        patch.write(qt_encode("-Xyrcord -Z4t0x") + b"\xC9\xB4\xCE")

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

        # Inca Ruins Entrance
        patch.seek(int("9ca03", 16) + rom_offset)  # Lilly
        patch.write(b"\xe0\x6b")
        patch.seek(int("9cea7", 16) + rom_offset)  # Kara
        patch.write(b"\xe0\x6b")

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

        # HP room rewards become +3 (non-Z3 mode only)
        if not settings.z3:
            # Room-clearing rewards
            patch.seek(int("e041", 16) + rom_offset)
            patch.write(b"\x03")

            # Boss rewards
            patch.seek(int("c381", 16) + rom_offset)
            patch.write(b"\x20\x90\xf4")
            patch.seek(int("f490", 16) + rom_offset)
            patch.write(b"\xee\xca\x0a\xee\xca\x0a\xee\xca\x0a\x60")

        # Change boss room ranges
        patch.seek(int("c31a", 16) + rom_offset)
        patch.write(b"\x67\x5A\x74\x00\x8A\x82\xA9\x00\xDD\xCC\xDD\x00\xF6\xB0\xBF\x00")
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
        if settings.z3:
            patch.write(b"\x01\xC6\x01\x03\x14\x2D\x31\x48\x50\x00")  # "+1HP"
        else:
            patch.write(b"\x01\xC6\x01\x03\x14\x2D\x33\x48\x50\x00")  # "+3HP"
        patch.seek(int("1ff80", 16) + rom_offset)
        patch.write(b"\x01\xC6\x01\x03\x14\x2D\x31\x53\x54\x52\x00")  # "+1STR"
        patch.seek(int("1ff90", 16) + rom_offset)
        patch.write(b"\x01\xC6\x01\x03\x14\x2D\x31\x44\x45\x46\x00")  # "+1DEF"

        ##########################################################################
        #                        Balance Enemy Stats
        ##########################################################################
        # Write Intermediate stat table to vanilla location for legacy code
        if settings.z3:
            f_legacystats = open(BIN_PATH + "01abf0_enemies_z3.bin", "rb")
        else:
            f_legacystats = open(BIN_PATH + "01abf0_enemiesintermediate.bin", "rb")
        patch.seek(int("1abf0", 16) + rom_offset)
        patch.write(f_legacystats.read())
        f_legacystats.close

        # Write enemy stat tables to memory, by Level
        if settings.z3:
            f_enemystats = open(BIN_PATH + "02f130_enemystats_z3.bin", "rb")
        else:
            f_enemystats = open(BIN_PATH + "02f130_enemystats.bin", "rb")
        patch.seek(int("2f130", 16) + rom_offset)
        patch.write(f_enemystats.read())
        f_enemystats.close

        # Rewrite enemy lookup routines to reference new tables
        patch.seek(int("3d003", 16) + rom_offset)   # HP
        patch.write(b"\x20\x80\xfe")
        patch.seek(int("3fe80", 16) + rom_offset)
        patch.write(b"\x20\xAD\xFE\xDA\xBB\xBF\x00\x00\x82\xFA\x60")       # HP
        patch.write(b"\x20\xAD\xFE\xDA\xBB\xBF\x01\x00\x82\xFA\x60")       # STR
        patch.write(b"\x20\xAD\xFE\xDA\xBB\xBF\x02\x00\x82\xFA\x60")       # DEF
        patch.write(b"\xA8\x20\xAD\xFE\xDA\xBB\xBF\x03\x00\x82\xFA\x6B")   # GEM, inconsistent APIs are a problem for future Bagu
        # Fix hardcoded stat block pointers
        patch.write(b"\xC0\x00\xB0\xB0\x0C\x98\xF0\x09\x38\xE9\xF0\xAB\x18\x20\xd0\xfe\xA8\x60")
        patch.seek(0x03be52 + rom_offset)
        patch.write(b"\x82")
        patch.seek(0x03bfba + rom_offset)   # HP
        patch.write(b"\x20\x80\xfe")
        patch.seek(0x03bfc3 + rom_offset)   # DEF
        patch.write(b"\x20\x96\xfe")
        patch.seek(0x03c45d + rom_offset)   # STR
        patch.write(b"\x20\x8b\xfe")
        patch.seek(0x00dadd + rom_offset)   # GEM
        patch.write(b"\x22\xa1\xfe\x83")
        patch.seek(0x00dc07 + rom_offset)   # GEM
        patch.write(b"\x22\xa1\xfe\x83")
        patch.seek(int("3fed0", 16) + rom_offset)
        patch.write(b"\x48\xAD\x24\x0B\xF0\x18\x3A\xF0\x0F\x3A\xF0\x06\x68\x69\x70\xF6\x80\x10")
        patch.write(b"\x68\x69\xB0\xF4\x80\x0A\x68\x69\xF0\xF2\x80\x04\x68\x69\x30\xF1\x60")
        patch.seek(int("3cffb", 16) + rom_offset)
        patch.write(b"\x20\xd0\xfe")


        ##########################################################################
        #                            Randomize Inca tile
        ##########################################################################
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

        # Get uncompressed map data
        f_incamapblank = open(BIN_PATH + "incamapblank.bin", "rb")
        incamap_data = f_incamapblank.read()
        f_incamapblank.close

        # Insert new compressed map data
        # patch.seek(int("1f38db",16)+rom_offset)
        incamap_data = incamap_data[:addr] + b"\x40\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x42\x43" + incamap_data[addr+18:]
        patch.seek(int("1f3ea0", 16) + rom_offset)
        patch.write(b"\x02\x02")
        patch.write(qt_compress(incamap_data))

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

        # Update snake game logic with new values
        patch.seek(int("8afe6", 16) + rom_offset)   # Timer, in frames (vanilla b"\x10\x0e")
        patch.write(binascii.unhexlify(snake_frames_str))
        patch.seek(int("8ff50", 16) + rom_offset)   # Snake target BCD (vanilla b"\x51")
        patch.write(binascii.unhexlify(snake_target_str[0]))
        patch.write(b"\x00")
        patch.write(binascii.unhexlify(snake_target_str[1]))
        patch.write(b"\x00")
        patch.write(binascii.unhexlify(snake_target_str[2]))
        patch.write(b"\x00")
        patch.write(binascii.unhexlify(snake_target_str[3]))
        patch.write(b"\x00")

        patch.seek(int("8aff3", 16) + rom_offset)
        patch.write(b"\x4c\x58\xff")
        patch.seek(int("8ff58", 16) + rom_offset)
        patch.write(b"\xDA\xAD\x24\x0B\x0A\xAA\xAD\xAC\x0A\xDF\x50\xFF\x88\xFA\x4C\xF9\xAF")

        # Update text to reflect changes
        patch.seek(int("8aeb9", 16) + rom_offset)
        patch.write(b"\x4c\x20\xaf")
        patch.seek(int("8af20", 16) + rom_offset)
        patch.write(b"\xAD\x24\x0B\xF0\x18\x3A\xF0\x0F\x3A\xF0\x06\x02\xBF\x28\xFF\x80\x10")
        patch.write(b"\x02\xBF\x00\xFF\x80\x0A\x02\xBF\xD8\xFE\x80\x04\x02\xBF\xB0\xFE\x4C\xBD\xAE")

        patch.seek(int("8feb0", 16) + rom_offset)
        patch.write(b"\xCE" + qt_encode("Hit " + str(snake_target[0]) + " snakes in " + str(snake_timer) + " seconds. Go!") + b"\xC0")
        patch.seek(int("8fed8", 16) + rom_offset)
        patch.write(b"\xCE" + qt_encode("Hit " + str(snake_target[1]) + " snakes in " + str(snake_timer) + " seconds. Go!") + b"\xC0")
        patch.seek(int("8ff00", 16) + rom_offset)
        patch.write(b"\xCE" + qt_encode("Hit " + str(snake_target[2]) + " snakes in " + str(snake_timer) + " seconds. Go!") + b"\xC0")
        patch.seek(int("8ff28", 16) + rom_offset)
        patch.write(b"\xCE" + qt_encode("Hit " + str(snake_target[3]) + " snakes in " + str(snake_timer) + " seconds. Go!") + b"\xC0")

        ##########################################################################
        #                    Randomize Jeweler Reward amounts
        ##########################################################################
        # Randomize jeweler reward values
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

        if int(gem_str[3]) < 10:
            gem_str[3] = format(2, "x") + format(gem[3] % 10, "x")
            patch.seek(int("8d2aa", 16) + rom_offset)
            patch.write(b"\xac" + binascii.unhexlify(gem_str[3]))
        else:
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

        if statue_req == StatueReq.PLAYER_CHOICE.value:
            statues = statueOrder[:]
            statues_hex = []

            # Set "player choice" flag in RAM (for autotracker)
            patch.seek(int("bfd4a", 16) + rom_offset)
            patch.write(b"\xfe\x02")

            # Modify end-game logic to check for statue count
            patch.seek(int("8dd17", 16) + rom_offset)
            patch.write(b"\xad\x1f\x0a\x8d\x00\x00\xa9\x00\x00\x18\xe2\x20\x20\x86\xff\xc2\x20\xc9")
            patch.write(statues_required.to_bytes(1,byteorder="little") + b"\x00\xb0\x03\x4c\x14\xdb\x80\x09")
            patch.seek(int("8ff86", 16) + rom_offset)
            patch.write(b"\x4e\x00\x00\x69\x00\x4e\x00\x00\x69\x00\x4e\x00\x00\x69\x00")
            patch.write(b"\x4e\x00\x00\x69\x00\x4e\x00\x00\x69\x00\x4e\x00\x00\x69\x00\x60")

        else:
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
        if settings.goal.value == Goal.RED_JEWEL_HUNT.value:
            patch.seek(int("8dd0d", 16) + rom_offset)
            patch.write(b"\x10\x01")

        statues.sort()
        statues_hex.sort()

        # Teacher at start spoils required Mystic Statues
        statue_str = ""
        if len(statues_hex) == 0:
            if statues_required == 0:
                statue_str = b"\xd3\x4d\x8e"
            else:
                statue_str = b"\xd3" + (0x20+statues_required).to_bytes(1,byteorder="little")
            statue_str += b"\xac\xd6\xd2\x80\xa2\x84\xac\xa2\x84\xa1\xa5\x88\xa2\x84\x83\x4f\xc0"
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

            if boss_order[5] != 6:      # Prevent early access to Babel entrance
                patch.seek(int("ce165", 16) + rom_offset)
                patch.write(b"\xff\xca")

            #    n = random.randint(1,6)
            #    boss_order = boss_order[n:] + boss_order[:n]

            #if boss_order[6] == 6:      # Prevent Babel self-loops (MQII can't be in Mansion) - NO LONGER NECESSARY
            #    n = random.randint(1,6)
            #    boss_order = boss_order[n:] + boss_order[:n]


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

            # Patch music headers into new dungeons (beginner and intermediate modes)
            if settings.difficulty.value <= 1:
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
                    if PRINT_LOG:
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
        babel_boss = boss_order.index(6)
        patch.seek(int("980a6", 16) + rom_offset)
        if babel_boss == 0:
            patch.write(b"\x42\x8e\x80\xa3\xa4\xca")                      # "Coast"
        elif babel_boss == 1:
            patch.write(b"\x63\x84\x80\xac\x60\x80\x8b\x80\x82\x84\xca")  # "Seaside Palace"
        elif babel_boss == 2:
            patch.write(b"\x4c\xa5\xca")                                  # "Mu"
        elif babel_boss == 3:
            patch.write(b"\xd6\x16\x67\x80\x8b\x8b\xca")                  # "Great Wall"
        elif babel_boss == 4:
            patch.write(b"\xd6\x3f\xca")                                  # "Pyramid"

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

        # Set Kara's location and logic mode in RAM switches (for autotracker)
        if settings.logic.value == Logic.COMPLETABLE.value:
            logic_int = 0x10 + kara_location
        elif settings.logic.value == Logic.BEATABLE.value:
            logic_int = 0x20 + kara_location
        else:
            logic_int = 0x40 + kara_location

        patch.seek(int("bfd13", 16) + rom_offset)
        patch.write(logic_int.to_bytes(1,byteorder="little"))

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
        patch.seek(int("d7c3", 16) + rom_offset)
        patch.write(death_list[random.randint(0, len(death_list) - 1)])
        # patch.write(death_list[0])

        # Standardize text, check for infinite death loop
        patch.seek(int("d7a2", 16) + rom_offset)
        patch.write(b"\xAD\xCA\x0A\xF0\x06\x02\xBF\xC2\xD7\x80\x0D\x02\xBF\xF0\xFD\x80\x07")

        f_pi = open(BIN_PATH + "00fdf0_pi.bin", "rb")
        patch.seek(int("fdf0", 16) + rom_offset)
        patch.write(f_pi.read())
        f_pi.close()

        ##########################################################################
        #                   Randomize item and ability placement
        ##########################################################################
        done = False
        seed_adj = 0
        #self.w = World(settings, statues, kara_location, gem, [inca_x + 1, inca_y + 1], hieroglyph_order, boss_order)
        while not done:
            if seed_adj > MAX_RANDO_RETRIES:
                self.logger.error("ERROR: Max number of seed adjustments exceeded")
                raise RecursionError
            elif seed_adj > 0:
                if PRINT_LOG:
                    print("Trying again... attempt", seed_adj+1)
            self.w = World(settings, statues_required, statues, statue_req, kara_location, gem, [inca_x + 1, inca_y + 1], hieroglyph_order, boss_order)
            done = self.w.randomize(seed_adj,PRINT_LOG)
            #k6_item = self.w.item_locations[136][3]
            #print(self.w.item_pool[k6_item][3])
            #done = False
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
                if PRINT_LOG:
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
        ishtarmapdata = f_ishtarmapblank.read()
        f_ishtarmapblank.close()
        f_ishtarmap = tempfile.TemporaryFile()
        f_ishtarmap.write(ishtarmapdata)

        # Initialize data
        room_offsets = ["6d95e", "6d98a", "6d9b4", "6d9de"]  # ROM addrs for cursor capture, by room
        coord_offsets = [3, 8, 15, 20]  # Byte offsets for xmin, xmax, ymin, ymax
        coords = [[],[],[],[]]
        idx_diff = [[],[],[],[]]
        other_changes = [[],[],[],[]]
        changes = [list(range(11)), list(range(8)), list(range(5)), list(range(10))]

        # Check if chest contents in room 3 are identical
        same_chest = (self.w.item_locations[80][3] == self.w.item_locations[81][3])

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

            if PRINT_LOG:
                print("Ishtar room",room+1,":",idx_diff[room],other_changes[room])
            done = False
            while not done:
                if other_changes[room]:
                    change_id = other_changes[room].pop(0)
                else:
                    change_id = idx_diff[room]
                    done = True

                # Set change for Room 1
                if room == 0:
                    if change_id == 0:  # Will's hair
                        patch.seek(int("6dd06", 16) + rom_offset)
                        patch.write(b"\x5d")
                        coords[room] = [b"\xa0\x01", b"\xc0\x01", b"\xb0\x00", b"\xd0\x00"]

                    elif change_id == 1:  # Change right vase to light (vanilla)
                        f_ishtarmap.seek(int("17b", 16))
                        f_ishtarmap.write(b"\x7b")
                        f_ishtarmap.seek(int("18b", 16))
                        f_ishtarmap.write(b"\x84")
                        if done:
                            coords[room] = [b"\xB0\x01", b"\xC0\x01", b"\x70\x00", b"\x90\x00"]
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
                            coords[room] = [b"\x50\x01", b"\x60\x01", b"\x70\x00", b"\x90\x00"]
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
                            coords[room] = [b"\x40\x01", b"\x50\x01", b"\x70\x00", b"\x90\x00"]
                        else:
                            f_ishtarmap.seek(int("74", 16))
                            f_ishtarmap.write(b"\x83")
                            f_ishtarmap.seek(int("84", 16))
                            f_ishtarmap.write(b"\x87")

                    elif change_id == 4:  # Change left shelf to empty
                        f_ishtarmap.seek(int("165", 16))
                        f_ishtarmap.write(b"\x74")
                        if done:
                            coords[room] = [b"\x50\x01", b"\x60\x01", b"\x58\x00", b"\x70\x00"]
                        else:
                            f_ishtarmap.seek(int("65", 16))
                            f_ishtarmap.write(b"\x74")

                    elif change_id == 5:  # Change left shelf to books
                        f_ishtarmap.seek(int("165", 16))
                        f_ishtarmap.write(b"\x76")
                        if done:
                            coords[room] = [b"\x50\x01", b"\x60\x01", b"\x58\x00", b"\x70\x00"]
                        else:
                            f_ishtarmap.seek(int("65", 16))
                            f_ishtarmap.write(b"\x76")

                    elif change_id == 6:  # Change right shelf to jar
                        f_ishtarmap.seek(int("166", 16))
                        f_ishtarmap.write(b"\x75")
                        if done:
                            coords[room] = [b"\x60\x01", b"\x70\x01", b"\x58\x00", b"\x70\x00"]
                        else:
                            f_ishtarmap.seek(int("66", 16))
                            f_ishtarmap.write(b"\x75")

                    elif change_id == 7:  # Change right shelf to empty
                        f_ishtarmap.seek(int("166", 16))
                        f_ishtarmap.write(b"\x74")
                        if done:
                            coords[room] = [b"\x60\x01", b"\x70\x01", b"\x58\x00", b"\x70\x00"]
                        else:
                            f_ishtarmap.seek(int("66", 16))
                            f_ishtarmap.write(b"\x74")

                    elif change_id == 8:  # Remove left sconce
                        f_ishtarmap.seek(int("157", 16))
                        f_ishtarmap.write(b"\x12\x12")
                        f_ishtarmap.seek(int("167", 16))
                        f_ishtarmap.write(b"\x1a\x1a")
                        if done:
                            coords[room] = [b"\x70\x01", b"\x90\x01", b"\x50\x00", b"\x70\x00"]
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
                            coords[room] = [b"\xa0\x01", b"\xc0\x01", b"\x50\x00", b"\x70\x00"]
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
                            coords[room] = [b"\xa0\x01", b"\xb0\x01", b"\x70\x00", b"\x90\x00"]
                        else:
                            f_ishtarmap.seek(int("7a", 16))
                            f_ishtarmap.write(b"\x83\x22")
                            f_ishtarmap.seek(int("8a", 16))
                            f_ishtarmap.write(b"\x87\x13")


                # Set change for Room 2
                elif room == 1:
                    if change_id == 0:  # Will's hair
                        patch.seek(int("6dd0e", 16) + rom_offset)
                        patch.write(b"\x5d")
                        coords[room] = [b"\x90\x03", b"\xb0\x03", b"\xa0\x00", b"\xc0\x00"]

                    elif change_id == 1:  # Change left vase to light
                        f_ishtarmap.seek(int("3a3", 16))
                        f_ishtarmap.write(b"\x7c")
                        f_ishtarmap.seek(int("3b3", 16))
                        f_ishtarmap.write(b"\x84")
                        if done:
                            coords[room] = [b"\x30\x03", b"\x40\x03", b"\xa0\x00", b"\xc0\x00"]
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
                            coords[room] = [b"\x40\x03", b"\x50\x03", b"\xa0\x00", b"\xc0\x00"]
                        else:
                            f_ishtarmap.seek(int("2a4", 16))
                            f_ishtarmap.write(b"\x7c")
                            f_ishtarmap.seek(int("2b4", 16))
                            f_ishtarmap.write(b"\x84")

                    elif change_id == 3:  # Remove rock
                        f_ishtarmap.seek(int("3bd", 16))
                        f_ishtarmap.write(b"\x73")
                        if done:
                            coords[room] = [b"\xd0\x03", b"\xe0\x03", b"\xb0\x00", b"\xc0\x00"]
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
                            coords[room] = [b"\x50\x03", b"\x70\x03", b"\x90\x00", b"\xb0\x00"]
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
                            coords[room] = [b"\x70\x03", b"\x90\x03", b"\x50\x00", b"\x70\x00"]
                        else:
                            f_ishtarmap.seek(int("257", 16))
                            f_ishtarmap.write(b"\x88\x89")
                            f_ishtarmap.seek(int("267", 16))
                            f_ishtarmap.write(b"\x90\x91")

                    elif change_id == 6:  # Add rock
                        f_ishtarmap.seek(int("3b2", 16))
                        f_ishtarmap.write(b"\x77")
                        if done:
                            coords[room] = [b"\x20\x03", b"\x30\x03", b"\xb0\x00", b"\xc0\x00"]
                        else:
                            f_ishtarmap.seek(int("2b2", 16))
                            f_ishtarmap.write(b"\x77")

                    elif change_id == 7:  # Put moss on rock
                        f_ishtarmap.seek(int("3bd", 16))
                        f_ishtarmap.write(b"\x8f")
                        if done:
                            coords[room] = [b"\xd0\x03", b"\xe0\x03", b"\xb0\x00", b"\xc0\x00"]
                        else:
                            f_ishtarmap.seek(int("2bd", 16))
                            f_ishtarmap.write(b"\x8f")

#                    elif change_id == 8:  # Change both vases to light (vanilla) - DOESN'T PLAY WELL WITH OTHERS, IS IN TIME OUT
#                        f_ishtarmap.seek(int("3a3", 16))
#                        f_ishtarmap.write(b"\x7c\x7c")
#                        f_ishtarmap.seek(int("3b3", 16))
#                        f_ishtarmap.write(b"\x84\x84")
#                        if done:
#                            coords[room] = [b"\x30\x03", b"\x50\x03", b"\xa0\x00", b"\xc0\x00"]
#                        else:
#                            f_ishtarmap.seek(int("2a3", 16))
#                            f_ishtarmap.write(b"\x7c\x7c")
#                            f_ishtarmap.seek(int("2b3", 16))
#                            f_ishtarmap.write(b"\x84\x84")


                # Set change for Room 3
                elif room == 2:
                    if (not done or same_chest) and change_id == 0:  # Will's hair
                        patch.seek(int("6dd16", 16) + rom_offset)
                        patch.write(b"\x5d")
                        coords[room] = [b"\x90\x05", b"\xb0\x05", b"\xa0\x00", b"\xc0\x00"]

                    if (not done or same_chest) and change_id == 1:  # Remove rock
                        f_ishtarmap.seek(int("5bd", 16))
                        f_ishtarmap.write(b"\x73")
                        if (done and same_chest):
                            coords[room] = [b"\xd0\x05", b"\xe0\x05", b"\xb0\x00", b"\xc0\x00"]
                        elif not done:
                            f_ishtarmap.seek(int("4bd", 16))
                            f_ishtarmap.write(b"\x73")

                    if (not done or same_chest) and change_id == 2:  # Add rock
                        f_ishtarmap.seek(int("5b2", 16))
                        f_ishtarmap.write(b"\x77")
                        if (done and same_chest):
                            coords[room] = [b"\x20\x05", b"\x30\x05", b"\xb0\x00", b"\xc0\x00"]
                        elif not done:
                            f_ishtarmap.seek(int("4b2", 16))
                            f_ishtarmap.write(b"\x77")

                    if (not done or same_chest) and change_id == 3:  # Add sconce
                        f_ishtarmap.seek(int("557", 16))
                        f_ishtarmap.write(b"\x88\x89")
                        f_ishtarmap.seek(int("567", 16))
                        f_ishtarmap.write(b"\x90\x91")
                        if (done and same_chest):
                            coords[room] = [b"\x70\x05", b"\x90\x05", b"\x50\x00", b"\x70\x00"]
                        elif not done:
                            f_ishtarmap.seek(int("457", 16))
                            f_ishtarmap.write(b"\x88\x89")
                            f_ishtarmap.seek(int("467", 16))
                            f_ishtarmap.write(b"\x90\x91")

                    if (not done or same_chest) and change_id == 4:  # Moss rock
                        f_ishtarmap.seek(int("5bd", 16))
                        f_ishtarmap.write(b"\x8f")
                        if (done and same_chest):
                            coords[room] = [b"\xd0\x05", b"\xe0\x05", b"\xb0\x00", b"\xc0\x00"]
                        elif not done:
                            f_ishtarmap.seek(int("4bd", 16))
                            f_ishtarmap.write(b"\x8f")


                # Set change for Room 4
                elif room == 3:
                    if change_id == 0:  # Will's hair (vanilla)
                        patch.seek(int("6dd1e", 16) + rom_offset)
                        patch.write(b"\x5d")

                    if change_id == 1:  # Remove rock
                        f_ishtarmap.seek(int("7bd", 16))
                        f_ishtarmap.write(b"\x73")
                        if done:
                            coords[room] = [b"\xd0\x07", b"\xe0\x07", b"\xb0\x00", b"\xc0\x00"]
                        else:
                            f_ishtarmap.seek(int("6bd", 16))
                            f_ishtarmap.write(b"\x73")

                    if change_id == 2:  # Add rock L
                        f_ishtarmap.seek(int("7b2", 16))
                        f_ishtarmap.write(b"\x77")
                        if done:
                            coords[room] = [b"\x20\x07", b"\x30\x07", b"\xb0\x00", b"\xc0\x00"]
                        else:
                            f_ishtarmap.seek(int("6b2", 16))
                            f_ishtarmap.write(b"\x77")

                    if change_id == 3:  # Add moss rock L
                        f_ishtarmap.seek(int("7b2", 16))
                        f_ishtarmap.write(b"\x8f")
                        if done:
                            coords[room] = [b"\x20\x07", b"\x30\x07", b"\xb0\x00", b"\xc0\x00"]
                        else:
                            f_ishtarmap.seek(int("6b2", 16))
                            f_ishtarmap.write(b"\x8f")

                    if change_id == 4:  # Add light vase L
                        f_ishtarmap.seek(int("7a3", 16))
                        f_ishtarmap.write(b"\x7c")
                        f_ishtarmap.seek(int("7b3", 16))
                        f_ishtarmap.write(b"\x84")
                        if done:
                            coords[room] = [b"\x30\x07", b"\x40\x07", b"\xa0\x00", b"\xc0\x00"]
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
                            coords[room] = [b"\x30\x07", b"\x40\x07", b"\xa0\x00", b"\xc0\x00"]
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
                            coords[room] = [b"\xc0\x07", b"\xd0\x07", b"\xa0\x00", b"\xc0\x00"]
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
                            coords[room] = [b"\xc0\x07", b"\xd0\x07", b"\xa0\x00", b"\xc0\x00"]
                        else:
                            f_ishtarmap.seek(int("6ac", 16))
                            f_ishtarmap.write(b"\x7f")
                            f_ishtarmap.seek(int("6bc", 16))
                            f_ishtarmap.write(b"\x87")

                    if change_id == 8:  # Crease in floor
                        f_ishtarmap.seek(int("7b4", 16))
                        f_ishtarmap.write(b"\x69\x6a")
                        if done:
                            coords[room] = [b"\x40\x07", b"\x60\x07", b"\xb0\x00", b"\xc8\x00"]
                        else:
                            f_ishtarmap.seek(int("6b4", 16))
                            f_ishtarmap.write(b"\x69\x6a")

                    if change_id == 9:  # Moss rock R
                        f_ishtarmap.seek(int("7bd", 16))
                        f_ishtarmap.write(b"\x8f")
                        if done:
                            coords[room] = [b"\xd0\x07", b"\xe0\x07", b"\xb0\x00", b"\xc0\x00"]
                        else:
                            f_ishtarmap.seek(int("6bd", 16))
                            f_ishtarmap.write(b"\x8f")

            # Update cursor check ranges
            if coords[room]:
                for i in range(4):
                    patch.seek(int(room_offsets[room], 16) + coord_offsets[i] + rom_offset)
                    patch.write(coords[room][i])

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
        #                                   Plugins
        ##########################################################################
        # Apocalypse Gaia
        if self.w.goal == "Apocalypse Gaia":
            patch.seek(int("98de4",16)+rom_offset)
            patch.write(b"\x80") # Respawn in space
            for pluginfilename in os.listdir(AG_PLUGIN_PATH):
                if pluginfilename[-4:] == ".bin":
                    f_plugin = open(AG_PLUGIN_PATH + pluginfilename, "rb")
                    patch.seek(int(pluginfilename[:6],16) + rom_offset)
                    patch.write(f_plugin.read())
                    f_plugin.close

        ##########################################################################
        #                          Have fun with final text
        ##########################################################################
        superhero_list = []
        superhero_list.append(qt_encode("I must go, my people need me!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("     Up, up, and away!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       Up and atom!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("  It's clobberin' time!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       For Asgard!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("   It's morphin' time!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("    Back in a flash!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("      I am GROOT!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       VALHALLA!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       Go Joes!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("Wonder Twin powers activate!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("    Titans together!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       HULK SMASH!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("        Flame on!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("        By Crom!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       Excelsior!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("Great Caesar's ghost!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("      Odin's beard!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("    I have the power!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("   Avengers assemble!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("To the Bat-pole, Robin!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("        Shazam!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("     Bite me, fanboy.") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("  Hi-yo Silver... away!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("Here I come to save the day!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("By the hoary hosts of Hoggoth!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("    Teen Titans, Go!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       Cowabunga!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("       SPOOOOON!!") + b"\xc3\x00\xc0")
        superhero_list.append(qt_encode("There better be bacon when I get there...") + b"\xc3\x00\xc0")

        # Assign final text box
        rand_idx = random.randint(0, len(superhero_list) - 1)
        patch.seek(int("98ebe", 16) + rom_offset)
        patch.write(superhero_list[rand_idx])

        ##########################################################################
        #                Finalize map headers and return patch data
        ##########################################################################
        f_mapdata.seek(0)
        patch.seek(int("d8000", 16) + rom_offset)
        patch.write(f_mapdata.read())

        return json.dumps(patch.patch_data)

    def generate_spoiler(self) -> str:
        return json.dumps(self.w.spoiler)

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
