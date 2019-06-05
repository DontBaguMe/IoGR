# Python libraries
from shutil import copyfile
import classes
import csv
import binascii
import datetime
import os
import random
import quintet_text as qt

# Local libraries
import quintet_comp

KARA_EDWARDS = 1
KARA_MINE = 2
KARA_ANGEL = 3
KARA_KRESS = 4
KARA_ANKORWAT = 5

GEMS_EASY = 35
GEMS_NORMAL = 40
GEMS_HARD = 50

INV_FULL = "\x5c\x8e\xc9\x80"

# Generate new ROM and prepare it for randomization
def generate_rom(version, rom_offset, rng_seed, rom_path, filename="Illusion of Gaia Randomized",
    mode_str="Normal", goal="Dark Gaia", logic_mode="Completable", statues_reqstr="4",firebird=False):

    # Initiate random seed
    random.seed(rng_seed)

    if mode_str == "Easy":
        mode = 0
    elif mode_str == "Hard":
        mode = 2
    elif mode_str == "Extreme":
        mode = 3
    else:
        mode = 1

    if goal == "Red Jewel Hunt":
        statues_required = 0
    elif statues_reqstr == "Random":
        statues_required = random.randint(0,6)
    else:
        statues_required = int(statues_reqstr)

    folder_dest = os.path.dirname(rom_path) + "\\"
    folder_root = os.getcwd()
    folder = folder_root + "\\bin\\"
    rom_path_new = folder_dest + filename + ".sfc"
    copyfile(rom_path,rom_path_new)

    f = open(rom_path_new,"r+b")

    ##########################################################################
    #                                Sandbox
    ##########################################################################
    # Unleash Firebird!
    if firebird:
        f.seek(int("2cd07",16)+rom_offset)
        f.write("\xad\xd4\x0a\xc9\x02\x00")
        f.seek(int("2cd88",16)+rom_offset)
        f.write("\xad\xd4\x0a\xc9\x02\x00")
        f.seek(int("2ce06",16)+rom_offset)
        f.write("\xad\xd4\x0a\xc9\x02\x00")
        f.seek(int("2ce84",16)+rom_offset)
        f.write("\xad\xd4\x0a\xc9\x02\x00")

    # Sprite for Inca statue?
    #f.seek(int("4fac5",16)+rom_offset)
    #f.write("\x00\x00\x10\x4c\x50\xfb\x84")
    #f.seek(int("4fb50",16)+rom_offset)
    #f.write("\x02\x88\x00\x80\x8e\x02\x8d\x01\x02\x0b\x02\xc0\xdf\xfa\x02\xc1\x02\xBC\x08\x00\x4c\xd0\xfa\x84")  # \x02\x88\x00\x80\x90

    # Get all text boxes in the game
#    f.seek(0)
#    rom = f.read()
#    addr_text = rom.find("\x02\xBF")
#    text_call_addresses = []
#    while addr_text >= 0:
#        text_call_addresses.append(addr_text)
#        addr_text = rom.find("\x02\xBF",addr_text+1)
#
#    #print text_call_addresses
#    for addr in text_call_addresses:
#        bank = int(addr / 65536)
#        f.seek(addr)
#        text_call = binascii.hexlify(rom[addr+2:addr+4])
#        addr_tuple = text_call[2]+text_call[3]+text_call[0]+text_call[1]
#        text_addr = bank*65536 + int(addr_tuple,16)
#        if rom[text_addr] in ["\xd3","\xc1","\xc2","\xce"]:
#            #print text_call, addr_tuple, bank, text_addr
#            print hex(text_addr), qt.get_text(text_addr,f)


    ##########################################################################
    #                            Modify ROM Header
    ##########################################################################
    f.seek(int("ffd1",16)+rom_offset)
    f.write("\x52\x41\x4E\x44\x4F")

    ##########################################################################
    #                           Negate useless switches
    #                 Frees up switches for the randomizer's use
    ##########################################################################
    f.seek(int("48a03",16)+rom_offset)  # Switch 17 - Enter Seth's house
    f.write("\x10")
    f.seek(int("4bca9",16)+rom_offset)  # Switch 18 - Enter Will's house (1/2)
    f.write("\x10")
    f.seek(int("4bccc",16)+rom_offset)  # Switch 18 - Enter Will's house (2/2)
    f.write("\x10")
    f.seek(int("4bcda",16)+rom_offset)  # Switch 19 - Enter Lance's house
    f.write("\x10")
    f.seek(int("4bce8",16)+rom_offset)  # Switch 20 - Enter Erik's house
    f.write("\x10")
    f.seek(int("4be3d",16)+rom_offset)  # Switch 21 - Enter seaside cave
    f.write("\x10")
    f.seek(int("4bcf6",16)+rom_offset)  # Switch 23 - Complete seaside cave events
    f.write("\x10")
    f.seek(int("9bf95",16)+rom_offset)  # Switch 58 - First convo with Lilly
    f.write("\x10")
    f.seek(int("4928a",16)+rom_offset)  # Switch 62 - First convo with Lola (1/2)
    f.write("\x10")
    f.seek(int("49873",16)+rom_offset)  # Switch 62 - First convo with Lola (1/2)
    f.write("\x10")
    f.seek(int("4e933",16)+rom_offset)  # Switch 65 - Hear Elder's voice
    f.write("\x10")
    #f.seek(int("581f2",16)+rom_offset)  # Switch 76 - Enter Gold Ship
    #f.write("\x10")
    f.seek(int("58a29",16)+rom_offset)  # Switch 78 - Talk to Gold Ship queen
    f.write("\x10")
    f.seek(int("4b067",16)+rom_offset)
    f.write("\x10\x00")
    f.seek(int("4b465",16)+rom_offset)
    f.write("\x10\x00")
    f.seek(int("4b8b6",16)+rom_offset)
    f.write("\x10\x00")
    #f.seek(int("5817e",16)+rom_offset)
    #f.write("\x10\x00")
    f.seek(int("686fa",16)+rom_offset)  # Switch 111 - meet Lilly at Seaside Palace
    f.write("\x10")
    f.seek(int("78d76",16)+rom_offset)
    f.write("\x10")
    f.seek(int("78d91",16)+rom_offset)
    f.write("\x10")
    f.seek(int("7d7b1",16)+rom_offset)  # Switch 159 - Mt. Kress on map
    f.write("\x10")

    ##########################################################################
    #                           Update map headers
    ##########################################################################
    f_mapdata = open(folder + "0d8000_mapdata.bin","r+b")
    f.seek(int("d8000",16)+rom_offset)
    f.write(f_mapdata.read())
    f_mapdata.close

    ##########################################################################
    #                        Update treasure chest data
    ##########################################################################
    # Remove fanfares from treasure chests
    f_chests = open(folder + "01afa6_chests.bin","r+b")
    f.seek(int("1afa6",16)+rom_offset)
    f.write(f_chests.read())
    f_chests.close

    # Update item acquisition messages and add messages for new items (29-2f)
    f_acquisition = open(folder + "01fd24_acquisition.bin","r+b")
    f.seek(int("1fd24",16)+rom_offset)
    f.write(f_acquisition.read())
    f_acquisition.close

    ##########################################################################
    #                            Update item events
    #    Adds new items that increase HP, DEF, STR and improve abilities
    ##########################################################################
    # Add pointers for new items @38491
    f.seek(int("38491",16)+rom_offset)
    f.write("\x6f\x9f\x91\x9f\x1d\x88\x3a\x88\x5f\x88\x90\x9d\xd0\x9d")

    # Add start menu descriptions for new items
    f_startmenu = open(folder + "01dabf_startmenu.bin","r+b")
    f.seek(int("1dabf",16)+rom_offset)
    f.write(f_startmenu.read())
    f_startmenu.close

    # Write STR, Psycho Dash, and Dark Friar upgrade items
    # Replaces code for item 05 - Inca Melody @3881d
    f_item05 = open(folder + "03881d_item05.bin","r+b")
    f.seek(int("3881d",16)+rom_offset)
    f.write(f_item05.read())
    f_item05.close

    # Modify Prison Key, now is destroyed when used
    f.seek(int("385d4",16)+rom_offset)
    f.write("\x0a\x17\x0c\x18")
    f.seek(int("385fe",16)+rom_offset)
    f.write("\x02\xd5\x02\x60")

    # Modify Lola's Melody, now is destroyed when used and only works in Itory
    f_item09 = open(folder + "038bf5_item09.bin","r+b")
    f.seek(int("38bf5",16)+rom_offset)
    f.write(f_item09.read())
    f_item09.close
    f.seek(int("38bbc",16)+rom_offset)
    f.write("\x00")
    f.seek(int("38bc1",16)+rom_offset)
    f.write("\x00")

    # Modify code for Memory Melody to heal Neil's memory
    f_item0d = open(folder + "038f17_item0d.bin","r+b")
    f.seek(int("38f17",16)+rom_offset)
    f.write(f_item0d.read())
    f_item0d.close

    # Modify Magic Dust, alters switch set and text
    f.seek(int("393c3",16)+rom_offset)
    f.write("\x8a")

    # Modify Blue Journal, functions as an in-game tutorial
    f.seek(int("3943b",16)+rom_offset)
    f.write("\xf0\x94")
    f.seek(int("39440",16)+rom_offset)
    f.write("\x10\xf2")
    f.seek(int("39445",16)+rom_offset)
    f.write("\x00\xf8")
    f.seek(int("3944a",16)+rom_offset)
    f.write("\x00\xfb")

    f.seek(int("3944e",16)+rom_offset)
    f.write("\xce" + qt.encode("       Welcome to") + "\xcb\xcb" + qt.encode("  Bagu's Super-Helpful"))
    f.write("\xcb" + qt.encode("  In-Game Tutorial!(TM)|"))
    f.write(qt.encode("Whadaya wanna know about?") + "\xcb" + qt.encode(" Beating the Game") + "\xcb")
    f.write(qt.encode(" Exploring the World") + "\xcb" + qt.encode(" What If I'm Stuck?") + "\xca")

    f.seek(int("394f0",16)+rom_offset)
    f.write("\xce" + qt.encode("He closed the journal.") + "\xc0")

    f.seek(int("3f210",16)+rom_offset)
    if goal == "Dark Gaia":
        f.write("\xce" + qt.encode("BEATING THE GAME:       You must do the following two things to beat the game:|"))
        f.write(qt.encode("1. RESCUE KARA          Kara is trapped in a painting! You need Magic Dust to free her.|"))
        f.write(qt.encode("She can be in either Edward's Prison, Diamond Mine, Angel Village, Mt. Temple, or Ankor Wat.|"))
        f.write(qt.encode("You can search for her yourself, or find Lance's Letter to learn where she can be found.|"))
        f.write(qt.encode("Once you find Kara, use the Magic Dust on her portrait to free her.|"))
        f.write(qt.encode("2. GATHER MYSTIC STATUES Each time you play the game, you may be required to gather Mystic Statues.|"))
        f.write(qt.encode("Talk to the teacher in the South Cape classroom to find out which Statues you need.|"))
        f.write(qt.encode("Statue 1 is in the Inca Ruins. You need the Wind Melody, Diamond Block, and both Incan Statues.|"))
        f.write(qt.encode("Statue 2 is in the Sky Garden. You'll need all four Crystal Balls to fight the boss Viper.|"))
        f.write(qt.encode("Statue 3 is in Mu. You need both Statues of Hope and both Rama Statues to fight the Vampires.|"))
        f.write(qt.encode("Statue 4 is in the Great Wall. You need Spin Dash and Dark Friar to face the boss Sand Fanger.|"))
        f.write(qt.encode("Statue 5 is in the Pyramid. You'll need all six Hieroglyphs as well as your father's journal.|"))
        f.write(qt.encode("Statue 6 is at the top of Babel Tower. You'll need the Aura and the Crystal Ring to get to the top.|"))
        f.write(qt.encode("Alternatively, if you collect enough Red Jewels to face Solid Arm, he can also take you there.|"))
        f.write(qt.encode("Once you've freed Kara and gathered the Statues you need, enter any Dark Space and talk to Gaia.|"))
        f.write(qt.encode("She will give you the option to face Dark Gaia and beat the game. Good luck, and have fun!") + "\xc0")
    elif goal == "Red Jewel Hunt":
        f.write("\xce" + qt.encode("BEATING THE GAME:       It's a Red Jewel hunt! The objective is super simple:|"))
        f.write(qt.encode("Find the Red Jewels you need, and talk to the Jeweler. That's it!|"))
        f.write(qt.encode("Check the Jeweler's inventory to find out how many Red Jewels you need to beat the game.|"))
        f.write(qt.encode("Happy hunting!") + "\xc0")

    f.seek(int("3f800",16)+rom_offset)
    f.write("\xce" + qt.encode("EXPLORING THE WORLD:    When you start the game, you only have access to a few locations.|"))
    f.write(qt.encode("As you gain more items, you will be able to visit other continents and access more locations.|"))
    f.write(qt.encode("Here are some of the helpful travel items you can find in the game:|"))
    f.write(qt.encode("- Lola's Letter         If you find this letter, read it and go see Erik in South Cape.|"))
    f.write(qt.encode("- The Teapot            If you use the Teapot in the Moon Tribe camp, you can travel by Sky Garden.|"))
    f.write(qt.encode("- Memory Melody         Play this melody in Neil's Cottage, and he'll fly you in his airplane.|"))
    f.write(qt.encode("- The Will              Show this document to the stable masters in either Watermia or Euro.|"))
    f.write(qt.encode("- The Large Roast       Give this to the hungry child in the Natives' Village.|"))
    f.write(qt.encode("If you're ever stuck in a location, find a Dark Space. Gaia can always return you to South Cape.") + "\xc0")

    f.seek(int("3fb00",16)+rom_offset)
    f.write("\xce" + qt.encode("WHAT IF I'M STUCK?      There are a lot of item locations in this game! It's easy to get stuck.|"))
    f.write(qt.encode("Here are some resources that might help you:|"))
    f.write(qt.encode("- Video Tutorial        Search YouTube for a video guide of this randomizer.|"))
    f.write(qt.encode("- Ask the Community     Find the IoGR community on Discord! Someone will be happy to help you.|"))
    if mode == 0:
        f.write(qt.encode("- In-Game Tracker       Enter the east-most house in South Cape to check your collection rate.|"))
    f.write(qt.encode("- Check the Spoiler Log Every seed comes with a detailed list of where every item can be found.") + "\xc0")

    # Modify Lance's Letter
    # Prepare it to spoil Kara location
    f_item16 = open(folder + "03950c_item16.bin","r+b")
    f.seek(int("3950c",16)+rom_offset)
    f.write(f_item16.read())
    f_item16.close

    # Modify Teapot
    # Now activates in Moon Tribe camp instead of Euro
    f_item19 = open(folder + "03983d_item19.bin","r+b")
    f.seek(int("3983d",16)+rom_offset)
    f.write(f_item19.read())
    f_item19.close

    # Modify Black Glasses, now permanently worn and removed from inventory when used
    f.seek(int("39981",16)+rom_offset)
    f.write("\x8a\x99\x02\xcc\xf5\x02\xd5\x1c\x60\xd3\x42\x8e\x8e\x8b\x8d\x84")
    f.write("\xa3\xa3\xac\x88\x8d\xa4\x84\x8d\xa3\x88\x85\x88\x84\xa3\x4f\xc0")

    # Modify Aura, now unlocks Shadow's form when used
    f.seek(int("39cdc",16)+rom_offset)
    f.write("\x02\xbf\xe4\x9c\x02\xcc\xb4\x60\xd3")
    f.write("\xd6\x4c\x85\x8e\xa2\x8c\xac\xa5\x8d\x8b\x8e\x82\x8a\x84\x83\x4f\xc0")

    # Write 2 Jewel and 3 Jewel items; Lola's Letter now teaches Morse Code
    # Replaces and modifies code for item 25 - Lola's Letter @39d09
    f_item25 = open(folder + "039d09_item25.bin","r+b")
    f.seek(int("39d09",16)+rom_offset)
    f.write(f_item25.read())
    f_item25.close

    # Have fun with text in Item 26 (Father's Journal)
    f.seek(int("39ea8",16)+rom_offset)
    f.write(qt.encode("It reads: ") + "\x2d" + qt.encode("He who is ") + "\xcb" + qt.encode("valiant and pure of spirit...") + "\xcf\x2d")
    f.write(qt.encode("... may find the Holy Grail in the Castle of... Aauugghh") + "\x2e\xcf")
    f.write(qt.encode("Here a page is missing.") + "\xc0")

    # Modify Crystal Ring, now permanently worn and removed from inventory when used
    f.seek(int("39f32",16)+rom_offset)
    f.write("\x3b\x9f\x02\xcc\x3e\x02\xd5\x27\x60\xd3\x41\x8b")
    f.write("\x88\x8d\x86\xac\x81\x8b\x88\x8d\x86\x2a\xc0")

    # Write HP and DEF upgrade items; make the Apple non-consumable
    # Replaces and modifies code for item 28 - Apple @39f5d
    f_item28 = open(folder + "039f5d_item28.bin","r+b")
    f.seek(int("39f5d",16)+rom_offset)
    f.write(f_item28.read())
    f_item28.close

    # Update herb HP fill based on difficulty
    f.seek(int("3889f",16)+rom_offset)
    if mode == 0:           # Easy mode = full HP
        f.write("\x28")
    elif mode == 2:         # Hard mode = fill 4 HP
        f.write("\x04")
    elif mode == 3:         # Extreme mode = fill 2 HP
        f.write("\x02")

    # Update HP jewel HP fill based on difficulty
    f.seek(int("39f7a",16)+rom_offset)
    if mode == 0:         # Easy mode = full HP
        f.write("\x28")

    # Update sprites for new items - first new item starts @108052, 7 new items
    # Points all items to unused sprite for item 4c ("76 83" in address table)
    f.seek(int("108052",16)+rom_offset)
    f.write("\x76\x83\x76\x83\x76\x83\x76\x83\x76\x83\x76\x83\x76\x83")

    # Update item removal restriction flags
    f.seek(int("1e12a",16)+rom_offset)
    f.write("\x9c\xff\x97\x27\xb0\x01")

    ##########################################################################
    #                  Update overworld map movement scripts
    #   Removes overworld animation and allows free travel within continents
    ##########################################################################
    # Update map choice scripts
    f_mapchoices = open(folder + "03b401_mapchoices.bin","r+b")
    f.seek(int("3b401",16)+rom_offset)
    f.write(f_mapchoices.read())
    f_mapchoices.close

    # Update map destination array
    f_mapdest = open(folder + "03b955_mapdest.bin","r+b")
    f.seek(int("3b955",16)+rom_offset)
    f.write(f_mapdest.read())
    f_mapdest.close

    ##########################################################################
    #                   Rewrite Red Jewel acquisition event
    #      Makes unique code for each instance (overwrites unused code)
    ##########################################################################
    # Fill block with new item acquisition code (16 items)
    f_redjewel = open(folder + "00f500_redjewel.bin","r+b")
    f.seek(int("f500",16)+rom_offset)
    f.write(f_redjewel.read())
    f_redjewel.close

    # Update event table instances to point to new events
    # New pointers include leading zero byte to negate event parameters
    f.seek(int("c8318",16)+rom_offset)  # South Cape: bell tower
    f.write("\x00\x00\xf5\x80")
    f.seek(int("c837c",16)+rom_offset)  # South Cape: Lance's house
    f.write("\x00\x80\xf5\x80")
    f.seek(int("c8ac0",16)+rom_offset)  # Underground Tunnel: barrel
    f.write("\x00\x00\xf6\x80")
    f.seek(int("c8b50",16)+rom_offset)  # Itory Village: logs
    f.write("\x00\x80\xf6\x80")
    f.seek(int("c9546",16)+rom_offset)  # Diamond Coast: jar
    f.write("\x00\x00\xf7\x80")
    f.seek(int("c97a6",16)+rom_offset)  # Freejia: hotel
    f.write("\x00\x80\xf7\x80")
    f.seek(int("caf60",16)+rom_offset)  # Angel Village: dance hall
    f.write("\x00\x00\xf8\x80")
    f.seek(int("cb3a6",16)+rom_offset)  # Angel Village: Ishtar's room
    f.write("\x00\x80\xf8\x80")
    f.seek(int("cb563",16)+rom_offset)  # Watermia: west Watermia
    f.write("\x00\x00\xf9\x80")
    f.seek(int("cb620",16)+rom_offset)  # Watermia: gambling house
    f.write("\x00\x80\xf9\x80")
    f.seek(int("cbf55",16)+rom_offset)  # Euro: behind house
    f.write("\x00\x00\xfa\x80")
    f.seek(int("cc17c",16)+rom_offset)  # Euro: slave room
    f.write("\x00\x80\xfa\x80")
    f.seek(int("ccb14",16)+rom_offset)  # Natives' Village: statue room
    f.write("\x00\x00\xfb\x80")
    f.seek(int("cd440",16)+rom_offset)  # Dao: east Dao
    f.write("\x00\x80\xfb\x80")
    f.seek(int("cd57e",16)+rom_offset)  # Pyramid: east entrance
    f.write("\x00\x00\xfc\x80")
    f.seek(int("ce094",16)+rom_offset)  # Babel: pillow
    f.write("\x00\x80\xfc\x80")

    ##########################################################################
    #                         Modify South Cape events
    ##########################################################################
    # Overwrite opening cutscene, set initial progression flags instead
    # TEMPORARILY SETS KARA RESCUE (0x8A) TO TRUE FOR TESTING PURPOSES
    f_switches = open(folder + "048a94_switches.bin","r+b")
    f.seek(int("48a94",16)+rom_offset)
    f.write(f_switches.read())
    f_switches.close

    # Force fisherman to always appear on E side of docks, and fix inventory full
    f.seek(int("48377",16)+rom_offset)
    f.write("\x02\xd0\x10\x01\xaa\x83")
    f.seek(int("48475",16)+rom_offset)
    f.write(INV_FULL)

    # Disable Lola Melody cutscene
    f.seek(int("49985",16)+rom_offset)
    f.write("\x6b")

    # Set flag 35 at Lola Melody acquisition
    f.seek(int("499dc",16)+rom_offset)
    f.write("\xeb\x99\x02\xbf\xe5\x9b\x02\xd4\x09\xf0\x99")
    f.write("\x02\xcc\x35\x6b\x02\xbf\x94\x9d\x6b")
    f.write(INV_FULL)

    # Erik in Seaside Cave allows player to use Lola's Letter to travel by sea
    f_seaside = open(folder + "04b9a5_seaside.bin","r+b")
    f.seek(int("4b9a5",16)+rom_offset)
    f.write(f_seaside.read())
    f_seaside.close
    f.seek(int("4b8b6",16)+rom_offset)
    f.write("\x10\x01\x62")
    f.seek(int("4b96a",16)+rom_offset)
    f.write("\xa5")

    # Various NPCs can give you a tutorial
    f_tutorial = open(folder + "04fb50_tutorial.bin","r+b")
    f.seek(int("4fb50",16)+rom_offset)
    f.write(f_tutorial.read())
    f_tutorial.close
    f.seek(int("49231",16)+rom_offset)   # NPC in front of school
    f.write("\x50\xfb")

    # Turns house in South Cape into item-tracking overworld map (Easy only)
    if mode == 0:
        f.seek(int("18480",16)+rom_offset)
        f.write("\x07\x90\x00\xd0\x03\x00\x00\x44")
        f.seek(int("1854e",16)+rom_offset)
        f.write("\x00\x3e\x40\x02")
        f.seek(int("c846c",16)+rom_offset)
        f.write("\x00\x01\x00\x00\xde\x86\x00\xFF\xCA")
        # Item count text box
        # Put current count in $a48, total in $a4c
        f.seek(int("6dd30",16)+rom_offset)
        f.write("\xF8\xAD\x58\x0A\x18\x69\x01\x00\x8D\x58\x0A\xD8\x60")
        f.seek(int("6dd40",16)+rom_offset)
        f.write("\xd3" + qt.encode("You have collected ") + "\xc6\x02\x00\x58\x0a\xcb")
        f.write(qt.encode("of the ") + "\xc6\x02\x00\x5c\x0a\xac" + qt.encode("total items"))
        f.write("\xcb" + qt.encode("in this area.") + "\xc9\x18\xc0")

        f_collectioncheck = open(folder + "06de00_collectioncheck.bin","r+b")
        f.seek(int("6de00",16)+rom_offset)
        f.write(f_collectioncheck.read())
        f_collectioncheck.close

    ##########################################################################
    #                       Modify Edward's Castle events
    ##########################################################################
    # Shorten Edward conversation
    f.seek(int("4c3d6",16)+rom_offset)
    f.write("\x06\xc4")
    f_edward = open(folder + "04c4fb_edward.bin","r+b")
    f.seek(int("4c4fb",16)+rom_offset)
    f.write(f_edward.read())
    f_edward.close

    f.seek(int("4c4fb",16)+rom_offset)
    f.write("\xd3")

    # Talking to Edward doesn't soft lock you
    f.seek(int("4c746",16)+rom_offset)
    f.write("\x10")

    # Move guard to allow roast location get
    f_castleguard = open(folder + "04d1a0_castleguard.bin","r+b")
    f.seek(int("4d1a0",16)+rom_offset)
    f.write(f_castleguard.read())
    f_castleguard.close
    f.seek(int("c8551",16)+rom_offset)
    f.write("\x10")

    #  Update Large Roast event
    f.seek(int("4d0da",16)+rom_offset)
    f.write("\x02\xc0\xe1\xd0\x02\xc1\x6b\x02\xd0\x46\x00\xe9\xd0\x02\xe0\x02")
    f.write("\xd4\x0a\xf6\xd0\x02\xcc\x46\x02\xbf\x41\xd1\x6b")
    f.write(INV_FULL)

    # Fix hidden guard text box
    f.seek(int("4c297",16)+rom_offset)
    f.write("\xc0")
    f.seek(int("4c21b",16)+rom_offset)
    f.write(INV_FULL)

    ##########################################################################
    #                   Modify Edward's Prison/Tunnel events
    ##########################################################################
    # Skip long cutscene in prison
    f.seek(int("4d209",16)+rom_offset)
    f.write("\x34\xd2")
    f.seek(int("4d234",16)+rom_offset)
    f.write("\x02\xd0\x23\x00\xcf\xd2\x02\xe0")
    f.seek(int("4d335",16)+rom_offset)
    f.write("\x6b")

    # Move Dark Space, allows player to exit area without key
    # Set new X/Y coordinates in exit table
    f.seek(int("18614",16)+rom_offset)
    f.write("\x12\x07")
    # Set new X/Y coordinates in event table
    f.seek(int("C8635",16)+rom_offset)
    f.write("\x12\x08")

    # Progression triggers when Lilly is with you
    f.seek(int("9aa45",16)+rom_offset)
    f.write("\x6f\x00")
    f.seek(int("9aa4b",16)+rom_offset)
    f.write("\x02")
    f.seek(int("9be74",16)+rom_offset)
    f.write("\xd7\x18")

    ##########################################################################
    #                            Modify Itory events
    ##########################################################################
    # Lilly event becomes Lola's Melody handler
    f_itory = open(folder + "04e2a3_itory.bin","r+b")
    f.seek(int("4e2a3",16)+rom_offset)
    f.write(f_itory.read())
    f_itory.close

    # Lilly now joins if you give her the Necklace
    f_lilly = open(folder + "04e5ff_lilly.bin","r+b")
    f.seek(int("4e5ff",16)+rom_offset)
    f.write(f_lilly.read())
    f_lilly.close
    f.seek(int("4e5a6",16)+rom_offset)
    f.write("\x6f")
    f.seek(int("4e5ac",16)+rom_offset)
    f.write("\xff\xe5\x02\x0b\x6b")

    # Shorten Inca Statue get
    f.seek(int("4f37b",16)+rom_offset)
    f.write("\x02\xbf\x8d\xf3\x6b")

    # For elder to always give spoiler
    f.seek(int("4e933",16)+rom_offset)
    f.write("\x10\x01")
    f.seek(int("4e97a",16)+rom_offset)
    f.write("\x02\xbf\xff\xe9\x6b")
#    f.seek(int("4e988",16)+rom_offset)
#    f.write("\x8a\xe9")

    ##########################################################################
    #                          Modify Moon Tribe events
    ##########################################################################
    # Allows player to use Teapot to travel by Sky Garden
    f_moontribe = open(folder + "09d11e_moontribe.bin","r+b")
    f.seek(int("9d11e",16)+rom_offset)
    f.write(f_moontribe.read())
    f_moontribe.close

    # Lilly event serves as an overworld exit
    f.seek(int("4f441",16)+rom_offset)
    f.write("\x00\x00\x30\x02\x45\x14\x1c\x17\x1d\x4d\xf4\x6b")
    f.write("\x02\x40\x00\x04\x54\xf4\x6b\x02\x66\x90\x00\x60\x02\x01\x02\xC1\x6b")

    # Shorten Inca Statue get
    f.seek(int("4fae7",16)+rom_offset)
    f.write("\x02\xbf\xf9\xfa\x6b")

    ##########################################################################
    #                          Modify Inca events
    ##########################################################################
    # Put Gold Ship captain at Inca entrance
    f.seek(int("c8c9c",16)+rom_offset)
    f.write("\x19\x1c\x00\x4e\x85\x85\x00")

    ##########################################################################
    #                          Modify Gold Ship events
    ##########################################################################
    # Move Seth from deserted ship to gold ship, allows player to acquire item
    # Write pointer to Seth event in new map
    f.seek(int("c945c",16)+rom_offset)
    f.write("\x0b\x24\x00\x3e\x96\x85\x00\xff\xca")
    f.seek(int("c805a",16)+rom_offset)
    f.write("\x65")
    # Modify Seth event to ignore switch conditions
    f.seek(int("59643",16)+rom_offset)
    f.write("\x10\x00")
    # Add in inventory full text
    f.seek(int("59665",16)+rom_offset)
    f.write(INV_FULL)

    # Entering Gold Ship doesn't lock out Castoth
    f.seek(int("58188",16)+rom_offset)
    f.write("\x02\xc1\x02\xc1")
    f.seek(int("18a09",16)+rom_offset)
    f.write("\xd0\x00\x40\x02\x03")

    # Have ladder NPC move aside only if Mystic Statue has been acquired
    f.seek(int("583cb",16)+rom_offset)
    f.write("\x10")

    # Modify queen switches
    f.seek(int("58a04",16)+rom_offset)
    f.write("\x10\x00")
    f.seek(int("58a1f",16)+rom_offset)
    f.write("\x10")

    # Have crow's nest NPC warp directly to Diamond Coast
    # Also checks for Castoth being defeated
    f_goldship = open(folder + "0584a9_goldship.bin","r+b")
    f.seek(int("584a9",16)+rom_offset)
    f.write(f_goldship.read())
    f_goldship.close

    # Sleeping sends player to Diamond Coast
    f.seek(int("586a3",16)+rom_offset)
    f.write("\x02\x26\x30\x48\x00\x20\x00\x03\x00\x21")

    ##########################################################################
    #                        Modify Diamond Coast events
    ##########################################################################
    # Kara event serves as an overworld exit
    f.seek(int("5aa9e",16)+rom_offset)
    f.write("\x00\x00\x30\x02\x45\x03\x00\x06\x01\xaa\xaa\x6b")
    f.write("\x02\x40\x00\x08\xb1\xaa\x6b\x02\x66\x50\x02\x50\x03\x07\x02\xC1\x6b")

    ##########################################################################
    #                           Modify Freejia events
    ##########################################################################
    # Trash can 1 gives you an item instead of a status upgrade
    # NOTE: This cannibalizes the following event @5cfbc (locked door)
    f_freejia = open(folder + "05cf85_freejia.bin","r+b")
    f.seek(int("5cf85",16)+rom_offset)
    f.write(f_freejia.read())
    f_freejia.close

    # Give full inventory text to trash can 2
    f.seek(int("5cf44",16)+rom_offset)
    f.write(INV_FULL)

    # Redirect event table to bypass deleted event
    # Changes locked door to a normal door
    f.seek(int("c95bb",16)+rom_offset)
    f.write("\xf3\xc5\x80")

    # Update NPC dialogue to acknowledge change
    f.seek(int("5c331",16)+rom_offset)
    f.write("\x42\xa2\x80\xa0\x2b\xac\x48\xac\xd6\xae\xa4\x87\x84\xac\xd7\x58\xcb\xa5")
    f.write("\x8d\x8b\x8e\x82\x8a\x84\x83\xac\x80\x86\x80\x88\x8d\x2a\x2a\x2a\xc0")

    # Add inventory full option to Creepy Guy event
    f.seek(int("5b6df",16)+rom_offset)
    f.write(INV_FULL)

    # Alter laborer text
    f.seek(int("5bfdb",16)+rom_offset)
    f.write("\xde\xbf")

    # Have some fun with snitch item text
    f.seek(int("5b8bc",16)+rom_offset)
    f.write("\x62")
    f.seek(int("5b925",16)+rom_offset)
    f.write("\x88\xa4\x84\x8c\x2a\xcb\xac\x69\x84\xa3\x2b\xac\x48\x0e\x8c\xac\x80\xac\x81")
    f.write("\x80\x83\xac\xa0\x84\xa2\xa3\x8e\x8d\xcb\xac\x63\x8d\x88\xa4\x82\x87\x84\xa3")
    f.write("\xac\x86\x84\xa4\xac\xa3\xa4\x88\xa4\x82\x87\x84\xa3\x2b\xac\xa9\x8e\xca")

    ##########################################################################
    #                        Modify Diamond Mine events
    ##########################################################################
    # Trapped laborer gives you an item instead of sending Jewels to Jeweler
    f.seek(int("5d739",16)+rom_offset)
    f.write("\x4c\x5d\xd8\x85")
    f_trappedlaborer = open(folder + "05d7e2_trappedlaborer.bin","r+b")
    f.seek(int("5d7e2",16)+rom_offset)
    f.write(f_trappedlaborer.read())
    f_trappedlaborer.close

    # Shorten morgue item get
    f.seek(int("5d4d8",16)+rom_offset)
    f.write("\x02\xbf\xeb\xd4\x02\xe0")

    # Cut out Sam's song
    f.seek(int("5d24f",16)+rom_offset)
    f.write("\x6b")

    ##########################################################################
    #                       Modify Neil's Cottage events
    ##########################################################################
    # Allow travel by plane with the Memory Melody
    f_neilscottage = open(folder + "05d89a_neilscottage.bin","r+b")
    f.seek(int("5d89a",16)+rom_offset)
    f.write(f_neilscottage.read())
    f_neilscottage.close

    # Invention event serves as an overworld exit
    f.seek(int("5e305",16)+rom_offset)
    f.write("\x00\x00\x30\x02\x45\x07\x0d\x0a\x0e\x11\xe3\x6b")
    f.write("\x02\x40\x00\x04\x18\xe3\x6b\x02\x66\x70\x02\x70\x02\x07\x02\xC1\x6b")

    ##########################################################################
    #                            Modify Nazca events
    ##########################################################################
    # Speedup warp sequence to Sky Garden
    f_nazca = open(folder + "05e647_nazca.bin","r+b")
    f.seek(int("5e647",16)+rom_offset)
    f.write(f_nazca.read())
    f_nazca.close

    # Allow exit to world map
    #f.seek(int("5e647",16))
    #f.write("\x32\x00\x10\x02\x0b\x02\xc0\xad\xe6\x02\xc1\x6b")
    f.seek(int("5e80c",16))
    f.write("\x02\x66\x10\x03\x90\x02\x07\x02\xC1\x6B")

    ##########################################################################
    #                          Modify Sky Garden events
    ##########################################################################
    # Allow travel from Sky Garden to other locations
    f_skygarden = open(folder + "05f356_skygarden.bin","r+b")
    f.seek(int("5f356",16)+rom_offset)
    f.write(f_skygarden.read())
    f_skygarden.close

    # Instant warp to Seaside Palace if Viper is defeated
    f.seek(int("acecb",16)+rom_offset)
    f.write("\x01\x02\x26\x5a\x90\x00\x70\x00\x83\x00\x14\x02\xc1\x6b")

    ##########################################################################
    #                       Modify Seaside Palace events
    ##########################################################################
    # Add exit from Mu passage to Angel Village @191de
    f.seek(int("191de",16)+rom_offset)
    f.write("\x04\x06\x02\x03\x69\xa0\x02\x38\x00\x00\x00\x13")   # Temporarily put exit one tile south
    #f.write("\x04\x05\x02\x03\x69\xa0\x02\x38\x00\x00\x00\x13")  # Change to this if map is ever updated

    # Replace Mu Passage map with one that includes a door to Angel Village
    f_mupassage = open(folder + "1e28a5_mupassage.bin","r+b")
    f.seek(int("1e28a5",16)+rom_offset)
    f.write(f_mupassage.read())
    f_mupassage.close

    # Shorten NPC item get
    f.seek(int("68b01",16)+rom_offset)
    f.write("\x6b")

    # Purification event won't softlock if you don't have Lilly
    f.seek(int("69406",16)+rom_offset)
    f.write("\x10")
    f.seek(int("6941a",16)+rom_offset)
    f.write("\x01\x02\xc1\x02\xc1")

    # Remove Lilly text when Mu door opens
    f.seek(int("39174",16)+rom_offset)
    f.write("\x60")
    f.seek(int("391d7",16)+rom_offset)
    f.write("\xc0")

    # Allow player to open Mu door from the back
    f_mudoor = open(folder + "069739_mudoor.bin","r+b")
    f.seek(int("69739",16)+rom_offset)
    f.write(f_mudoor.read())
    f_mudoor.close

    ##########################################################################
    #                             Modify Mu events
    ##########################################################################
    # Add "inventory full" option to Statue of Hope items
    f.seek(int("698cd",16)+rom_offset)
    f.write(INV_FULL)

    # Shorten Statue of Hope get
    f.seek(int("698c0",16)+rom_offset)
    f.write("\x02\xbf\xd2\x98\x6b")
    f.seek(int("69968",16)+rom_offset)
    f.write("\x02\xbf\x75\x99\x6b")

    # Shorten Rama statue event
    f.seek(int("69e50",16)+rom_offset)
    f.write("\x10")
    f.seek(int("69f26",16)+rom_offset)
    f.write("\x00")

    # Spirits in Rama statue room can't lock you
    f.seek(int("6a07a",16)+rom_offset)
    f.write("\x6b")
    f.seek(int("6a082",16)+rom_offset)
    f.write("\x6b")
    f.seek(int("6a08a",16)+rom_offset)
    f.write("\x6b")
    f.seek(int("6a092",16)+rom_offset)
    f.write("\x6b")
    f.seek(int("6a09a",16)+rom_offset)
    f.write("\x6b")
    f.seek(int("6a0a2",16)+rom_offset)
    f.write("\x6b")


    # Move exits around to make Vampires required for Statue
    f.seek(int("193ea",16)+rom_offset)
    f.write("\x5f\x80\x00\x50\x00\x03\x00\x44")
    f.seek(int("193f8",16)+rom_offset)
    f.write("\x65\xb8\x00\x80\x02\x03\x00\x44")
    f.seek(int("69c62",16)+rom_offset)
    f.write("\x67\x78\x01\xd0\x01\x80\x01\x22")
    f.seek(int("6a4c9",16)+rom_offset)
    f.write("\x02\x26\x66\xf8\x00\xd8\x01\x00\x00\x22\x02\xc1\x6b")

    ##########################################################################
    #                       Modify Angel Village events
    ##########################################################################
    # Add exit from Angel Village to Mu passage @1941a
    f.seek(int("1941a",16)+rom_offset)
    f.write("\x2a\x05\x01\x01\x5e\x48\x00\x90\x00\x01\x00\x14")   # Temporarily put exit one tile south
    #f.write("\x2a\x05\x01\x01\x5e\x48\x00\x80\x00\x01\x00\x14")  # Change to this if map is ever updated

    # Update sign to read "Passage to Mu"
    f_angelsign = open(folder + "06ba36_angelsign.bin","r+b")
    f.seek(int("6ba36",16)+rom_offset)
    f.write(f_angelsign.read())
    f_angelsign.close

    # Entering this area clears your enemy defeat count
    f.seek(int("6bff7",16)+rom_offset)
    f.write("\x00\x00\x30\x02\x40\x01\x0F\x01\xC0\x6b")
    f.write("\xA0\x00\x00\xA9\x00\x00\x99\x80\x0A\xC8\xC8\xC0\x20\x00\xD0\xF6\x02\xE0")

    # Insert new arrangement for map 109, takes out rock to prevent spin dash softlock
    f_angelmap = open(folder + "1a5a37_angelmap.bin","r+b")
    f.seek(int("1a5a37",16)+rom_offset)
    f.write(f_angelmap.read())
    f_angelmap.close

    # Ishtar's game never closes
    f.seek(int("6d9fc",16)+rom_offset)
    f.write("\x10")
    f.seek(int("6cede",16)+rom_offset)
    f.write("\x9c\xa6\x0a\x6b")
    f.seek(int("6cef6",16)+rom_offset)
    f.write("\x40\x86\x80\x88\x8d\x4f\xc0")

    ##########################################################################
    #                           Modfy Watermia events
    ##########################################################################
    # Allow for travel from  Watermia to Euro
    # Update address pointer
    f.seek(int("78544",16)+rom_offset)
    f.write("\x69")

    # Update event address pointers
    f_watermia1 = open(folder + "078569_watermia1.bin","r+b")
    f.seek(int("78569",16)+rom_offset)
    f.write(f_watermia1.read())
    f_watermia1.close

    # Change textbox contents
    f_watermia2 = open(folder + "0786c1_watermia2.bin","r+b")
    f.seek(int("786c1",16)+rom_offset)
    f.write(f_watermia2.read())
    f_watermia2.close

    # Russian Glass NPC just gives you the item
    f_russianglass = open(folder + "079237_russianglass.bin","r+b")
    f.seek(int("79237",16)+rom_offset)
    f.write(f_russianglass.read())
    f_russianglass.close

    # Fix Lance item get text
    f.seek(int("7ad28",16)+rom_offset)
    f.write(INV_FULL)

    ##########################################################################
    #                          Modify Great Wall events
    ##########################################################################
    # Rewrite Necklace Stone acquisition event
    # Fill block with new item acquisition code (2 items)
    f_necklace = open(folder + "07b59e_necklace.bin","r+b")
    f.seek(int("7b59e",16)+rom_offset)
    f.write(f_necklace.read())
    f_necklace.close

    # Update event table instance to point to new events
    # New pointers include leading zero byte to negate event parameters
    f.seek(int("cb822",16)+rom_offset)  # First stone, map 130
    f.write("\x00\x9e\xb5\x87")
    f.seek(int("cb94a",16)+rom_offset)  # Second stone, map 131
    f.write("\x00\xfe\xb5\x87")

    # Entering wrong door in 2nd map area doesn't softlock you
    f.seek(int("19a4c",16)+rom_offset)
    f.write("\x84")

    # Exit after Sand Fanger takes you back to start
    f.seek(int("19c84",16)+rom_offset)
    f.write("\x82\x10\x00\x90\x00\x07\x00\x18")

    ##########################################################################
    #                            Modify Euro events
    ##########################################################################
    # Allow travel from Euro to Watermia
    # Update event address pointers
    f_euro1 = open(folder + "07c432_euro1.bin","r+b")
    f.seek(int("7c432",16)+rom_offset)
    f.write(f_euro1.read())
    f_euro1.close
    # Change textbox contents
    f_euro2 = open(folder + "07c4d0_euro2.bin","r+b")
    f.seek(int("7c4d0",16)+rom_offset)
    f.write(f_euro2.read())
    f_euro2.close
    f.seek(int("7c482",16)+rom_offset)
    f.write(qt.encode("A moose once bit my sister.",True))

    # Neil in Euro
    f_euroneil = open(folder + "07e398_euroneil.bin","r+b")
    f.seek(int("7e398",16)+rom_offset)
    f.write(f_euroneil.read())
    f_euroneil.close
    f.seek(int("7e37f",16)+rom_offset)
    f.write("\x14\x00")
    f.seek(int("7e394",16)+rom_offset)
    f.write("\x10\x00")

    # Hidden house replaces STR upgrade with item acquisition
    f_euroitem = open(folder + "07e517_euroitem.bin","r+b")
    f.seek(int("7e517",16)+rom_offset)
    f.write(f_euroitem.read())
    f_euroitem.close

    # Speed up store line
    f.seek(int("7d5e1",16)+rom_offset)
    f.write("\x00\x01")

    # Change vendor event, allows for only one item acquisition
    # Note: this cannibalizes the following event
    f.seek(int("7c0a7",16)+rom_offset)
    f.write("\x02\xd0\x9a\x01\xba\xc0\x02\xd4\x28\xbf\xc0\x02\xcc\x9a")
    f.write("\x02\xbf\xf3\xc0\x6b\x02\xbf\xdd\xc0\x6b")
    f.write(INV_FULL)
    # Change pointer for cannibalized event
    f.seek(int("7c09b",16)+rom_offset)
    f.write("\xc4")

    # Store replaces status upgrades with item acquisition
    f.seek(int("7cd03",16)+rom_offset)         # HP upgrade
    f.write("\x02\xd0\xf0\x01\x32\xcd\x02\xc0\x10\xcd\x02\xc1\x6b")
    f.write("\x02\xd4\x29\x20\xcd\x02\xcc\xf0\x02\xbf\x39\xcd\x02\xe0")
    f.seek(int("7cdf7",16)+rom_offset)         # Dark Friar upgrade
    f.write("\x02\xd4\x2d\x05\xce\x02\xcc\xf1\x02\xbf\x28\xce\x02\xe0")
    f.write("\x02\xbf\x3e\xce\x6b")

    # Old men text no longer checks for Teapot
    f.seek(int("7d60a",16)+rom_offset)
    f.write("\x14\xd6")
    f.seek(int("7d7a5",16)+rom_offset)
    f.write("\xbd\xd7")

    # Various NPC dialogue
    f.seek(int("7d6db",16)+rom_offset)
    f.write("\x2A\xD0\xC8\xC9\x1E\xC2\x0B\xC2\x03" + qt.encode("It could be carried by an African swallow!"))
    f.write("\xCF\xC2\x03\xC2\x04" + qt.encode("Oh yeah, an African swallow maybe, but not a European swallow, that's my point!") + "\xc0")
    f.seek(int("7d622",16)+rom_offset)
    f.write(qt.encode("Rofsky: Wait a minute, supposing two swallows carried it together?...") + "\xc0")
    f.seek(int("7c860",16)+rom_offset)
    f.write("\xce" + qt.encode("Nobody expects the Spanish Inquisition!") + "\xc0")
    f.seek(int("7c142",16)+rom_offset)
    f.write(qt.encode("I am no longer infected.",True))
    f.seek(int("7c160",16)+rom_offset)
    f.write(qt.encode("My hovercraft is full of eels.",True))
    f.seek(int("7c182",16)+rom_offset)
    f.write(qt.encode("... w-i-i-i-i-ith... a herring!!",True))
    f.seek(int("7c1b6",16)+rom_offset)
    f.write(qt.encode("It's only a wafer-thin mint, sir...",True))
    f.seek(int("7c1dc",16)+rom_offset)
    f.write("\xd3" + qt.encode("The mill's closed. There's no more work. We're destitute.|"))
    f.write(qt.encode("I've got no option but to sell you all for scientific experiments.") + "\xc0")
    f.seek(int("7c3d4",16)+rom_offset)
    f.write(qt.encode("You're a looney.",True))

    ##########################################################################
    #                        Modify Native Village events
    ##########################################################################
    # Native can guide you to Dao if you give him the roast
    f_natives = open(folder + "088fc4_natives.bin","r+b")
    f.seek(int("88fc4",16)+rom_offset)
    f.write(f_natives.read())
    f_natives.close

    # Change event pointers for cannibalized NPC code
    f.seek(int("cca93",16)+rom_offset)
    f.write("\x88\x8f\x88")

    ##########################################################################
    #                         Modify Ankor Wat events
    ##########################################################################
    # Modify Gorgon Flower event, make it a simple item get
    f_ankorwat1 = open(folder + "089abf_ankorwat.bin","r+b")
    f.seek(int("89abf",16)+rom_offset)
    f.write(f_ankorwat1.read())
    f_ankorwat1.close

    # Shorten black glasses get
    f.seek(int("89fa9",16)+rom_offset)
    f.write("\x02\xe0")

    # Bright room looks at switch 4f rather than equipment
    f_ankorwat2 = open(folder + "089a31_ankorwat.bin","r+b")
    f.seek(int("89a31",16)+rom_offset)
    f.write(f_ankorwat2.read())
    f_ankorwat2.close

    ##########################################################################
    #                            Modify Dao events
    ##########################################################################
    # Snake game grants an item instead of sending Jewels to the Jeweler
    f_snakegame = open(folder + "08b010_snakegame.bin","r+b")
    f.seek(int("8b010",16)+rom_offset)
    f.write(f_snakegame.read())
    f_snakegame.close

    # Neil in Dao
    f_daoneil = open(folder + "08a5bd_daoneil.bin","r+b")
    f.seek(int("8a5bd",16)+rom_offset)
    f.write(f_daoneil.read())
    f_daoneil.close
    f.seek(int("8a5b3",16)+rom_offset)
    f.write("\x14\x00")

    # Modify two-item acquisition event
    f.seek(int("8b1bb",16)+rom_offset)
    f.write("\x6b")
    f.seek(int("8b21a",16)+rom_offset)
    f.write("\xd3\x69\x8e\xa5\xac\x86\x8e\xa4\xac\x22\xac\x88\xa4\x84\x8c\xa3\x4f\xc0")

    # Spirit appears only after you get the Mystic Statue
    f.seek(int("980cb",16)+rom_offset)
    f.write("\x4c\xb0\xf6")
    f.seek(int("9f6b0",16)+rom_offset)
    f.write("\x02\xd0\xf4\x01\xd1\x80\x02\xd1\x79\x01\x01\xd1\x80\x02\xe0")

    ##########################################################################
    #                           Modify Pyramid events
    ##########################################################################
    # Shorten hieroglyph get
    f.seek(int("8c7b8",16)+rom_offset)
    f.write("\x6b")
    f.seek(int("8c87f",16)+rom_offset)
    f.write("\x6b")
    f.seek(int("8c927",16)+rom_offset)
    f.write("\x6b")
    f.seek(int("8c9cf",16)+rom_offset)
    f.write("\x6b")
    f.seek(int("8ca77",16)+rom_offset)
    f.write("\x6b")
    f.seek(int("8cb1f",16)+rom_offset)
    f.write("\x6b")

    ##########################################################################
    #                            Modify Babel events
    ##########################################################################
    # Move Dark Space in Babel Tower from map 224 to map 223
    # Allows player to exit Babel without crystal ring
    # Modify address pointer for Maps 224 in exit table
    f.seek(int("183f4",16)+rom_offset)
    f.write("\xea")
    # Move Dark Space exit data to Map 223
    f_babel1 = open(folder + "01a7c2_babel.bin","r+b")
    f.seek(int("1a7c2",16)+rom_offset)
    f.write(f_babel1.read())
    f_babel1.close
    # Modify address pointer for Maps 224-227 in event table
    f.seek(int("c81c0",16)+rom_offset)
    f.write("\xa2\xe0\xe3\xe0\x0f\xe1\x2d\xe1")
    # Move Dark Space event data to Map 223
    # Also move spirits for entrance warp
    f_babel2 = open(folder + "0ce099_babel.bin","r+b")
    f.seek(int("ce099",16)+rom_offset)
    f.write(f_babel2.read())
    f_babel2.close

    # Spirits can warp you back to start
    f.seek(int("99b69",16)+rom_offset)
    f.write("\x76\x9B\x76\x9B\x76\x9B\x76\x9B")
    f.seek(int("99b7a",16)+rom_offset)
    f.write("\x02\xBE\x02\x01\x80\x9B\x86\x9B\x86\x9B\x16\x9D\x02\xBF\x95\x9C\x6B")
    f.seek(int("99c1e",16)+rom_offset)
    f.write("\xd3" + qt.encode("What'd you like to do?") + "\xcb\xac")
    f.write(qt.encode("Git gud") + "\xcb\xac" + qt.encode("Run away!") + "\xca")
    f.seek(int("99c95",16)+rom_offset)
    f.write("\xce" + qt.encode("Darn straight.") + "\xc0")
    f.seek(int("99d16",16)+rom_offset)
    f.write("\x02\x26\xDE\x78\x00\xC0\x00\x00\x00\x11\x02\xC5")

    # Change switch conditions for Crystal Ring item
    f.seek(int("9999b",16)+rom_offset)
    f.write("\x4c\xd0\xf6")
    f.seek(int("9f6d0",16)+rom_offset)
    f.write("\x02\xd0\xdc\x00\xa0\x99\x02\xd0\x3e\x00\xa0\x99\x02\xd0\xb4\x01\x9a\x99\x4c\xa0\x99")
    f.seek(int("999aa",16)+rom_offset)
    f.write("\x4c\xf0\xf6")
    f.seek(int("9f6f0",16)+rom_offset)
    f.write("\x02\xd0\xdc\x01\x9a\x99\x4c\xaf\x99")
    f.seek(int("99a57",16)+rom_offset)
    f.write("\x4c\x10\xf7")
    f.seek(int("9f710",16)+rom_offset)
    f.write("\x02\xd4\x27\x6b\x9a\x02\xcc\xdc\x4c\x5c\x9a")
    # Change text
    f.seek(int("99a70",16)+rom_offset)
    f.write(qt.encode("Hey! Listen!", True))
    f.seek(int("99a91",16)+rom_offset)
    f.write(qt.encode("Well, lookie here.", True))

    # Olman event no longer warps you out of the room
    f.seek(int("98891",16)+rom_offset)
    f.write("\x02\x0b\x6b")

    # Shorten Olman text boxes
    f.seek(int("9884c",16)+rom_offset)
    f.write("\x01\x00")
    f.seek(int("98903",16)+rom_offset)
    f.write(qt.encode("heya.", True))
    f.seek(int("989a2",16)+rom_offset)
    f.write(qt.encode("you've been busy, huh?", True))

    # Speed up roof sequence
    f.seek(int("98fad",16)+rom_offset)
    f.write("\x02\xcc\x0e\x02\xcc\x0f\x6b")

    ##########################################################################
    #                      Modify Jeweler's Mansion events
    ##########################################################################
    # Set exit warp to Dao
    f.seek(int("8fcb2",16)+rom_offset)
    f.write("\x02\x26\xc3\x40\x01\x88\x00\x00\x00\x23")

    # Set flag when Solid Arm is killed
    f.seek(int("8fa25",16)+rom_offset)
    f.write("\x4c\x20\xfd")
    f.seek(int("8fd20",16)+rom_offset)
    f.write("\x02\xcc\xf4\x02\x26\xe3\x80\x02\xa0\x01\x80\x10\x23\x02\xe0")

    ##########################################################################
    #                           Modify Ending cutscene
    ##########################################################################
    # Custom credits
    f_ending = open(folder + "0bd558_ending.bin","r+b")
    f.seek(int("bd558",16)+rom_offset)
    f.write(f_ending.read())
    f_ending.close
    f.seek(int("bdee2",16)+rom_offset)
    f.write("\xcb\xac\xac\xd6\x53\x88\xa4\x2b\xac\xa3\x87\x8e\xa7\x0e\xa3\xac\xd6\xbe\xc9\xb4\xc8\xca")

    ##########################################################################
    #                           Modify Jeweler event
    ##########################################################################
    # Replace status upgrades with item acquisitions
    f_jeweler = open(folder + "08cec9_jeweler.bin","r+b")
    f.seek(int("8cec9",16)+rom_offset)
    f.write(f_jeweler.read())
    f_jeweler.close

    # Jeweler doesn't disappear when defeated
    f.seek(int("8cea5",16)+rom_offset)
    f.write("\x10\x00")

    # Jeweler warps you to credits for Red Jewel hunts
    if goal == "Red Jewel Hunt":
        f.seek(int("8d089",16)+rom_offset)
        f.write("\xE5\x00\x00\x00\x00\x00\x00\x11")
        f.seek(int("8d2d8",16)+rom_offset)
        f.write(qt.encode("Beat the game"))

    ##########################################################################
    #                          Update dark space code
    ##########################################################################
    # Allow player to return to South Cape at any time
    # Also, checks for end game state and warps to final boss
    f_darkspace = open(folder + "08db07_darkspace.bin","r+b")
    f.seek(int("8db07",16)+rom_offset)
    f.write(f_darkspace.read())
    f_darkspace.close

    # Shorten ability acquisition text
    f.seek(int("8eb81",16)+rom_offset)
    f.write("\xc0")

    # Cut out ability explanation text
    f.seek(int("8eb15",16)+rom_offset)
    f.write("\xa4\x26\xa9\x00\x00\x99\x24\x00\x02\x04\x16")
    f.write("\x02\xda\x01\xa9\xf0\xff\x1c\x5a\x06\x02\xe0")

    # Remove abilities from all Dark Spaces
    f.seek(int("c8b34",16)+rom_offset)        # Itory Village (Psycho Dash)
    f.write("\x01")
    f.seek(int("c9b49",16)+rom_offset)        # Diamond Mine (Dark Friar)
    f.write("\x03")
    f.seek(int("caa99",16)+rom_offset)        # Mu (Psycho Slide)
    f.write("\x03")
    f.seek(int("cbb80",16)+rom_offset)        # Great Wall (Spin Dash)
    f.write("\x03")
    f.seek(int("cc7b8",16)+rom_offset)        # Mt. Temple (Aura Barrier)
    f.write("\x03")
    f.seek(int("cd0a2",16)+rom_offset)        # Ankor Wat (Earthquaker)
    f.write("\x03")

    ##########################################################################
    #                          Fix special attacks
    ##########################################################################
    # Earthquaker no longer charges; Aura Barrier can be used w/o Friar
    f.seek(int("2b871",16)+rom_offset)
    f.write("\x30")

    # Insert new code to explicitly check for Psycho Dash and Friar
    f.seek(int("2f090",16)+rom_offset)
    f.write("\xAD\xA2\x0A\x89\x01\x00\xF0\x06\xA9\xA0\xBE\x20\x26\xB9\x4C\x01\xB9")  # Psycho Dash @2f090
    f.write("\xAD\xA2\x0A\x89\x10\x00\xF0\x06\xA9\x3B\xBB\x20\x26\xB9\x4C\x01\xB9")  # Dark Friar @2f0a1

    # Insert jumps to new code
    f.seek(int("2b858",16)+rom_offset)  # Psycho Dash
    f.write("\x4c\x90\xf0")
    f.seek(int("2b8df",16)+rom_offset)  # Dark Friar
    f.write("\x4c\xa1\xf0")

    ##########################################################################
    #                      Disable NPCs in various maps
    ##########################################################################
    # School
    f.seek(int("48d25",16)+rom_offset)   # Lance
    f.write("\xe0\x6b")
    f.seek(int("48d72",16)+rom_offset)   # Seth
    f.write("\xe0\x6b")
    f.seek(int("48d99",16)+rom_offset)   # Erik
    f.write("\xe0\x6b")

    # Seaside cave
    f.seek(int("4afb6",16)+rom_offset)   # Playing cards
    f.write("\xe0\x6b")
    f.seek(int("4b06c",16)+rom_offset)   # Lance
    f.write("\xe0\x6b")
    f.seek(int("4b459",16)+rom_offset)   # Seth
    f.write("\xe0\x6b")

    # Edward's Castle
    f.seek(int("4cb5e",16)+rom_offset)   # Kara
    f.write("\xe0\x6b")
    f.seek(int("9bc37",16)+rom_offset)   # Lilly's flower
    f.write("\x02\xe0\x6b")

    # Itory Village
    f.seek(int("4e06e",16)+rom_offset)   # Kara
    f.write("\xe0\x6b")
    f.seek(int("4f0a7",16)+rom_offset)   # Lola
    f.write("\xe0\x6b")
    f.seek(int("4ef78",16)+rom_offset)   # Bill
    f.write("\xe0\x6b")

    # Lilly's House
    f.seek(int("4e1b7",16)+rom_offset)   # Kara
    f.write("\xe0\x6b")

    # Moon Tribe
    #f.seek(int("4f445",16)+rom_offset)   # Lilly
    #f.write("\xe0\x6b")

    # Inca Ruins Entrance
    f.seek(int("9ca03",16)+rom_offset)   # Lilly
    f.write("\xe0\x6b")
    f.seek(int("9cea7",16)+rom_offset)   # Kara
    f.write("\xe0\x6b")

    # Diamond Coast
    #f.seek(int("5aaa2",16)+rom_offset)   # Kara
    #f.write("\xe0\x6b")

    # Freejia Hotel
    f.seek(int("5c782",16)+rom_offset)   # Lance
    f.write("\xe0\x6b")
    f.seek(int("5cb34",16)+rom_offset)   # Erik
    f.write("\xe0\x6b")
    f.seek(int("5c5b7",16)+rom_offset)   # Lilly??
    f.write("\xe0\x6b")
    f.seek(int("5c45a",16)+rom_offset)   # Kara??
    f.write("\xe0\x6b")

    # Nazca Plain
    f.seek(int("5e845",16)+rom_offset)
    f.write("\xe0\x6b")
    f.seek(int("5ec8f",16)+rom_offset)
    f.write("\xe0\x6b")
    f.seek(int("5eea5",16)+rom_offset)
    f.write("\xe0\x6b")
    f.seek(int("5efed",16)+rom_offset)
    f.write("\xe0\x6b")
    f.seek(int("5f1fd",16)+rom_offset)
    f.write("\xe0\x6b")

    # Seaside Palace
    f.seek(int("68689",16)+rom_offset)   # Lilly
    f.write("\xe0\x6b")

    # Mu
    f.seek(int("6a2cc",16)+rom_offset)   # Erik
    f.write("\xe0\x6b")

    # Angel Village
    #f.seek(int("6dc54",16)+rom_offset)   # Ishtar's apprentice
    #f.write("\xe0\x6b")
    #f.seek(int("6d8bf",16)+rom_offset)   # Ishtar's puzzle doors
    #f.write("\x02\xe0\x6b")

    # Watermia
    f.seek(int("7a871",16)+rom_offset)   # Lilly
    f.write("\xe0\x6b")

    # Euro
    f.seek(int("7d989",16)+rom_offset)   # Kara
    f.write("\xe0\x6b")
    f.seek(int("7daa1",16)+rom_offset)   # Erik
    f.write("\xe0\x6b")
    f.seek(int("7db29",16)+rom_offset)   # Neil
    f.write("\xe0\x6b")

    # Natives' Village
    #f.seek(int("8805d",16)+rom_offset)   # Kara
    #f.write("\xe0\x6b")
    #f.seek(int("8865f",16)+rom_offset)   # Hamlet
    #f.write("\xe0\x6b")
    #f.seek(int("8854a",16)+rom_offset)   # Erik
    #f.write("\xe0\x6b")

    # Dao
    f.seek(int("8a4af",16)+rom_offset)   # Kara
    f.write("\xe0\x6b")
    f.seek(int("8a56b",16)+rom_offset)   # Erik
    f.write("\xe0\x6b")
    #f.seek(int("980cc",16)+rom_offset)   # Spirit
    #f.write("\xe0\x6b")

    # Pyramid
    f.seek(int("8b7a1",16)+rom_offset)   # Kara
    f.write("\xe0\x6b")
    f.seek(int("8b822",16)+rom_offset)   # Jackal
    f.write("\xe0\x6b")

    # Babel
    f.seek(int("99e90",16)+rom_offset)   # Kara 1
    f.write("\xe0\x6b")
    f.seek(int("98519",16)+rom_offset)   # Kara 2
    f.write("\xe0\x6b")

    ##########################################################################
    #                       Assign Room/Boss Rewards
    ##########################################################################
    # Remove existing rewards
    f_roomrewards = open(folder + "01aade_roomrewards.bin","r+b")
    f.seek(int("1aade",16)+rom_offset)
    f.write(f_roomrewards.read())
    f_roomrewards.close

    # Make room-clearing HP rewards grant +3 HP each
    f.seek(int("e041",16)+rom_offset)
    f.write("\x03")

    # Make boss rewards also grant +3 HP per unclaimed reward
    f.seek(int("c381",16)+rom_offset)
    f.write("\x20\x90\xf4")
    f.seek(int("f490",16)+rom_offset)
    f.write("\xee\xca\x0a\xee\xca\x0a\xee\xca\x0a\x60")

    # Change boss room ranges
    f.seek(int("c31a",16)+rom_offset)
    f.write("\x67\x5A\x73\x00\x8A\x82\xA8\x00\xDD\xCC\xDD\x00\xEA\xB0\xBF\x00")
    #f.write("\xF6\xB0\xBF\x00")   # If Solid Arm ever grants Babel rewards

    # Add boss reward events to Babel and Jeweler Mansion
    #f.seek(int("ce3cb",16)+rom_offset)  # Solid Arm
    #f.write("\x00\x01\x01\xDF\xA5\x8B\x00\x00\x01\x01\xBB\xC2\x80\x00\xFF\xCA")
    f.seek(int("ce536",16)+rom_offset)  # Mummy Queen (Babel)
    f.write("\x00\x01\x01\xBB\xC2\x80\x00\xFF\xCA")

    # Collect map numbers for valid room-clearing rewards
    maps_castoth = [12,13,14,15,18]                                                 # Underground
    maps_castoth += [29,32,33,34,35,37,38,39,40]                                    # Inca
    maps_viper = [61,62,63,64,65,69,70]                                             # Mine
    maps_viper += [77,78,79,80,81,82,83,84]                                         # Sky Garden
    maps_vampires = [95,96,97,98,100,101]                                           # Mu
    maps_vampires += [109,110,111,112,113,114]                                      # Angel
    maps_sandfanger = [130,131,132,133,134,135,136]                                 # Wall
    maps_sandfanger += [160,161,162,163,164,165,166,167,168]                        # Kress
    maps_babel = [176,177,178,179,180,181,182,183,184,185,186,187,188,189,190]      # Ankor Wat
    maps_mummyqueen = [204,205,206,207,208,209,210,211,212,213,214,215,216,217,219] # Pyramid

    random.shuffle(maps_castoth)
    random.shuffle(maps_viper)
    random.shuffle(maps_vampires)
    random.shuffle(maps_sandfanger)
    random.shuffle(maps_babel)
    random.shuffle(maps_mummyqueen)

    boss_areas = [maps_castoth,maps_viper,maps_vampires,maps_sandfanger,maps_babel,maps_mummyqueen]
    boss_rewards = 4 - mode

    rewards = []              # Total rewards by mode (HP/STR/DEF)
    if mode == 0:             # Easy: 10/7/7
        rewards += [1] * 10
        rewards += [2] * 7
        rewards += [3] * 7
    elif mode == 1:           # Normal: 10/4/4
        rewards += [1] * 10
        rewards += [2] * 4
        rewards += [3] * 4
    elif mode == 2:           # Hard: 8/2/2
        rewards += [1] * 8
        rewards += [2] * 2
        rewards += [3] * 2
    elif mode == 3:           # Extreme: 6/0/0
        rewards += [1] * 6

    random.shuffle(rewards)

    # Add in rewards, where applicable, by difficulty
    for area in boss_areas:
        i = 0
        while i < boss_rewards:
            map_num = area[i]
            reward = rewards.pop(0)
            f.seek(int("1aade",16) + map_num + rom_offset)
            if reward == 1:
                f.write("\x01")
            elif reward == 2:
                f.write("\x02")
            elif reward == 3:
                f.write("\x03")
            i += 1

    ##########################################################################
    #                        Balance Enemy Stats
    ##########################################################################
    # Determine enemy stats, by difficulty
    if mode == 0:
        f_enemies = open(folder + "01abf0_enemieseasy.bin","r+b")
    elif mode == 1:
        f_enemies = open(folder + "01abf0_enemiesnormal.bin","r+b")
    elif mode == 2:
        f_enemies = open(folder + "01abf0_enemieshard.bin","r+b")
    elif mode == 3:
        f_enemies = open(folder + "01abf0_enemiesextreme.bin","r+b")

    if mode < 4:
        f.seek(int("1abf0",16)+rom_offset)
        f.write(f_enemies.read())
        f_enemies.close

    ##########################################################################
    #                            Randomize Inca tile
    ##########################################################################
    # Prepare file for uncompressed map data
    path_incamapblank = folder + "incamapblank.bin"
    path_incamapnew = folder + "incamap.bin"
    copyfile(path_incamapblank,path_incamapnew)

    # Set random X/Y for new Inca tile
    inca_x = random.randint(0,11)
    inca_y = random.randint(0,5)

    # Modify coordinates in event data
    inca_str = format(2*inca_x+4,"02x") + format(15+2*inca_y,"02x")
    inca_str = inca_str + format(7+2*inca_x,"02x") + format(18+2*inca_y,"02x")
    f.seek(int("9c683",16)+rom_offset)
    f.write(binascii.unhexlify(inca_str))

    # Remove Wind Melody when door opens
    f.seek(int("9c660",16)+rom_offset)
    f.write("\x02\xcd\x12\x01\x02\xd5\x08\x02\xe0")
    f.seek(int("9c676",16)+rom_offset)
    f.write("\x67")
    f.seek(int("9c6a3",16)+rom_offset)
    f.write("\x02\xd0\x10\x01\x60\xc6")

    # Determine address location for new tile in uncompressed map data
    row = 32 + 2*inca_y + 16*int(inca_x/6)
    column = 2 * ((inca_x+2) % 8)
    addr = 16*row + column

    # Write single tile at new location in uncompressed data
    f_incamap = open(folder + "incamap.bin","r+b")
    f_incamap.seek(addr)
    f_incamap.write("\x40\x41\x00\x00\x00\x00\x00\x00\x00")
    f_incamap.write("\x00\x00\x00\x00\x00\x00\x00\x42\x43")
    f_incamap.seek(0)

    # Compress map data and write to file
    f_incamapcomp = open(folder + "incamapcomp.bin","r+b")
    f_incamapcomp.seek(0)
    f_incamapcomp.write(quintet_comp.compress(f_incamap.read()))
    f_incamapcomp.seek(0)
    f_incamap.close

    # Insert new compressed map data
    #f.seek(int("1f38db",16)+rom_offset)
    f.seek(int("1f3ea0",16)+rom_offset)
    f.write("\x02\x02")
    f.write(f_incamapcomp.read())
    f_incamapcomp.close

    # Direct map arrangement pointer to new data - NO LONGER NECESSARY
    #f.seek(int("d8703",16)+rom_offset)
    #f.write("\xa0\x3e")

    ##########################################################################
    #                       Randomize heiroglyph order
    ##########################################################################
    # Determine random order
    hieroglyph_order = [1,2,3,4,5,6]
    random.shuffle(hieroglyph_order)

    # Update Father's Journal with correct order
    f.seek(int("39e9a",16)+rom_offset)
    for x in hieroglyph_order:
        if x==1:
            f.write("\xc0\xc1")
        elif x==2:
            f.write("\xc2\xc3")
        elif x==3:
            f.write("\xc4\xc5")
        elif x==4:
            f.write("\xc6\xc7")
        elif x==5:
            f.write("\xc8\xc9")
        elif x==6:
            f.write("\xca\xcb")

    # Update sprite pointers for hieroglyph items, Item 1e is @10803c
    f.seek(int("10803c",16)+rom_offset)
    for x in hieroglyph_order:
        if x==1:
            f.write("\xde\x81")
        if x==2:
            f.write("\xe4\x81")
        if x==3:
            f.write("\xea\x81")
        if x==4:
            f.write("\xf0\x81")
        if x==5:
            f.write("\xf6\x81")
        if x==6:
            f.write("\xfc\x81")

    # Update which tiles are called when hieroglyph is placed
    i = 0
    for x in hieroglyph_order:
        f.seek(int("39b89",16)+5*i+rom_offset)
        if x==1:
            f.write("\x84")
        elif x==2:
            f.write("\x85")
        elif x==3:
            f.write("\x86")
        elif x==4:
            f.write("\x8c")
        elif x==5:
            f.write("\x8d")
        elif x==6:
            f.write("\x8e")
        i += 1

    # Update which tiles are called from placement flags
    f.seek(int("8cb94",16)+rom_offset)
    for x in hieroglyph_order:
        if x==1:
            f.write("\x84")
        elif x==2:
            f.write("\x85")
        elif x==3:
            f.write("\x86")
        elif x==4:
            f.write("\x8c")
        elif x==5:
            f.write("\x8d")
        elif x==6:
            f.write("\x8e")


    ##########################################################################
    #                    Randomize Jeweler Reward amounts
    ##########################################################################
    # Randomize jeweler reward values
    gem=[]
    gem.append(random.randint(1,3))
    gem.append(random.randint(4,6))
    gem.append(random.randint(7,9))
    gem.append(random.randint(10,14))
    gem.append(random.randint(16,24))
    gem.append(random.randint(26,34))
    gem.append(random.randint(36,50))

    if goal == "Red Jewel Hunt":
        if mode == 0:
            gem[6] = GEMS_EASY
        elif mode == 1:
            gem[6] = GEMS_NORMAL
        else:
            gem[6] = GEMS_HARD

    gem_str=[]

    # Write new values into reward check code (BCD format)
    gem_str.append(format(int(gem[0]/10),"x") + format(gem[0] % 10,"x"))
    f.seek(int("8cee0",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[0]))

    gem_str.append(format(int(gem[1]/10),"x") + format(gem[1] % 10,"x"))
    f.seek(int("8cef1",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[1]))

    gem_str.append(format(int(gem[2]/10),"x") + format(gem[2] % 10,"x"))
    f.seek(int("8cf02",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[2]))

    gem_str.append(format(int(gem[3]/10),"x") + format(gem[3] % 10,"x"))
    f.seek(int("8cf13",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[3]))

    gem_str.append(format(int(gem[4]/10),"x") + format(gem[4] % 10,"x"))
    f.seek(int("8cf24",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[4]))

    gem_str.append(format(int(gem[5]/10),"x") + format(gem[5] % 10,"x"))
    f.seek(int("8cf35",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[5]))

    gem_str.append(format(int(gem[6]/10),"x") + format(gem[6] % 10,"x"))
    f.seek(int("8cf40",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[6]))

    # Write new values into inventory table (Quintet text table format)
    # NOTE: Hard-coded for 1st, 2nd and 3rd rewards each < 10
    gem_str[0] = format(2,"x") + format(gem[0] % 10,"x")
    f.seek(int("8d26f",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[0]))

    gem_str[1] = format(2,"x") + format(gem[1] % 10,"x")
    f.seek(int("8d283",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[1]))

    gem_str[2] = format(2,"x") + format(gem[2] % 10,"x")
    f.seek(int("8d297",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[2]))

    gem_str[3] = format(2,"x") + format(int(gem[3]/10),"x")
    gem_str[3] = gem_str[3] + format(2,"x") + format(gem[3] % 10,"x")
    f.seek(int("8d2aa",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[3]))

    gem_str[4] = format(2,"x") + format(int(gem[4]/10),"x")
    gem_str[4] = gem_str[4] + format(2,"x") + format(gem[4] % 10,"x")
    f.seek(int("8d2be",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[4]))

    gem_str[5] = format(2,"x") + format(int(gem[5]/10),"x")
    gem_str[5] = gem_str[5] + format(2,"x") + format(gem[5] % 10,"x")
    f.seek(int("8d2d2",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[5]))

    gem_str[6] = format(2,"x") + format(int(gem[6]/10),"x")
    gem_str[6] = gem_str[6] + format(2,"x") + format(gem[6] % 10,"x")
    f.seek(int("8d2e6",16)+rom_offset)
    f.write(binascii.unhexlify(gem_str[6]))

    ##########################################################################
    #                    Randomize Mystic Statue requirement
    ##########################################################################
    statueOrder=[1,2,3,4,5,6]
    random.shuffle(statueOrder)

    statues=[]
    statues_hex=[]

    i = 0
    while i < statues_required:
        if statueOrder[i] == 1:
            statues.append(1)
            statues_hex.append("\x21")

            # Check for Mystic Statue possession at end game state
            f.seek(int("8dd19",16)+rom_offset)
            f.write("\xf8")

        if statueOrder[i] == 2:
            statues.append(2)
            statues_hex.append("\x22")

            # Check for Mystic Statue possession at end game state
            f.seek(int("8dd1f",16)+rom_offset)
            f.write("\xf9")

        if statueOrder[i] == 3:
            statues.append(3)
            statues_hex.append("\x23")

            # Check for Mystic Statue possession at end game state
            f.seek(int("8dd25",16)+rom_offset)
            f.write("\xfa")

            # Restrict removal of Rama Statues from inventory
            f.seek(int("1e12c",16)+rom_offset)
            f.write("\x8f")

        if statueOrder[i] == 4:
            statues.append(4)
            statues_hex.append("\x24")

            # Check for Mystic Statue possession at end game state
            f.seek(int("8dd2b",16)+rom_offset)
            f.write("\xfb")

        if statueOrder[i] == 5:
            statues.append(5)
            statues_hex.append("\x25")

            # Check for Mystic Statue possession at end game state
            f.seek(int("8dd31",16)+rom_offset)
            f.write("\xfc")

            # Restrict removal of Hieroglyphs from inventory
            f.seek(int("1e12d",16)+rom_offset)
            f.write("\xe7\xbf")

        if statueOrder[i] == 6:
            statues.append(6)
            statues_hex.append("\x26")

            # Check for Mystic Statue possession at end game state
            f.seek(int("8dd37",16)+rom_offset)
            f.write("\xfd")

        i += 1

    # Can't face Dark Gaia in Red Jewel hunts
    if goal != "Dark Gaia":
        f.seek(int("8dd0d",16)+rom_offset)
        f.write("\x10\x01")

    statues.sort()
    statues_hex.sort()

    # Teacher at start spoils required Mystic Statues
    statue_str = ""
    if len(statues_hex) == 0:
        statue_str = "\xd3\x4d\x8e\xac\xd6\xd2\x80\xa2\x84\xac"
        statue_str += "\xa2\x84\xa1\xa5\x88\xa2\x84\x83\x4f\xc0"

    else:
        statue_str = "\xd3\x69\x8e\xa5\xac\x8d\x84\x84\x83\xac"
        statue_str += "\x4c\xa9\xa3\xa4\x88\x82\xac\x63\xa4\x80\xa4\xa5\x84"
        if len(statues_hex) == 1:
            statue_str += "\xac"
            statue_str += statues_hex[0]
            statue_str += "\x4f\xc0"

        else:
            statue_str += "\xa3\xcb"
            while statues_hex:
                if len(statues_hex) > 1:
                    statue_str += statues_hex[0]
                    statue_str += "\x2b\xac"

                else:
                    statue_str += "\x80\x8d\x83\xac"
                    statue_str += statues_hex[0]
                    statue_str += "\x4f\xc0"

                statues_hex.pop(0)

    f.seek(int("48aa8",16)+rom_offset)
    f.write(statue_str)

    ##########################################################################
    #                   Randomize Location of Kara Portrait
    #       Sets spoiler in Lance's Letter and places portrait sprite
    ##########################################################################
    # Determine random location ID
    kara_location = random.randint(1,5)
    #ANGEL_TILESET = "\x03\x00\x10\x10\x36\x18\xca\x01"
    #ANGEL_PALETTE = "\x04\x00\x60\xa0\x80\x01\xdf"
    #ANGEL_SPRTESET = "\x10\x43\x0a\x00\x00\x00\xda"

    # Modify Kara Portrait event
    f.seek(int("6d153",16)+rom_offset)
    f.write("\x8a")
    f.seek(int("6d169",16)+rom_offset)
    f.write("\x02\xd2\x8a\x01\x02\xe0")
    f.seek(int("6d25c",16)+rom_offset)
    f.write("\x8a")
    f.seek(int("6d27e",16)+rom_offset)
    f.write(qt.encode("Hurry boy, she's waiting there for you!") + "\xc0")
    f.seek(int("6d305",16)+rom_offset)
    f.write(qt.encode("Kara's portrait. If only you had Magic Dust...") + "\xc0")

    if kara_location == KARA_ANGEL:
        # Set spoiler for Kara's location in Lance's Letter
        f.seek(int("3951e",16)+rom_offset)
        f.write("\x40\x8d\x86\x84\x8b\xac\x66\x88\x8b\x8b\x80\x86\x84")

    else:
        # Remove Kara's painting from Ishtar's Studio
        f.seek(int("cb397",16)+rom_offset)
        f.write("\x18")

        if kara_location == KARA_EDWARDS:  # Underground tunnel exit, map 19 (0x13)
            # Set spoiler for Kara's location in Lance's Letter
            f.seek(int("3951e",16)+rom_offset)
            f.write("\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x60\xa2\x88\xa3\x8e\x8d")

            # Set map check ID for Magic Dust item event
            f.seek(int("393a9",16)+rom_offset)
            f.write("\x13\x00\xD0\x08\x02\x45\x0b\x0b\x0d\x0d")

            # Set Kara painting event in appropriate map
            f.seek(int("c8ac5",16)+rom_offset)
            f.write("\x0b\x0b\x00\x4e\xd1\x86\xff\xca") # this is correct

            # Adjust sprite palette
            f.seek(int("6d15b",16)+rom_offset)
            f.write("\x02\xb6\x30")

        elif kara_location == KARA_MINE:
            # Set spoiler for Kara's location in Lance's Letter
            f.seek(int("3951e",16)+rom_offset)
            f.write("\x43\x88\x80\x8c\x8e\x8d\x83\xac\x4c\x88\x8d\x84")

            # Set map check ID for Magic Dust item event
            f.seek(int("393a9",16)+rom_offset)
            f.write("\x47\x00\xD0\x08\x02\x45\x0b\x24\x0d\x26")

            # Change "Sam" to "Samlet"
            f.seek(int("5fee0",16)+rom_offset)
            f.write("\x1a\x00\x10\x02\xc0\x9e\xd2\x02\x0b\x02\xc1\x6b")
            f.seek(int("5d2bd",16)+rom_offset)
            f.write("\xf0\xd2")
            f.seek(int("5d2f0",16)+rom_offset)
            f.write("\xd3\xc2\x05" + qt.encode("Samlet: I'll never forget you!") + "\xc0")
            f.seek(int("c9c78",16)+rom_offset)
            f.write("\x03\x2a\x00\xe0\xfe\x85")

            # Disable Remus
            f.seek(int("5d15e",16)+rom_offset)
            f.write("\xe0")

            # Assign Kara painting spriteset to appropriate Map
            f.seek(int("d8d55",16)+rom_offset)
            f.write("\x0a")

            # Set Kara painting event in appropriate map
            f.seek(int("c9c6a",16)+rom_offset)
            f.write("\x0b\x24\x00\x4e\xd1\x86")

            # Adjust sprite
            #f.seek(int("6d14e",16)+rom_offset)
            #f.write("\x2a")
            f.seek(int("6d15b",16)+rom_offset)
            f.write("\x02\xb6\x30")

        elif kara_location == KARA_KRESS:

            # Set spoiler for Kara's location in Lance's Letter
            f.seek(int("3951e",16)+rom_offset)
            f.write("\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3")

            # Set map check ID for Magic Dust item event
            f.seek(int("393a9",16)+rom_offset)
            f.write("\xa9\x00\xD0\x08\x02\x45\x12\x06\x14\x08")

            # Set Kara painting event in appropriate map
            # Map #169, written into unused Map #104 (Seaside Tunnel)
            f.seek(int("c8152",16)+rom_offset)
            f.write("\x42\xad")
            f.seek(int("cad42",16)+rom_offset)
            f.write("\x05\x0a\x00\x8c\xc3\x82\x00\x00\x00\x00\xed\xea\x80\x00\xdf")
            f.write("\xdf\x00\x4d\xe9\x80\x00\x12\x06\x00\x4e\xd1\x86\x00\xff\xca")

            # Adjust sprite
            f.seek(int("6d15b",16)+rom_offset)
            f.write("\x02\xb6\x30")

        elif kara_location == KARA_ANKORWAT:
            # Set spoiler for Kara's location in Lance's Letter
            f.seek(int("3951e",16)+rom_offset)
            f.write("\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4")

            # Set map check ID for Magic Dust item event
            f.seek(int("393a9",16)+rom_offset)
            f.write("\xbf\x00\xD0\x08\x02\x45\x1a\x10\x1c\x12")

            # Set Kara painting event in appropriate map (Map #191)
            # Map #191, written into unused Map #104 (Seaside Tunnel)
            f.seek(int("c817e",16)+rom_offset)
            f.write("\x42\xad")
            f.seek(int("cad42",16)+rom_offset)
            f.write("\x05\x0a\x02\x8c\xc3\x82\x00\x00\x00\x00\xed\xea\x80\x00\x0f")
            f.write("\x0b\x00\xa3\x9a\x88\x00\x1a\x10\x00\x4e\xd1\x86\x00\xff\xca")

            # Adjust sprite
            f.seek(int("6d15b",16)+rom_offset)
            f.write("\x02\xb6\x30")

    ##########################################################################
    #                          Have fun with death text
    ##########################################################################
    death_list = []
    death_list.append("\x2d\x41\x84\xac\x82\x80\x8b\x8c\x2a\xac\x46\x8e\x83\xac\x80\xa7\x80\x88\xa4\xa3\xac\xa9\x8e\xa5\xac\xcb\x80\xa4\xac\xa4\x87\x84\xac\x83\x8e\x8e\xa2\x2a\x2e\xcb\xac\xac\x6d\x46\x80\x81\xa2\x88\x84\x8b\xac\x46\x80\xa2\x82\x88\x80\xac\x4c\x80\xa2\xa1\xa5\x84\xaa\xc0")
    death_list.append("\x2d\x67\x84\xac\xd6\x91\xd7\x88\x80\x8b\x88\xa6\x84\xac\xd6\xf6\xcb\xa7\x84\xac\x80\xa2\x84\xac\x82\x8b\x8e\xa3\x84\xa3\xa4\xac\xa4\x8e\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x4d\x84\x8d\x88\x80\xac\x42\x80\x8c\xa0\x81\x84\x8b\x8b\xc0")
    death_list.append("\x43\x84\x80\xa4\x87\xac\xa4\xa7\x88\xa4\x82\x87\x84\xa3\xac\x8c\xa9\xac\x84\x80\xa2\x2f\xac\xcb\x2d\x4b\x88\xa6\x84\xab\x2e\xac\x87\x84\xac\xa3\x80\xa9\xa3\x2a\x2a\x2a\xac\x2d\x48\x0e\x8c\xac\xcb\x82\x8e\x8c\x88\x8d\x86\x2a\x2e\xcb\xac\xac\x6d\x66\x88\xa2\x86\x88\x8b\xc0")
    death_list.append("\x2d\x47\x84\x80\xa6\x84\x8d\xac\x88\xa3\xac\x80\xac\xd7\x90\xd6\xf4\xcb\x80\x8b\x8b\xac\xa4\x87\x84\xac\x83\x8e\x86\xa3\xac\xa9\x8e\xa5\x0e\xa6\x84\xac\xd7\x5d\xcb\x8b\x8e\xa6\x84\x83\xac\xd6\x79\xa4\x8e\xac\x86\xa2\x84\x84\xa4\xac\xa9\x8e\xa5\x2a\x2e\xcb\xac\xac\x6d\x4e\x8b\x88\xa6\x84\xa2\xac\x46\x80\xa3\xa0\x88\xa2\xa4\xaa\xc0")
    death_list.append("\x2d\x44\xa6\x84\xa2\xa9\xac\x8c\x80\x8d\xac\x83\x88\x84\xa3\x2a\xac\x4d\x8e\xa4\xac\xcb\x84\xa6\x84\xa2\xa9\xac\x8c\x80\x8d\xac\xd7\x95\x8b\x88\xa6\x84\xa3\x2a\x2e\xcb\xac\xac\x6d\x67\x88\x8b\x8b\x88\x80\x8c\xac\x67\x80\x8b\x8b\x80\x82\x84\xc0")
    death_list.append("\x2d\x40\x8d\x83\xac\x48\xac\xa7\x88\x8b\x8b\xac\xa3\x87\x8e\xa7\xac\xa4\x87\x80\xa4\xcb\x8d\x8e\xa4\x87\x88\x8d\x86\xac\x82\x80\x8d\xac\x87\x80\xa0\xa0\x84\x8d\xac\x8c\x8e\xa2\x84\xcb\x81\x84\x80\xa5\xa4\x88\x85\xa5\x8b\xac\xa4\x87\x80\x8d\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x67\x80\x8b\xa4\xac\x67\x87\x88\xa4\x8c\x80\x8d\xc0")
    death_list.append("\x2d\x46\x84\xa4\xac\x81\xa5\xa3\xa9\xac\x8b\x88\xa6\x88\x8d\x0e\x2b\xac\x8e\xa2\xac\x86\x84\xa4\xcb\x81\xa5\xa3\xa9\xac\x83\xa9\x88\x8d\x0e\x2a\x2e\xcb\xac\xac\x6d\x40\x8d\x83\xa9\xac\x43\xa5\x85\xa2\x84\xa3\x8d\x84\xc0")
    death_list.append("\x2d\x69\x8e\xa5\x0e\xa2\x84\xac\x8a\x88\x8b\x8b\x88\x8d\x0e\xac\x8c\x84\x2b\xcb\x63\x8c\x80\x8b\x8b\xa3\x4f\x2e\xcb\xac\xac\x6d\x47\x80\x8c\x88\x8b\xa4\x8e\x8d\xac\x60\x8e\xa2\xa4\x84\xa2\xc0")
    death_list.append("\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x89\xa5\xa3\xa4\xac\x80\x8d\x8e\xa4\x87\x84\xa2\xcb\xa0\x80\xa4\x87\x2a\xac\x4E\x8d\x84\xac\xa4\x87\x80\xa4\xac\xa7\x84\xac\x80\x8b\x8b\xac\x8c\xa5\xa3\xa4\xcb\xa4\x80\x8a\x84\x2a\x2e\xcb\xac\xac\x6d\x46\x80\x8d\x83\x80\x8b\x85\xc0")
    death_list.append("\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x8d\x8e\xa4\x87\x88\x8d\x86\x2b\xac\x81\xa5\xa4\xac\xa4\x8e\xcb\x8b\x88\xa6\x84\xac\x83\x84\x85\x84\x80\xa4\x84\x83\xac\x80\x8d\x83\xac\x88\x8d\x86\x8b\x8e\xa2\x6d\xcb\x88\x8e\xa5\xa3\xac\x88\xa3\xac\xa4\x8e\xac\x83\x88\x84\xac\x83\x80\x88\x8b\xa9\x2a\x2e\xcb\xac\xac\x6d\x4D\x80\xa0\x8e\x8b\x84\x8e\x8d\xac\x41\x8e\x8d\x80\xa0\x80\xa2\xa4\x84\xc0")
    death_list.append("\x2d\x44\xa6\x84\xa2\xa9\xac\xa0\x80\xa2\xa4\x88\x8d\x86\xac\x86\x88\xa6\x84\xa3\xac\x80\xcb\x85\x8e\xa2\x84\xa4\x80\xa3\xa4\x84\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2b\xac\x84\xa6\x84\xa2\xa9\xcb\xa2\x84\xa5\x8d\x88\x8e\x8d\xac\x80\xac\x87\x88\x8d\xa4\xac\x8e\x85\xac\xa4\x87\x84\xac\xa2\x84\x6d\xcb\xa3\xa5\xa2\xa2\x84\x82\xa4\x88\x8e\x8d\x2a\x2e\xac\x6d\x63\x82\x87\x8e\xa0\x84\x8d\x87\x80\xa5\x84\xa2\xc0")
    death_list.append("\x2d\x45\x8e\xa2\xac\x8b\x88\x85\x84\xac\x80\x8d\x83\xac\x83\x84\x80\xa4\x87\xac\x80\xa2\x84\xcb\x8e\x8d\x84\x2b\xac\x84\xa6\x84\x8d\xac\x80\xa3\xac\xa4\x87\x84\xac\xa2\x88\xa6\x84\xa2\xac\x80\x8d\x83\xcb\xa4\x87\x84\xac\xa3\x84\x80\xac\x80\xa2\x84\xac\x8e\x8d\x84\x2a\x2e\xcb\xac\x6d\x4A\x87\x80\x8b\x88\x8b\xac\x46\x88\x81\xa2\x80\x8d\xc0")
    death_list.append("\x2d\x4B\x88\xa6\x84\xac\xa9\x8e\xa5\xa2\xac\x8b\x88\x85\x84\xac\xa4\x87\x80\xa4\xac\xa4\x87\x84\xcb\x85\x84\x80\xa2\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\xac\x82\x80\x8d\xac\x8d\x84\xa6\x84\xa2\xcb\x84\x8d\xa4\x84\xa2\xac\xa9\x8e\xa5\xa2\xac\x87\x84\x80\xa2\xa4\x2a\x2e\xcb\xac\xac\x6d\x64\x84\x82\xa5\x8c\xa3\x84\x87\xc0")
    death_list.append("\x2d\x40\x82\x87\x88\x84\xa6\x88\x8d\x86\xac\x8b\x88\x85\x84\xac\x88\xa3\xac\x8d\x8e\xa4\xac\xa4\x87\x84\xcb\x84\xa1\xa5\x88\xa6\x80\x8b\x84\x8d\xa4\xac\x8e\x85\xac\x80\xa6\x8e\x88\x83\x88\x8d\x86\xcb\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x40\xa9\x8d\xac\x62\x80\x8d\x83\xc0")
    death_list.append("\x2d\x48\x85\xac\xa7\x84\xac\x8c\xa5\xa3\xa4\xac\x83\x88\x84\x2b\xac\xa7\x84\xac\x83\x88\x84\xcb\x83\x84\x85\x84\x8d\x83\x88\x8d\x86\xac\x8e\xa5\xa2\xac\xa2\x88\x86\x87\xa4\xa3\x2a\x2e\xcb\xac\xac\x6d\x63\x88\xa4\xa4\x88\x8d\x86\xac\x41\xa5\x8b\x8b\xc0")
    death_list.append("\x2d\x64\x87\x84\xac\x82\x8b\x8e\xa3\x84\xa2\xac\xa7\x84\xac\x82\x8e\x8c\x84\xac\xa4\x8e\xac\xa4\x87\x84\xcb\x8d\x84\x86\x80\xa4\x88\xa6\x84\x2b\xac\xa4\x8e\xac\x83\x84\x80\xa4\x87\x2b\xac\xa4\x87\x84\xcb\x8c\x8e\xa2\x84\xac\xa7\x84\xac\x81\x8b\x8e\xa3\xa3\x8e\x8c\x2a\x2e\xcb\xac\xac\x6d\x4C\x8e\x8d\xa4\x86\x8e\x8c\x84\xa2\xa9\xac\x42\x8b\x88\x85\xa4\xc0")
    death_list.append("\x2d\x48\x85\xac\xa7\x84\xac\x83\x8e\x8d\x0e\xa4\xac\x8a\x8d\x8e\xa7\xac\x8b\x88\x85\x84\x2b\xcb\x87\x8e\xa7\xac\x82\x80\x8d\xac\xa7\x84\xac\x8a\x8d\x8e\xa7\xac\x83\x84\x80\xa4\x87\x0d\x2e\xcb\xac\xac\x6d\x42\x8e\x8d\x85\xa5\x82\x88\xa5\xa3\xc0")
    death_list.append("\x2d\x48\xac\x83\x8e\x8d\x0e\xa4\xac\x87\x80\xa6\x84\xac\x8d\x8e\xac\x85\x84\x80\xa2\xac\x8e\x85\xcb\x83\x84\x80\xa4\x87\x2a\xac\x4C\xa9\xac\x8e\x8d\x8b\xa9\xac\x85\x84\x80\xa2\xac\x88\xa3\xcb\x82\x8e\x8c\x88\x8d\x86\xac\x81\x80\x82\x8a\xac\xa2\x84\x88\x8d\x82\x80\xa2\x8d\x80\xa4\x84\x83\x2a\x2e\xcb\xac\xac\x6d\x64\xa5\xa0\x80\x82\xac\x63\x87\x80\x8a\xa5\xa2\xc0")
    death_list.append("\x2d\x4B\x88\x85\x84\xac\x88\xa4\xa3\x84\x8b\x85\xac\x88\xa3\xac\x81\xa5\xa4\xac\xa4\x87\x84\xcb\xa3\x87\x80\x83\x8e\xa7\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2b\xac\x80\x8d\x83\xac\xa3\x8e\xa5\x8b\xa3\xcb\x83\x84\xa0\x80\xa2\xa4\x84\x83\xac\x81\xa5\xa4\xac\xa4\x87\x84\xac\xa3\x87\x80\x83\x8e\xa7\xa3\xcb\x8e\x85\xac\xa4\x87\x84\xac\x8b\x88\xa6\x88\x8d\x86\x2a\x2e\xac\x6d\x64\x2a\xac\x41\xa2\x8e\xa7\x8d\x84\xc0")
    death_list.append("\x2d\x63\x8e\x8c\x84\x8e\x8d\x84\xac\x87\x80\xa3\xac\xa4\x8e\xac\x83\x88\x84\xac\x88\x8d\xcb\x8e\xa2\x83\x84\xa2\xac\xa4\x87\x80\xa4\xac\xa4\x87\x84\xac\xa2\x84\xa3\xa4\xac\x8e\x85\xac\xa5\xa3\xcb\xa3\x87\x8e\xa5\x8b\x83\xac\xa6\x80\x8b\xa5\x84\xac\x8b\x88\x85\x84\xac\x8c\x8e\xa2\x84\x2a\x2e\xcb\xac\xac\x6d\x66\x88\xa2\x86\x88\x8d\x88\x80\xac\x67\x8e\x8e\x8b\x85\xc0")
    death_list.append("\x2d\x4E\xa5\xa2\xac\x8b\x88\x85\x84\xac\x83\xa2\x84\x80\x8c\xa3\xac\xa4\x87\x84\xcb\x65\xa4\x8e\xa0\x88\x80\x2a\xac\x4E\xa5\xa2\xac\x83\x84\x80\xa4\x87\xac\x80\x82\x87\x88\x84\xa6\x84\xa3\xcb\xa4\x87\x84\xac\x48\x83\x84\x80\x8b\x2a\x2e\xcb\xac\xac\x6d\x66\x88\x82\xa4\x8e\xa2\xac\x47\xa5\x86\x8e\xc0")
    death_list.append("\x2d\x48\x85\xac\xa9\x8e\xa5\xac\x83\x88\x84\xac\x88\x8d\xac\x80\x8d\xcb\x84\x8b\x84\xa6\x80\xa4\x8e\xa2\x2b\xac\x81\x84\xac\xa3\xa5\xa2\x84\xac\xa4\x8e\xac\xa0\xa5\xa3\x87\xcb\xa4\x87\x84\xac\x65\xa0\xac\x81\xa5\xa4\xa4\x8e\x8d\x2a\x2e\xcb\xac\xac\x6d\x63\x80\x8c\xac\x4B\x84\xa6\x84\x8d\xa3\x8e\x8d\xc0")
    death_list.append("\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa6\x84\xa2\xa9\xac\x8e\x85\xa4\x84\x8d\xcb\xa2\x84\x85\x84\xa2\xa2\x84\x83\xac\xa4\x8e\xac\x80\xa3\xac\x80\xac\x86\x8e\x8e\x83\xcb\x82\x80\xa2\x84\x84\xa2\xac\x8c\x8e\xa6\x84\x2a\x2e\xcb\xac\xac\x6d\x41\xa5\x83\x83\xa9\xac\x47\x8e\x8b\x8b\xa9\xc0")
    death_list.append("\x2d\x42\x8e\xa5\xa2\x80\x86\x84\xac\x88\xa3\xac\x81\x84\x88\x8d\x86\xac\xa3\x82\x80\xa2\x84\x83\xcb\xa4\x8e\xac\x83\x84\x80\xa4\x87\x2a\x2a\x2a\xac\x80\x8d\x83\xac\xa3\x80\x83\x83\x8b\x88\x8d\x86\xcb\xa5\xa0\xac\x80\x8d\xa9\xa7\x80\xa9\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x67\x80\xa9\x8d\x84\xc0")
    death_list.append("\x2d\x48\x8d\x80\x82\xa4\x88\xa6\x88\xa4\xa9\xac\x88\xa3\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x41\x84\x8d\x88\xa4\x8e\xac\x4C\xa5\xa3\xa3\x8e\x8b\x88\x8d\x88\xc0")
    death_list.append("\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa4\x87\x84\xac\x86\x8e\x8b\x83\x84\x8d\xac\x8a\x84\xa9\xcb\xa4\x87\x80\xa4\xac\x8e\xa0\x84\x8d\xa3\xac\xa4\x87\x84\xac\xa0\x80\x8b\x80\x82\x84\xac\x8e\x85\xcb\x84\xa4\x84\xa2\x8d\x88\xa4\xa9\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x4C\x88\x8b\xa4\x8e\x8d\xc0")
    death_list.append("\x2d\x48\xac\x80\x8b\xa7\x80\xa9\xa3\xac\xa3\x80\xa9\x2b\xac\x82\x8e\x8c\xa0\x8b\x80\x82\x84\x8d\x82\xa9\xcb\x88\xa3\xac\xa4\x87\x84\xac\x8a\x88\xa3\xa3\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x63\x87\x80\xa2\x88\xac\x62\x84\x83\xa3\xa4\x8e\x8d\x84\xc0")
    death_list.append("\x2d\x48\x8d\xac\xa4\x87\x84\xac\x8b\x8e\x8d\x86\xac\xa2\xa5\x8d\xac\xa7\x84\xac\x80\xa2\x84\xcb\x80\x8b\x8b\xac\x83\x84\x80\x83\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x4C\x80\xa9\x8d\x80\xa2\x83\xac\x4A\x84\xa9\x8d\x84\xa3\xc0")
    death_list.append("\x2d\x48\x0e\x8c\xac\x8d\x8e\xa4\xac\x80\x85\xa2\x80\x88\x83\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\x2b\xcb\x81\xa5\xa4\xac\x48\x0e\x8c\xac\x88\x8d\xac\x8d\x8e\xac\x87\xa5\xa2\xa2\xa9\xac\xa4\x8e\xcb\x83\x88\x84\x2a\xac\x48\xac\x87\x80\xa6\x84\xac\xa3\x8e\xac\x8c\xa5\x82\x87\xac\x48\xac\xa7\x80\x8d\xa4\xcb\xa4\x8e\xac\x83\x8e\xac\x85\x88\xa2\xa3\xa4\x2a\x2e\xac\x6d\x63\x2a\xac\x47\x80\xa7\x8a\x88\x8d\x86\xc0")
    death_list.append("\x2d\x45\x8e\xa2\xac\xa4\x88\xa3\xac\x8d\x8e\xa4\xac\x88\x8d\xac\x8c\x84\xa2\x84\xac\x83\x84\x80\xa4\x87\xcb\xa4\x87\x80\xa4\xac\x8c\x84\x8d\xac\x83\x88\x84\xac\x8c\x8e\xa3\xa4\x2a\x2e\xcb\xac\xac\x6d\x44\x8b\x88\xaa\x80\x81\x84\xa4\x87\xac\x41\x80\xa2\xa2\x84\xa4\xa4\xcb\xac\xac\xac\xac\xac\x41\xa2\x8e\xa7\x8d\x88\x8d\x86\xc0")
    death_list.append("\x2d\x43\x8e\xac\x8d\x8e\xa4\xac\x85\x84\x80\xa2\xac\x83\x84\x80\xa4\x87\xac\xa3\x8e\xac\x8c\xa5\x82\x87\xcb\x81\xa5\xa4\xac\xa2\x80\xa4\x87\x84\xa2\xac\xa4\x87\x84\xac\x88\x8d\x80\x83\x84\xa1\xa5\x80\xa4\x84\xcb\x8b\x88\x85\x84\x2a\x2e\xcb\xac\xac\x6d\x41\x84\xa2\xa4\x8e\x8b\xa4\xac\x41\xa2\x84\x82\x87\xa4\xc0")
    death_list.append("\x2d\x4D\x8e\xa4\x87\x88\x8d\x86\xac\x88\x8d\xac\x8b\x88\x85\x84\xac\x88\xa3\xcb\xa0\xa2\x8e\x8c\x88\xa3\x84\x83\xac\x84\xa8\x82\x84\xa0\xa4\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x4A\x80\x8d\xa9\x84\xac\x67\x84\xa3\xa4\xc0")
    death_list.append("\x2d\x4C\xa9\xac\x85\x84\x80\xa2\xac\xa7\x80\xa3\xac\x8d\x8e\xa4\xac\x8e\x85\xac\x83\x84\x80\xa4\x87\xcb\x88\xa4\xa3\x84\x8b\x85\x2b\xac\x81\xa5\xa4\xac\x80\xac\x83\x84\x80\xa4\x87\xac\xa7\x88\xa4\x87\x6d\xcb\x8e\xa5\xa4\xac\x8c\x84\x80\x8d\x88\x8d\x86\x2a\x2e\xcb\xac\xac\x6d\x47\xa5\x84\xa9\xac\x4D\x84\xa7\xa4\x8e\x8d\xc0")
    death_list.append("\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x89\xa5\xa3\xa4\xac\x8b\x88\x85\x84\x0e\xa3\xac\x8d\x84\xa8\xa4\xcb\x81\x88\x86\xac\x80\x83\xa6\x84\x8d\xa4\xa5\xa2\x84\x2a\x2e\xcb\xac\xac\x6d\x49\x2a\xac\x4A\x2a\xac\x62\x8e\xa7\x8b\x88\x8d\x86\xc0")
    death_list.append("\x2d\x41\x84\x82\x80\xa5\xa3\x84\xac\x8e\x85\xac\x88\x8d\x83\x88\x85\x85\x84\xa2\x84\x8d\x82\x84\x2b\xcb\x8e\x8d\x84\xac\x83\x88\x84\xa3\xac\x81\x84\x85\x8e\xa2\x84\xac\x8e\x8d\x84\xcb\x80\x82\xa4\xa5\x80\x8b\x8b\xa9\xac\x83\x88\x84\xa3\x2a\x2e\xcb\xac\xac\x6d\x44\x8b\x88\x84\xac\x67\x88\x84\xa3\x84\x8b\xc0")
    death_list.append("\x2d\x4C\xa5\xa3\xa4\xac\x8d\x8e\xa4\xac\x80\x8b\x8b\xac\xa4\x87\x88\x8d\x86\xa3\xac\x80\xa4\xcb\xa4\x87\x84\xac\x8b\x80\xa3\xa4\xac\x81\x84\xac\xa3\xa7\x80\x8b\x8b\x8e\xa7\x84\x83\xac\xa5\xa0\xcb\x88\x8d\xac\x83\x84\x80\xa4\x87\x0d\x2e\xcb\xac\xac\x6d\x60\x8b\x80\xa4\x8e\xc0")
    death_list.append("\x2d\x64\x87\x84\xa2\x84\xac\x88\xa3\xac\x8d\x8e\xac\x83\x84\x80\xa4\x87\x2b\xac\x8e\x8d\x8b\xa9\xcb\x80\xac\x82\x87\x80\x8d\x86\x84\xac\x8e\x85\xac\xa7\x8e\xa2\x8b\x83\xa3\x2a\x2e\xcb\xac\xac\x6d\x42\x87\x88\x84\x85\xac\x63\x84\x80\xa4\xa4\x8b\x84\xc0")
    death_list.append("\x2d\x48\xac\x87\x80\x83\xac\xa3\x84\x84\x8d\xac\x81\x88\xa2\xa4\x87\xac\x80\x8d\x83\xcb\x83\x84\x80\xa4\x87\xac\x81\xa5\xa4\xac\x87\x80\x83\xac\xa4\x87\x8e\xa5\x86\x87\xa4\xac\xa4\x87\x84\xa9\xcb\xa7\x84\xa2\x84\xac\x83\x88\x85\x85\x84\xa2\x84\x8d\xa4\x2a\x2e\xcb\xac\xac\x6d\x64\x2a\xac\x63\x2a\xac\x44\x8b\x88\x8e\xa4\xc0")
    death_list.append("\x2d\x42\xa5\xa2\x88\x8e\xa3\x88\xa4\xa9\xac\x88\xa3\xac\x8b\x88\x85\x84\x2a\xcb\x40\xa3\xa3\xa5\x8c\xa0\xa4\x88\x8e\x8d\xac\x88\xa3\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\xac\x6d\x4C\x80\xa2\x8a\xac\x60\x80\xa2\x8a\x84\xa2\xc0")
    death_list.append("\x2d\x48\xac\x85\x84\x84\x8b\xac\x8c\x8e\x8d\x8e\xa4\x8e\x8d\xa9\xac\x80\x8d\x83\xac\x83\x84\x80\xa4\x87\xcb\xa4\x8e\xac\x81\x84\xac\x80\x8b\x8c\x8e\xa3\xa4\xac\xa4\x87\x84\xac\xa3\x80\x8c\x84\x2a\x2e\xcb\xac\xac\x6d\x42\x87\x80\xa2\x8b\x8e\xa4\xa4\x84\xac\x41\xa2\x8e\x8d\xa4\x84\xc0")
    death_list.append("\x2d\x63\x8e\x8c\x84\xac\xa0\x84\x8e\xa0\x8b\x84\xac\x80\xa2\x84\xac\xa3\x8e\xac\x80\x85\xa2\x80\x88\x83\xcb\xa4\x8e\xac\x83\x88\x84\xac\xa4\x87\x80\xa4\xac\xa4\x87\x84\xa9\xac\x8d\x84\xa6\x84\xa2\xcb\x81\x84\x86\x88\x8d\xac\xa4\x8e\xac\x8b\x88\xa6\x84\x2a\x2e\xcb\xac\xac\x6d\x47\x84\x8d\xa2\xa9\xac\x66\x80\x8d\xac\x43\xa9\x8a\x84\xc0")
    death_list.append("\x2d\x64\x87\x84\xac\x81\x8e\x83\xa9\xac\x83\x88\x84\xa3\x2b\xac\x81\xa5\xa4\xac\xa4\x87\x84\xcb\xa3\xa0\x88\xa2\x88\xa4\xac\xa4\x87\x80\xa4\xac\xa4\xa2\x80\x8d\xa3\x82\x84\x8d\x83\xa3\xac\x88\xa4\xcb\x82\x80\x8d\x8d\x8e\xa4\xac\x81\x84\xac\xa4\x8e\xa5\x82\x87\x84\x83\xac\x81\xa9\xcb\x83\x84\x80\xa4\x87\x2a\x2e\xac\xac\x6d\x62\x80\x8c\x80\x8d\x80\xac\x4C\x80\x87\x80\xa2\xa3\x87\x88\xc0")
    death_list.append("\x2d\x67\x87\x84\xa4\x87\x84\xa2\xac\x85\x8e\xa2\xac\x8b\x88\x85\x84\xac\x8e\xa2\xcb\x83\x84\x80\xa4\x87\x2b\xac\x83\x8e\xac\xa9\x8e\xa5\xa2\xac\x8e\xa7\x8d\xac\xa7\x8e\xa2\x8a\xcb\xa7\x84\x8b\x8b\x2a\x2e\xcb\xac\xac\x6d\x49\x8e\x87\x8d\xac\x62\xa5\xa3\x8a\x88\x8d\xc0")
    death_list.append("\x2d\x64\x87\x84\xac\xa2\x84\xa0\x8e\xa2\xa4\xa3\xac\x8e\x85\xac\x8c\xa9\xac\x83\x84\x80\xa4\x87\xcb\x87\x80\xa6\x84\xac\x81\x84\x84\x8d\xac\x86\xa2\x84\x80\xa4\x8b\xa9\xcb\x84\xa8\x80\x86\x86\x84\xa2\x80\xa4\x84\x83\x2a\x2e\xcb\xac\xac\x6d\x4C\x80\xa2\x8a\xac\x64\xa7\x80\x88\x8d\xc0")
    death_list.append("\x2d\x64\x87\x84\xac\xa6\x80\x8b\x88\x80\x8d\xa4\xac\x8d\x84\xa6\x84\xa2\xac\xa4\x80\xa3\xa4\x84\xcb\x8e\x85\xac\x83\x84\x80\xa4\x87\xac\x81\xa5\xa4\xac\x8e\x8d\x82\x84\x2a\x2e\xcb\xac\xac\x6d\x67\x88\x8b\x8b\x88\x80\x8c\xac\x63\x87\x80\x8a\x84\xa3\xa0\x84\x80\xa2\x84\xc0")
    death_list.append("\x2d\x67\x84\xac\x8a\x8d\x8e\xa7\xac\xa4\x87\x84\xac\xa2\x8e\x80\x83\xac\xa4\x8e\xcb\x85\xa2\x84\x84\x83\x8e\x8c\xac\x87\x80\xa3\xac\x80\x8b\xa7\x80\xa9\xa3\xac\x81\x84\x84\x8d\xcb\xa3\xa4\x80\x8b\x8a\x84\x83\xac\x81\xa9\xac\x83\x84\x80\xa4\x87\x2a\x2e\xcb\xac\x6d\x40\x8d\x86\x84\x8b\x80\xac\x43\x80\xa6\x88\xa3\xc0")
    death_list.append("\x2d\x43\x84\xa3\xa0\x88\xa3\x84\xac\x8d\x8e\xa4\xac\x83\x84\x80\xa4\x87\x2b\xac\x81\xa5\xa4\xcb\xa7\x84\x8b\x82\x8e\x8c\x84\xac\x88\xa4\x2b\xac\x85\x8e\xa2\xac\x8d\x80\xa4\xa5\xa2\x84\xcb\xa7\x88\x8b\x8b\xa3\xac\x88\xa4\xac\x8b\x88\x8a\x84\xac\x80\x8b\x8b\xac\x84\x8b\xa3\x84\x2a\x2e\xcb\xac\xac\x6d\x4C\x80\xa2\x82\xa5\xa3\xac\x40\xa5\xa2\x84\x8b\x88\xa5\xa3\xc0")
    death_list.append("\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\x8d\x8e\xa4\xac\xa4\x87\x84\xac\xa7\x8e\xa2\xa3\xa4\xcb\xa4\x87\x80\xa4\xac\x82\x80\x8d\xac\x87\x80\xa0\xa0\x84\x8d\xac\xa4\x8e\xac\x8c\x84\x8d\x2a\x2e\xcb\xac\xac\x6d\x60\x8b\x80\xa4\x8e\xc0")
    death_list.append("\x2d\x4B\x88\x85\x84\xac\x8b\x84\xa6\x84\x8b\xa3\xac\x80\x8b\x8b\xac\x8c\x84\x8d\x2a\xcb\x43\x84\x80\xa4\x87\xac\xa2\x84\xa6\x84\x80\x8b\xa3\xac\xa4\x87\x84\xcb\x84\x8c\x88\x8d\x84\x8d\xa4\x2a\x2e\xcb\xac\xac\x6d\x46\x84\x8e\xa2\x86\x84\xac\x41\x84\xa2\x8d\x80\xa2\x83\xac\x63\x87\x80\xa7\xc0")
    death_list.append("\x2d\x43\x84\x80\xa4\x87\xac\x88\xa3\xac\xa4\x87\x84\xac\xa7\x88\xa3\x87\xac\x8e\x85\xcb\xa3\x8e\x8c\x84\x2b\xac\xa4\x87\x84\xac\xa2\x84\x8b\x88\x84\x85\xac\x8e\x85\xac\x8c\x80\x8d\xa9\x2b\xcb\x80\x8d\x83\xac\xa4\x87\x84\xac\x84\x8d\x83\xac\x8e\x85\xac\x80\x8b\x8b\x2a\x2e\xcb\xac\xac\x6d\x4B\xa5\x82\x88\xa5\xa3\xac\x40\x8d\x8d\x80\x84\xa5\xa3\xac\x63\x84\x8d\x84\x82\x80\xc0")
    death_list.append("\x2d\x43\x84\x80\xa4\x87\xac\xa7\x88\x8b\x8b\xac\x81\x84\xac\x80\xac\x86\xa2\x84\x80\xa4\xcb\xa2\x84\x8b\x88\x84\x85\x2a\xac\x4D\x8e\xac\x8c\x8e\xa2\x84\xcb\x88\x8d\xa4\x84\xa2\xa6\x88\x84\xa7\xa3\x2a\x2e\xcb\xac\xac\x6d\x4A\x80\xa4\x87\x80\xa2\x88\x8d\x84\xac\x47\x84\xa0\x81\xa5\xa2\x8d\xc0\xc0")
    if mode == 3:
        death_list.append("\x2d\x46\x88\xa4\xac\x86\xa5\x83\xac\xa3\x82\xa2\xa5\x81\x2a\x2e\xcb\xac\xac\x6d\x41\x80\x86\xa5\xc0")

    random.shuffle(death_list)

    # Will death text
    f.seek(int("d7c3",16)+rom_offset)
    f.write(death_list[0])

    # Change Fredan and Shadow death pointers
    f.seek(int("d7b2",16)+rom_offset)
    f.write("\xc2\xd7")
    f.seek(int("d7b8",16)+rom_offset)
    f.write("\xc2\xd7")

    ##########################################################################
    #                   Randomize item and ability placement
    ##########################################################################

    w=classes.World(rng_seed,mode,goal,logic_mode,statues,kara_location,gem,[inca_x+1,inca_y+1],hieroglyph_order)
    w.randomize()
    #w.print_spoiler()
    w.generate_spoiler(folder_dest, version, filename)
    w.write_to_rom(f)

    ##########################################################################
    #                        Randomize Ishtar puzzle
    ##########################################################################
    # Prepare file for uncompressed map data
    path_ishtarmapblank = folder + "ishtarmapblank.bin"
    path_ishtarmapnew = folder + "ishtarmap.bin"
    copyfile(path_ishtarmapblank,path_ishtarmapnew)

    # Add checks for Will's hair in each room
    f.seek(int("6dc53",16)+rom_offset)
    f.write("\x4c\x00\xdd\x86")
    f.seek(int("6dd00",16)+rom_offset)
    f.write("\x02\x45\x10\x00\x20\x10\x66\xdc\x02\x45\x30\x00\x40\x10\x66\xDC")
    f.write("\x02\x45\x50\x00\x60\x10\x66\xdc\x02\x45\x70\x00\x80\x10\x66\xDC")
    f.write("\x4c\x66\xdc\x86")

    # Generalize success text boxes
    # Make Rooms 1 and 3 equal to Room 2 text (which is already general)
    f.seek(int("6d978",16)+rom_offset)    # Room 1
    f.write("\x2c\xdb")
    f.seek(int("6d9ce",16)+rom_offset)    # Room 3
    f.write("\x2c\xdb")
    # Generalize Room 4 text
    f.seek(int("6d9f8",16)+rom_offset)
    f.write("\xc6\xdb")
    f.seek(int("6dbc6",16)+rom_offset)
    f.write("\xc2\x0a")

    f_ishtarmap = open(folder + "ishtarmap.bin","r+b")
    room_offsets = ["6d95e","6d98a","6d9b4","6d9de"]  # ROM addrs for cursor capture, by room
    coord_offsets = [3,8,15,20]                       # Offsets for xmin, xmax, ymin, ymax
    changes = [random.randint(1,8), random.randint(1,6), random.randint(1,4), random.randint(1,6)]

    # Set change for Room 1
    if changes[0] == 1:                        # Change right vase to light (vanilla)
        f_ishtarmap.seek(int("17b",16))
        f_ishtarmap.write("\x7b")
        f_ishtarmap.seek(int("18b",16))
        f_ishtarmap.write("\x84")
        coords = ["\xB0\x01","\xC0\x01","\x70\x00","\x90\x00"]

    elif changes[0] == 2:                      # Change middle vase to light
        f_ishtarmap.seek(int("175",16))
        f_ishtarmap.write("\x7b")
        f_ishtarmap.seek(int("185",16))
        f_ishtarmap.write("\x84")
        coords = ["\x50\x01","\x60\x01","\x70\x00","\x90\x00"]

    elif changes[0] == 3:                      # Change left vase to dark
        f_ishtarmap.seek(int("174",16))
        f_ishtarmap.write("\x83")
        f_ishtarmap.seek(int("184",16))
        f_ishtarmap.write("\x87")
        coords = ["\x40\x01","\x50\x01","\x70\x00","\x90\x00"]

    elif changes[0] == 4:                      # Change left shelf to empty
        f_ishtarmap.seek(int("165",16))
        f_ishtarmap.write("\x74")
        coords = ["\x50\x01","\x60\x01","\x58\x00","\x70\x00"]

    elif changes[0] == 5:                      # Change left shelf to books
        f_ishtarmap.seek(int("165",16))
        f_ishtarmap.write("\x76")
        coords = ["\x50\x01","\x60\x01","\x58\x00","\x70\x00"]

    elif changes[0] == 6:                      # Change right shelf to jar
        f_ishtarmap.seek(int("166",16))
        f_ishtarmap.write("\x75")
        coords = ["\x60\x01","\x70\x01","\x58\x00","\x70\x00"]

    elif changes[0] == 7:                      # Change right shelf to empty
        f_ishtarmap.seek(int("166",16))
        f_ishtarmap.write("\x74")
        coords = ["\x60\x01","\x70\x01","\x58\x00","\x70\x00"]

    elif changes[0] == 8:                      # Will's hair
        f.seek(int("6dd06",16)+rom_offset)
        f.write("\x5d")
        coords = ["\xa0\x01","\xc0\x01","\xb0\x00","\xd0\x00"]

    # Update cursor check ranges for Room 1
    for i in range(4):
        f.seek(int(room_offsets[0],16) + coord_offsets[i] + rom_offset)
        f.write(coords[i])



    # Set change for Room 2
    if changes[1] == 1:                        # Change both pots to dark (vanilla)
        f_ishtarmap.seek(int("3a3",16))
        f_ishtarmap.write("\x7c\x7c")
        f_ishtarmap.seek(int("3b3",16))
        f_ishtarmap.write("\x84\x84")
        coords = ["\x30\x03","\x50\x03","\xa0\x00","\xc0\x00"]

    elif changes[1] == 2:                      # Remove rock
        f_ishtarmap.seek(int("3bd",16))
        f_ishtarmap.write("\x73")
        coords = ["\xd0\x03","\xe0\x03","\xb0\x00","\xc0\x00"]

    elif changes[1] == 3:                      # Add round table
        f_ishtarmap.seek(int("395",16))
        f_ishtarmap.write("\x7d\x7e")
        f_ishtarmap.seek(int("3a5",16))
        f_ishtarmap.write("\x85\x86")
        f_ishtarmap.seek(int("3b5",16))
        f_ishtarmap.write("\x8d\x8e")
        coords = ["\x50\x03","\x70\x03","\x90\x00","\xb0\x00"]

    elif changes[1] == 4:                      # Add sconce
        f_ishtarmap.seek(int("357",16))
        f_ishtarmap.write("\x88\x89")
        f_ishtarmap.seek(int("367",16))
        f_ishtarmap.write("\x90\x91")
        coords = ["\x70\x03","\x90\x03","\x50\x00","\x70\x00"]

    elif changes[1] == 5:                      # Add rock
        f_ishtarmap.seek(int("3b2",16))
        f_ishtarmap.write("\x77")
        coords = ["\x20\x03","\x30\x03","\xb0\x00","\xc0\x00"]

    elif changes[1] == 6:                      # Will's hair
        f.seek(int("6dd0e",16)+rom_offset)
        f.write("\x5d")
        coords = ["\x90\x03","\xb0\x03","\xa0\x00","\xc0\x00"]

    # Update cursor check ranges for Room 2
    for i in range(4):
        f.seek(int(room_offsets[1],16) + coord_offsets[i] + rom_offset)
        f.write(coords[i])



    # Set change for Room 3
    # Check for chest contents, only change map if contents are the same
    if w.item_locations[80][3] == w.item_locations[81][3]:
        if changes[2] == 1:                        # Remove rock
            f_ishtarmap.seek(int("5bd",16))
            f_ishtarmap.write("\x73")
            coords = ["\xd0\x05","\xe0\x05","\xb0\x00","\xc0\x00"]

        elif changes[2] == 2:                      # Add rock
            f_ishtarmap.seek(int("5b2",16))
            f_ishtarmap.write("\x77")
            coords = ["\x20\x05","\x30\x05","\xb0\x00","\xc0\x00"]

        elif changes[2] == 3:                      # Add sconce
            f_ishtarmap.seek(int("557",16))
            f_ishtarmap.write("\x88\x89")
            f_ishtarmap.seek(int("567",16))
            f_ishtarmap.write("\x90\x91")
            coords = ["\x70\x05","\x90\x05","\x50\x00","\x70\x00"]

        elif changes[2] == 4:                      # Will's hair
            f.seek(int("6dd16",16)+rom_offset)
            f.write("\x5d")
            coords = ["\x90\x05","\xb0\x05","\xa0\x00","\xc0\x00"]

        # Update cursor check ranges for Room 3 (only if chest contents different)
        for i in range(4):
            f.seek(int(room_offsets[2],16) + coord_offsets[i] + rom_offset)
            f.write(coords[i])



    # Set change for Room 4
    if changes[3] == 1:                      # Will's hair (vanilla)
        f.seek(int("6dd1e",16)+rom_offset)
        f.write("\x5d")

    else:
        if changes[3] == 2:                        # Remove rock
            f_ishtarmap.seek(int("7bd",16))
            f_ishtarmap.write("\x73")
            coords = ["\xd0\x07","\xe0\x07","\xb0\x00","\xc0\x00"]

        elif changes[3] == 3:                      # Add rock
            f_ishtarmap.seek(int("7b2",16))
            f_ishtarmap.write("\x77")
            coords = ["\x20\x07","\x30\x07","\xb0\x00","\xc0\x00"]

        elif changes[3] == 4:                      # Add vase L
            f_ishtarmap.seek(int("7a3",16))
            f_ishtarmap.write("\x7c")
            f_ishtarmap.seek(int("7b3",16))
            f_ishtarmap.write("\x84")
            coords = ["\x30\x07","\x40\x07","\xa0\x00","\xc0\x00"]

        elif changes[3] == 5:                      # Add vase R
            f_ishtarmap.seek(int("7ac",16))
            f_ishtarmap.write("\x7c")
            f_ishtarmap.seek(int("7bc",16))
            f_ishtarmap.write("\x84")
            coords = ["\xc0\x07","\xd0\x07","\xa0\x00","\xc0\x00"]

        elif changes[3] == 6:                      # Crease in floor
            f_ishtarmap.seek(int("7b4",16))
            f_ishtarmap.write("\x69\x6a")
            coords = ["\x40\x07","\x60\x07","\xb0\x00","\xc8\x00"]

        # Update cursor check ranges for Room 3 (only if not hair)
        for i in range(4):
            f.seek(int(room_offsets[3],16) + coord_offsets[i] + rom_offset)
            f.write(coords[i])



    # Compress map data and write to file
    f_ishtarmapcomp = open(folder + "ishtarmapcomp.bin","r+b")
    f_ishtarmapcomp.seek(0)
    f_ishtarmap.seek(0)
    f_ishtarmapcomp.write(quintet_comp.compress(f_ishtarmap.read()))
    f_ishtarmapcomp.seek(0)
    f_ishtarmap.close

    # Insert new compressed map data
    #f.seek(int("193d25",16)+rom_offset)
    f.seek(int("1f4100",16)+rom_offset)
    f.write("\x08\x02")
    f.write(f_ishtarmapcomp.read())
    f_ishtarmapcomp.close

    # Direct map arrangement pointer to new data - NO LONGER NECESSARY
    #f.seek(int("d977e",16)+rom_offset)
    #f.write("\x00\x41")

    ##########################################################################
    #                        Close file and return
    ##########################################################################
    f.close

    return True
