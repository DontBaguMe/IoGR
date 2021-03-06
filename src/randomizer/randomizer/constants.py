class Constants:
    INACCESSIBLE = 1000
    MAX_CYCLES = 100
    MAX_INVENTORY = 15

    # Database of enemy types
    # FORMAT: { ID: [Enemyset, Event addr, VanillaTemplate,
    #           Type(1=stationary,2=walking,3=flying),OnWalkableTile,CanBeRandom,Name]}
    ENEMIES = {
        # Underground Tunnel
        0: [0, b"\x55\x87\x8a", b"\x05", 2, True, True, "Bat"],  # a8755
        1: [0, b"\x6c\x82\x8a", b"\x01", 2, True, True, "Ribber"],
        2: [0, b"\x00\x80\x8a", b"\x02", 1, False, True, "Canal Worm"],
        3: [0, b"\xf7\x85\x8a", b"\x03", 2, True, False, "King Bat"],
        4: [0, b"\x76\x84\x8a", b"\x10", 2, True, True, "Skull Chaser"],
        5: [0, b"\xff\x86\x8a", b"\x04", 2, True, False, "Bat Minion 1"],
        6: [0, b"\x9a\x86\x8a", b"\x04", 2, True, False, "Bat Minion 2"],
        7: [0, b"\x69\x86\x8a", b"\x04", 2, True, False, "Bat Minion 3"],
        8: [0, b"\xcb\x86\x8a", b"\x04", 2, True, False, "Bat Minion 4"],

        # Inca Ruins
        10: [1, b"\xb7\x8d\x8a", b"\x0b", 2, True, True, "Slugger"],
        11: [1, b"\xb6\x8e\x8a", b"\x0b", 2, True, False, "Scuttlebug"],
        12: [1, b"\x1b\x8b\x8a", b"\x0a", 2, True, True, "Mudpit"],
        13: [1, b"\x70\x8c\x8a", b"\x0c", 1, True, True, "Four Way"],
        14: [2, b"\xee\x97\x8a", b"\x0f", 2, True, True, "Splop"],
        15: [2, b"\xbc\x98\x8a", b"\x0e", 3, False, True, "Whirligig"],
        16: [2, b"\xc2\x95\x8a", b"\x0d", 2, True, False, "Stone Lord R"],  # shoots fire
        17: [2, b"\xb3\x95\x8a", b"\x0d", 2, True, True, "Stone Lord D"],  # shoots fire
        18: [2, b"\xb8\x95\x8a", b"\x0d", 2, True, False, "Stone Lord U"],  # shoots fire
        19: [2, b"\xbd\x95\x8a", b"\x0d", 2, True, False, "Stone Lord L"],  # shoots fire
        # throws spears
        20: [2, b"\x70\x90\x8a", b"\x0d", 2, True, False, "Stone Guard R"],
        # throws spears
        21: [2, b"\x6b\x90\x8a", b"\x0d", 2, True, False, "Stone Guard L"],
        # throws spears
        22: [2, b"\x61\x90\x8a", b"\x0d", 2, True, True, "Stone Guard D"],
        23: [2, b"\xc3\x99\x8a", b"\x0e", 1, False, False, "Whirligig (stationary)"],

        # Diamond Mine
        30: [3, b"\xca\xaa\x8a", b"\x18", 2, True, True, "Flayzer 1"],
        31: [3, b"\x54\xaa\x8a", b"\x18", 2, True, False, "Flayzer 2"],
        32: [3, b"\x8a\xaa\x8a", b"\x18", 2, True, False, "Flayzer 3"],
        33: [3, b"\x03\xb1\x8a", b"\x19", 2, True, True, "Eye Stalker"],
        34: [3, b"\xb3\xb0\x8a", b"\x19", 2, True, False, "Eye Stalker (stone)"],
        35: [3, b"\xf5\xaf\x8a", b"\x1a", 1, True, True, "Grundit"],
        #            36: [3,b"\xf5\xa4\x8a",b"\x1a","Grundit (stationary)"],  # Can't randomize this guy

        # Sky Garden
        40: [4, b"\xb0\xb4\x8a", b"\x1d", 2, True, True, "Blue Cyber"],
        41: [4, b"\x20\xc5\x8a", b"\x1b", 2, True, True, "Dynapede 1"],
        42: [4, b"\x33\xc5\x8a", b"\x1b", 2, True, False, "Dynapede 2"],
        43: [5, b"\xb0\xb8\x8a", b"\x1e", 2, True, True, "Red Cyber"],
        44: [5, b"\x16\xc8\x8a", b"\x1c", 2, True, True, "Nitropede"],

        # Mu
        50: [6, b"\xcc\xe6\x8a", b"\x2b", 2, True, True, "Slipper"],
        51: [6, b"\x5c\xe4\x8a", b"\x2a", 2, True, True, "Skuddle"],
        52: [6, b"\x9e\xdd\x8a", b"\x28", 2, True, True, "Cyclops"],
        53: [6, b"\x6e\xe2\x8a", b"\x29", 3, True, True, "Flasher"],
        54: [6, b"\x07\xde\x8a", b"\x28", 2, True, False, "Cyclops (asleep)"],
        55: [6, b"\xf4\xe6\x8a", b"\x2b", 2, True, True, "Slipper (falling)"],

        # Angel Dungeon
        60: [7, b"\x9f\xee\x8a", b"\x2d", 3, False, True, "Dive Bat"],
        61: [7, b"\x51\xea\x8a", b"\x2c", 2, True, True, "Steelbones"],
        # False for now...
        62: [7, b"\x33\xef\x8a", b"\x2e", 1, True, True, "Draco"],
        63: [7, b"\xc7\xf0\x8a", b"\x2e", 1, True, True, "Ramskull"],

        # Great Wall
        70: [8, b"\x55\x91\x8b", b"\x33", 2, True, True, "Archer 1"],
        71: [8, b"\xfe\x8e\x8b", b"\x33", 2, True, False, "Archer Statue"],
        72: [8, b"\xbe\x8d\x8b", b"\x34", 2, True, True, "Eyesore"],
        73: [8, b"\x70\x8c\x8b", b"\x35", 3, False, True, "Fire Bug 1"],
        74: [8, b"\x70\x8c\x8b", b"\x33", 3, False, False, "Fire Bug 2"],
        75: [8, b"\x23\x94\x8b", b"\x32", 2, True, True, "Asp"],
        76: [8, b"\x65\x91\x8b", b"\x33", 2, True, False, "Archer 2"],
        77: [8, b"\x77\x91\x8b", b"\x33", 2, True, False, "Archer 3"],
        78: [8, b"\x72\x8f\x8b", b"\x46", 2, True, False, "Archer Statue (switch) 1"],
        79: [8, b"\x4f\x8f\x8b", b"\x33", 2, True, False, "Archer Statue (switch) 2"],

        # Mt. Kress
        80: [9, b"\xac\x9b\x8b", b"\x3e", 3, True, True, "Skulker (N/S)"],
        81: [9, b"\x4e\x9c\x8b", b"\x3e", 3, True, True, "Skulker (E/W)"],
        82: [9, b"\x44\x9c\x8b", b"\x3e", 3, True, False, "Skulker (E/W)"],
        83: [9, b"\xa2\x9b\x8b", b"\x3e", 3, True, False, "Skulker (E/W)"],
        84: [9, b"\x8b\x9e\x8b", b"\x3d", 3, False, True, "Yorrick (E/W)"],
        85: [9, b"\x53\x9f\x8b", b"\x3d", 3, False, False, "Yorrick (E/W)"],
        86: [9, b"\x0f\x9d\x8b", b"\x3d", 3, False, True, "Yorrick (N/S)"],
        87: [9, b"\xcd\x9d\x8b", b"\x3d", 3, False, False, "Yorrick (N/S)"],
        88: [9, b"\x3b\x98\x8b", b"\x3f", 3, False, True, "Fire Sprite"],
        89: [9, b"\xcf\xa0\x8b", b"\x3c", 2, True, True, "Acid Splasher"],
        90: [9, b"\xa1\xa0\x8b", b"\x3c", 2, True, False, "Acid Splasher (stationary E)"],
        91: [9, b"\x75\xa0\x8b", b"\x3c", 2, True, False, "Acid Splasher (stationary W)"],
        92: [9, b"\x49\xa0\x8b", b"\x3c", 2, True, False, "Acid Splasher (stationary S)"],
        93: [9, b"\x1d\xa0\x8b", b"\x3c", 2, True, False, "Acid Splasher (stationary N)"],

        # Ankor Wat
        100: [10, b"\xd7\xb1\x8b", b"\x49", 2, True, True, "Shrubber"],
        101: [10, b"\xb4\xb1\x8b", b"\x49", 2, True, False, "Shrubber 2"],
        102: [10, b"\x75\xb2\x8b", b"\x46", 2, True, True, "Zombie"],
        # False for now...
        103: [10, b"\x4f\xaf\x8b", b"\x4a", 3, True, True, "Zip Fly"],
        104: [11, b"\x8d\xbd\x8b", b"\x42", 3, True, True, "Goldcap"],
        105: [11, b"\x25\xb8\x8b", b"\x45", 2, True, True, "Gorgon"],
        106: [11, b"\x17\xb8\x8b", b"\x45", 2, True, False, "Gorgon (jump down)"],
        107: [11, b"\xbb\xbf\x8b", b"\x43", 2, True, False, "Frenzie"],
        108: [11, b"\xd0\xbf\x8b", b"\x43", 2, True, True, "Frenzie 2"],
        109: [11, b"\x66\xbb\x8b", b"\x44", 1, False, True, "Wall Walker"],
        110: [11, b"\x66\xbb\x8b", b"\x3a", 1, False, False, "Wall Walker 2"],
        111: [11, b"\x5c\xbb\x8b", b"\x44", 1, False, False, "Wall Walker 3"],
        112: [11, b"\x5c\xbb\x8b", b"\x3a", 1, False, False, "Wall Walker 4"],
        113: [11, b"\xaf\x99\x88", b"\x45", 2, True, False, "Gorgon (block)"],

        # Pyramid
        120: [12, b"\x5f\xc6\x8b", b"\x4f", 1, True, True, "Mystic Ball (stationary)"],
        121: [12, b"\xfc\xc5\x8b", b"\x4f", 2, True, True, "Mystic Ball"],
        122: [12, b"\xa3\xc5\x8b", b"\x4f", 2, True, True, "Mystic Ball"],
        123: [12, b"\x9d\xc3\x8b", b"\x4e", 2, True, True, "Tuts"],
        124: [12, b"\x98\xc7\x8b", b"\x51", 1, True, True, "Blaster"],
        125: [12, b"\x84\xc1\x8b", b"\x4c", 2, True, False, "Haunt (stationary)"],
        126: [12, b"\xa7\xc1\x8b", b"\x4c", 2, True, True, "Haunt"],

        # Babel Tower
        #   130: [14,b"\xd7\x99\x8a",b"\x5a","Castoth (boss)"],
        #   131: [14,b"\xd5\xd0\x8a",b"\x5b","Viper (boss)"],
        #   132: [14,b"\x50\xf1\x8a",b"\x5c","Vampire (boss)"],
        #   133: [14,b"\x9c\xf1\x8a",b"\x5c","Vampire (boss)"],
        #   134: [14,b"\x00\x80\x8b",b"\x5d","Sand Fanger (boss)"],
        #   135: [14,b"\x1a\xa6\x8b",b"\x5e","Mummy Queen (boss)"],

        # Jeweler's Mansion
        140: [13, b"\xca\xaa\x8a", b"\x61", 2, True, True, "Flayzer"],
        141: [13, b"\xf5\xaf\x8a", b"\x63", 1, True, True, "Grundit"],
        142: [13, b"\xd8\xb0\x8a", b"\x62", 2, True, False, "Eye Stalker 1"],
        143: [13, b"\x03\xb1\x8a", b"\x62", 2, True, True, "Eye Stalker 2"]

        # Bosses
        #   24: [15,b"\x03\x9b\x8a",b"\x14","Castoth (boss)"],
        #   45: [15,b"\x6f\xd1\x8a",b"\x27","Viper (boss)"],
        #   55: [15,b"\xf7\xf1\x8a",b"\x2f","Vampire (boss)"],
        #   56: [15,b"\xc8\xf3\x8a",b"\x30","Vampire (boss)"],
        #   79: [15,b"\x5c\x81\x8b",b"\x36","Sand Fanger (boss)"],
        #   128: [15,b"\xb6\xa6\x8b",b"\x50","Mummy Queen (boss)"],
        #   143: [15,b"\x09\xf7\x88",b"\x5f","Solid Arm (boss)"],
        #   140: [15,b"\xaa\xee\x8c",b"\x54","Dark Gaia"]

    }
    # Database of non-enemy sprites to disable in enemizer
    # FORMAT: { ID: [Enemyset, Event addr, Name]}
    NOENEMY_SPRITES = {
        # Underground Tunnel
        0: [0, "a8835", "Movable statue"],
        1: [0, "a87ce", "Falling spear 1"],
        2: [0, "a87c3", "Falling spear 2"],
        3: [0, "a8aae", "Spike ball 1"],
        4: [0, "a8a0f", "Spike ball 2"],
        5: [0, "a8a7d", "Spike ball 3"],
        6: [0, "a8a46", "Spike ball 4"],
        7: [0, "a89de", "Spike ball 5"],

        # Inca Ruins
        10: [1, "9c26f", "Skeleton 1"],
        11: [1, "9c798", "Skeleton 2"],
        #            12: [1,"9c89d","Skeleton 3"],   # Spriteset already restricted for this room
        13: [1, "9c8f7", "Skeleton 4"],
        14: [1, "a8896", "Broken statue (chest)"],
        15: [1, "a88de", "Broken statue (blockade)"],

        # Diamond Mine
        20: [3, "5d6a8", "Elevator sign"],
        21: [3, "aa4f5", "Elevator platform 1"],
        22: [3, "aa50c", "Elevator platform 2"],
        23: [3, "aa4e2", "Elevator platform 3"],

        # Sky Garden
        30: [4, "5f8c0", "Broken statue"],
        31: [4, "ac0fe", "Sword statue 1"],
        #            32: [4,"ac150","Sword statue 2"],
        33: [4, "ac3b3", "Sword statue 3"],
        #            34: [4,"ac409","Sword statue 4"],
        35: [4, "accd4", "Fire snake (top)"],
        36: [5, "accf1", "Fire snake (bottom)"],

        # Mu
        40: [6, "69ce9", "Floor spikes 1"],
        41: [6, "69d1f", "Floor spikes 2"],
        42: [6, "ae943", "Fire snake"],
        #            43: [6,"69d4d","Donut"],

        # Angel
        50: [7, "6d56f", "Flame 1"],
        51: [7, "6d57e", "Flame 2"],
        52: [7, "6d58f", "Flame 3"],

        # Great Wall
        60: [8, "b8c30", "Wall spike 1"],
        61: [8, "b8bf8", "Wall spike 2"],
        62: [8, "7bd17", "Wall spike 3"],
        63: [8, "7bd46", "Wall spike 4"],
        64: [8, "7bd75", "Wall spike 5"],
        65: [8, "7bce8", "Wall spike 5"],

        # Mt Kress (nothing)

        # Ankor Wat
        80: [11, "89f2c", "Floating crystal"],
        81: [11, "89ffc", "Skeleton 1"],
        82: [11, "8a25e", "Skeleton 2"]

        # Pyramid
        #            90: [12,"8b6a2","Warp point"],
        #            91: [12,"8cd6c","Warp point"],

        # Jeweler's Mansion (nothing)
    }
    # Database of enemy groups and spritesets
    # FORMAT: { ID: [ROM_Loction, HeaderCode, HeaderData, Name]}
    ENEMY_SETS = {
        0: [b"\x03\x00\x10\x10\xEC\x59\xCD\x01\x04\x00\x60\xA0\x8C\x75\xDE\x10\xD0\x21\x00\x47\xED\x9F", "Underground Tunnel"],
        1: [b"\x03\x00\x10\x10\xBC\x33\xC2\x01\x04\x00\x60\xA0\x0C\x77\xDE\x10\x2A\x0F\x00\xE6\x08\xD5", "Inca Ruins (Mud Monster and Larva)"],
        2: [b"\x03\x00\x10\x10\x23\x4D\xC2\x01\x04\x00\x60\xA0\xCC\x77\xDE\x10\x36\x23\x00\x24\x45\xCC", "Inca Ruins (Statues)"],
        3: [b"\x03\x00\x10\x10\x16\x5C\xCC\x01\x04\x00\x60\xA0\xCC\x7A\xDE\x10\x30\x29\x00\xBE\x2F\xCB", "Diamond Mine"],
        4: [b"\x03\x00\x10\x10\x62\x3D\xCF\x01\x04\x00\x60\xA0\x4C\x7C\xDE\x10\x54\x1D\x00\xEF\xEE\x9E", "Sky Garden (top)"],
        5: [b"\x03\x00\x10\x10\x62\x3D\xCF\x01\x04\x00\x60\xA0\x0C\x7D\xDE\x10\x54\x1D\x00\xEF\xEE\x9E", "Sky Garden (bottom)"],
        6: [b"\x03\x00\x10\x10\x2D\x2E\xCC\x01\x04\x00\x60\xA0\x00\x00\xDF\x10\x16\x1C\x00\x41\x36\xD1", "Mu"],
        7: [b"\x03\x00\x10\x10\xD1\x14\xCF\x01\x04\x00\x60\xA0\x40\x02\xDF\x10\x7F\x0F\x00\x2C\x2B\xD5", "Angel Dungeon"],
        8: [b"\x03\x00\x10\x10\x6D\x13\xD0\x01\x04\x00\x60\xA0\x40\x05\xDF\x10\xFF\x16\x00\xF7\xF3\x99", "Great Wall"],
        9: [b"\x03\x00\x10\x10\x00\x00\xD0\x01\x04\x00\x60\xA0\x40\x08\xDF\x10\x70\x0E\x00\x5C\x4D\xD8", "Mt. Kress"],
        10: [b"\x03\x00\x10\x10\xEA\x15\xCE\x01\x04\x00\x70\x90\x53\x55\xDE\x10\xD5\x14\x00\x08\x73\xCC", "Ankor Wat (outside)"],
        11: [b"\x03\x00\x10\x10\x81\x6A\xC1\x01\x04\x00\x70\x90\x13\x57\xDE\x10\x57\x10\x00\x5F\x39\xD4", "Ankor Wat (inside)"],
        12: [b"\x03\x00\x10\x10\x0d\x18\xcb\x01\x04\x00\x60\x90\x80\x0a\xdf\x10\xfb\x13\x00\x0e\x67\xd1", "Pyramid"],
        13: [b"\x03\x00\x10\x10\x16\x5C\xCC\x01\x04\x00\x60\xA0\xC0\x0C\xDF\x10\x30\x29\x00\xBE\x2F\xCB", "Jeweler's Mansion"]
    }
    # World graph is initially populated only with "free" edges
    # Format: { Region ID: Traversed flag, [Accessible regions], Region Name],
    #                                                       ItemsToRemove }
    GRAPH = {
        -1: [False, [0], "Game Start", []],
        0:  [False, [7, 14, 15, 74], "South Cape", [9]],
        74: [False, [], "Jeweler Access", []],
        1:  [False, [], "Jeweler Reward 1", []],
        2:  [False, [], "Jeweler Reward 2", []],
        3:  [False, [], "Jeweler Reward 3", []],
        4:  [False, [], "Jeweler Reward 4", []],
        5:  [False, [], "Jeweler Reward 5", []],
        6:  [False, [], "Jeweler Reward 6", []],
        7:  [False, [0, 8, 14, 15], "Edward's Castle", []],
        8:  [False, [], "Edward's Prison", [2]],
        9:  [False, [], "Underground Tunnel - Behind Prison Key", []],
        10: [False, [7, 9], "Underground Tunnel - Behind Lilly", []],
        12: [False, [0, 7, 14, 15], "Itory Village", [23]],
        13: [False, [], "Itory Cave", []],
        75: [False, [], "Got Lilly", []],
        14: [False, [0, 7, 15], "Moon Tribe", [25]],
        73: [False, [], "Moon Tribe Cave", []],
        15: [False, [0, 7, 14], "Inca Ruins", [7]],
        16: [False, [15], "Inca Ruins - Behind Diamond Tile & Psycho Dash", [8]],
        17: [False, [], "Inca Ruins - Behind Wind Melody", [3, 4]],
        18: [False, [19], "Inca Ruins - Castoth", []],
        19: [False, [20], "Gold Ship", []],
        20: [False, [21, 22, 27, 28], "Diamond Coast", []],
        21: [False, [20, 22, 27, 28, 74], "Freejia", []],
        22: [False, [20, 21, 27, 28], "Diamond Mine", [15]],
        23: [False, [], "Diamond Mine - Behind Psycho Dash", []],
        24: [False, [], "Diamond Mine - Behind Dark Friar", []],
        25: [False, [], "Diamond Mine - Behind Elevator Key", [11, 12]],
        26: [False, [], "Diamond Mine - Behind Mine Keys", []],
        27: [False, [20, 21, 22, 28], "Neil's Cottage", [13]],
        28: [False, [20, 21, 22, 27, 29], "Nazca Plain", []],
        29: [False, [28], "Sky Garden", [14, 14, 14, 14]],
        30: [False, [72], "Sky Garden - Behind Dark Friar", []],
        72: [False, [], "Sky Garden - Behind Friar or Barrier", []],
        31: [False, [], "Sky Garden - Behind Psycho Dash", []],
        32: [False, [33], "Sky Garden - Viper", []],
        33: [False, [], "Seaside Palace", [16, 17]],
        34: [False, [], "Seaside Palace - Behind Purification Stone", []],
        35: [False, [], "Seaside Palace - Behind Necklace", []],
        36: [False, [37, 42], "Seaside Palace - Mu Passage", [16]],
        37: [False, [], "Mu", [18]],
        38: [False, [], "Mu - Behind Hope Statue 1", [18]],
        71: [False, [], "Mu - Behind Dark Friar", []],
        39: [False, [], "Mu - Behind Psycho Slide", []],
        40: [False, [], "Mu - Behind Hope Statue 2", [19, 19]],
        41: [False, [], "Mu - Vampires", []],
        42: [False, [36, 44, 45, 74], "Angel Village", []],
        43: [False, [], "Angel Village Dungeon", []],
        44: [False, [42, 45, 74], "Watermia", [24]],
        45: [False, [42, 44, 45, 80], "Great Wall", []],
        80: [False, [], "Great Wall - Behind Ramp", []],
        46: [False, [], "Great Wall - Behind Dark Friar", []],
        47: [False, [46], "Great Wall - Sand Fanger", []],
        48: [False, [54, 56, 74], "Euro", [24, 40]],
        49: [False, [], "Euro - Ann's Item", []],
        50: [False, [], "Mt. Temple", [26]],
        51: [False, [], "Mt. Temple - Behind Drops 1", [26]],
        52: [False, [], "Mt. Temple - Behind Drops 2", [26]],
        53: [False, [], "Mt. Temple - Behind Drops 3", []],
        54: [False, [48, 56], "Natives' Village", [10, 29]],
        55: [False, [], "Natives' Village - Statue Item", []],
        56: [False, [48, 54], "Ankor Wat", []],
        76: [False, [56], "Ankor Wat - Garden", []],
        57: [False, [56, 76], "Ankor Wat - Behind Psycho Slide & Spin Dash", []],
        58: [False, [], "Ankor Wat - Behind Dark Friar", []],
        59: [False, [56], "Ankor Wat - Behind Earthquaker", []],
        60: [False, [76], "Ankor Wat - Behind Black Glasses", []],
        61: [False, [54, 74], "Dao", []],
        62: [False, [61], "Pyramid", [30, 31, 32, 33, 34, 35, 38]],
        77: [False, [62], "Pyramid - Bottom Level", []],
        63: [False, [77, 78, 79], "Pyramid - Behind Aura", []],
        64: [False, [77], "Pyramid - Behind Spin Dash", []],
        78: [False, [77], "Pyramid - Behind Dark Friar", []],
        79: [False, [77], "Pyramid - Behind Earthquaker", []],
        65: [False, [], "Pyramid - Mummy Queen", [38]],
        66: [False, [], "Babel Tower", []],
        67: [False, [61], "Babel Tower - Behind Crystal Ring and Aura", []],
        68: [False, [61], "Jeweler's Mansion", []],
        69: [False, [], "Rescue Kara", []],
        70: [False, [], "Dark Gaia", []]
    }
    # Define Item/Ability/Statue locations
    # Format: { ID: [Region, Type (1=item,2=ability,3=statue), Filled Flag,
    #                Filled Item, Restricted Items, Item Addr, Text Addr, Text2 Addr,
    #                Special (map# or inventory addr), Name, Swapped Flag]}
    #         (For random start, [6]=Type, [7]=XY_spawn_data)
    ITEM_LOCATIONS = {
        0:  [1, 1, False, 0, [], "8d019", "8d19d", "", "8d260",     "Jeweler Reward 1                    "],
        1:  [2, 1, False, 0, [], "8d028", "8d1ba", "", "8d274",     "Jeweler Reward 2                    "],
        2:  [3, 1, False, 0, [], "8d037", "8d1d7", "", "8d288",     "Jeweler Reward 3                    "],
        3:  [4, 1, False, 0, [], "8d04a", "8d1f4", "", "8d29c",     "Jeweler Reward 4                    "],
        4:  [5, 1, False, 0, [], "8d059", "8d211", "", "8d2b0",     "Jeweler Reward 5                    "],
        5:  [6, 1, False, 0, [], "8d069", "8d2ea", "", "8d2c4",     "Jeweler Reward 6                    "],

        6:  [0, 1, False, 0, [], "F51D", "F52D", "F543", "",        "South Cape: Bell Tower              "],
        # text2 was 0c6a1
        7:  [0, 1, False, 0, [], "4846e", "48479", "", "",          "South Cape: Fisherman               "],
        8:  [0, 1, False, 0, [], "F59D", "F5AD", "F5C3", "",        "South Cape: Lance's House           "],
        9:  [0, 1, False, 0, [], "499e4", "49be5", "", "",          "South Cape: Lola                    "],
        10: [0, 2, False, 0, [51, 52, 53], "c830a", "Safe", b"\xE0\x00\x70\x00\x83\x00\x43", b"\x01",
             "South Cape: Dark Space              "],

        11: [7, 1, False, 0, [], "4c214", "4c299", "", "",          "Edward's Castle: Hidden Guard       "],
        12: [7, 1, False, 0, [], "4d0ef", "4d141", "", "",          "Edward's Castle: Basement           "],

        # text 4d5f4?
        13: [8, 1, False, 0, [], "4d32f", "4d4b1", "", "",          "Edward's Prison: Hamlet             "],
        14: [8, 2, False, 0, [51, 52, 53], "c8637", "", "", b"\x0b",   "Edward's Prison: Dark Space         "],

        15: [9, 1, False, 0, [2], "1AFA9", "", "", "",              "Underground Tunnel: Spike's Chest   "],
        16: [9, 1, False, 0, [2], "1AFAE", "", "", "",              "Underground Tunnel: Small Room Chest"],
        17: [10, 1, False, 0, [2], "1AFB3", "", "", "",             "Underground Tunnel: Ribber's Chest  "],
        18: [10, 1, False, 0, [], "F61D", "F62D", "F643", "",       "Underground Tunnel: Barrels         "],
        19: [10, 2, True, 0, [], "c8aa2", "Unsafe", b"\xA0\x00\xD0\x04\x83\x00\x74", b"\x12",
             "Underground Tunnel: Dark Space      "],   # Always open

        20: [12, 1, False, 0, [9], "F69D", "F6AD", "F6C3", "",      "Itory Village: Logs                 "],
        21: [13, 1, False, 0, [9], "4f375", "4f38d", "4f3a8", "",   "Itory Village: Cave                 "],
        22: [12, 2, False, 0, [51, 52, 53], "c8b34", "Safe", b"\x30\x04\x90\x00\x83\x00\x35", b"\x15",
             "Itory Village: Dark Space           "],

        23: [73, 1, False, 0, [], "4fae1", "4faf9", "4fb16", "",    "Moon Tribe: Cave                    "],

        24: [15, 1, False, 0, [], "1AFB8", "", "", "",              "Inca Ruins: Diamond-Block Chest     "],
        25: [16, 1, False, 0, [7], "1AFC2", "", "", "",             "Inca Ruins: Broken Statues Chest    "],
        26: [16, 1, False, 0, [7], "1AFBD", "", "", "",             "Inca Ruins: Stone Lord Chest        "],
        27: [16, 1, False, 0, [7], "1AFC6", "", "", "",             "Inca Ruins: Slugger Chest           "],
        28: [16, 1, False, 0, [7], "9c5bd", "9c614", "9c637", "",   "Inca Ruins: Singing Statue          "],
        29: [16, 2, True, 0, [], "c9302", "Unsafe", b"\x10\x01\x90\x00\x83\x00\x32", b"\x28",
             "Inca Ruins: Dark Space 1            "],   # Always open
        30: [16, 2, False, 0, [], "c923b", "Unsafe", b"\xC0\x01\x50\x01\x83\x00\x32", b"\x26",
             "Inca Ruins: Dark Space 2            "],
        31: [17, 2, False, 0, [], "c8db8", "", "", b"\x1e",          "Inca Ruins: Final Dark Space        "],

        32: [19, 1, False, 0, [3, 4, 7, 8], "5965e", "5966e", "", "",  "Gold Ship: Seth                     "],

        33: [20, 1, False, 0, [], "F71D", "F72D", "F743", "",       "Diamond Coast: Jar                  "],

        34: [21, 1, False, 0, [], "F79D", "F7AD", "F7C3", "",       "Freejia: Hotel                      "],
        35: [21, 1, False, 0, [], "5b6d8", "5b6e8", "", "",         "Freejia: Creepy Guy                 "],
        36: [21, 1, False, 0, [], "5cf9e", "5cfae", "5cfc4", "",    "Freejia: Trash Can 1                "],
        # text2 was 5cf5b
        37: [21, 1, False, 0, [], "5cf3d", "5cf49", "", "",         "Freejia: Trash Can 2                "],
        # text1 was @5b94d
        38: [21, 1, False, 0, [], "5b8b7", "5b962", "5b9ee", "",    "Freejia: Snitch                     "],
        39: [21, 2, False, 0, [51, 52, 53], "c96ce", "Safe", b"\x40\x00\xa0\x00\x83\x00\x11", b"\x34",
             "Freejia: Dark Space                 "],

        40: [22, 1, False, 0, [], "1AFD0", "", "", "",              "Diamond Mine: Chest                 "],
        41: [23, 1, False, 0, [], "5d7e4", "5d819", "5d830", "",    "Diamond Mine: Trapped Laborer       "],
        # text1 was aa811
        42: [24, 1, False, 0, [], "aa777", "aa85c", "", "",         "Diamond Mine: Laborer w/Elevator Key"],
        43: [25, 1, False, 0, [15], "5d4d2", "5d4eb", "5d506", "",  "Diamond Mine: Morgue                "],
        # text1 was aa7b4
        44: [25, 1, False, 0, [15], "aa757", "aa7ef", "", "",       "Diamond Mine: Laborer w/Mine Key    "],
        45: [26, 1, False, 0, [11, 12, 15], "5d2b0", "5d2da", "", "", "Diamond Mine: Sam                   "],
        46: [22, 2, False, 0, [], "c9a87", "Unsafe", b"\xb0\x01\x70\x01\x83\x00\x32", b"\x40",
             "Diamond Mine: Appearing Dark Space  "],  # Always open
        47: [22, 2, False, 0, [], "c98b0", "Unsafe", b"\xd0\x00\xc0\x00\x83\x00\x61", b"\x3d",
             "Diamond Mine: Dark Space at Wall    "],
        48: [23, 2, False, 0, [], "c9b49", "", "", b"\x42",          "Diamond Mine: Dark Space behind Wall"],

        49: [29, 1, False, 0, [], "1AFDD", "", "", "",              "Sky Garden: (NE) Platform Chest     "],
        50: [29, 1, False, 0, [], "1AFD9", "", "", "",              "Sky Garden: (NE) Blue Cyber Chest   "],
        51: [29, 1, False, 0, [], "1AFD5", "", "", "",              "Sky Garden: (NE) Statue Chest       "],
        52: [30, 1, False, 0, [], "1AFE2", "", "", "",              "Sky Garden: (SE) Dark Side Chest    "],
        53: [31, 1, False, 0, [], "1AFE7", "", "", "",              "Sky Garden: (SW) Ramp Chest         "],
        54: [29, 1, False, 0, [], "1AFEC", "", "", "",              "Sky Garden: (SW) Dark Side Chest    "],
        55: [72, 1, False, 0, [], "1AFF1", "", "", "",              "Sky Garden: (NW) Top Chest          "],
        56: [72, 1, False, 0, [], "1AFF5", "", "", "",              "Sky Garden: (NW) Bottom Chest       "],
        57: [29, 2, False, 0, [51, 52, 53], "c9d63", "Unsafe", b"\x90\x00\x70\x00\x83\x00\x22", b"\x4c",
             "Sky Garden: Dark Space (Foyer)      "],
        58: [29, 2, False, 0, [], "ca505", "Unsafe", b"\x70\x00\xa0\x00\x83\x00\x11", b"\x56",
             "Sky Garden: Dark Space (SE)         "],  # in the room
        59: [29, 2, False, 0, [], "ca173", "", "", b"\x51",          "Sky Garden: Dark Space (SW)         "],
        60: [29, 2, False, 0, [], "ca422", "Unsafe", b"\x20\x00\x70\x00\x83\x00\x44", b"\x54",
             "Sky Garden: Dark Space (NW)         "],

        61: [33, 1, False, 0, [], "1AFFF", "", "", "",              "Seaside Palace: Side Room Chest     "],
        62: [33, 1, False, 0, [], "1AFFA", "", "", "",              "Seaside Palace: First Area Chest    "],
        63: [33, 1, False, 0, [], "1B004", "", "", "",              "Seaside Palace: Second Area Chest   "],
        64: [34, 1, False, 0, [17], "68af7", "68ea9", "68f02", "",  "Seaside Palace: Buffy               "],
        # text1 was 69377
        65: [35, 1, False, 0, [9, 23], "6922d", "6939e", "693b7", "", "Seaside Palace: Coffin              "],
        66: [33, 2, False, 0, [51, 52, 53], "ca574", "Safe", b"\xf0\x02\x90\x00\x83\x00\x64", b"\x5a",
             "Seaside Palace: Dark Space          "],

        67: [37, 1, False, 0, [], "1B012", "", "", "",              "Mu: Empty Chest 1                   "],
        68: [37, 1, False, 0, [], "1B01B", "", "", "",              "Mu: Empty Chest 2                   "],
        69: [37, 1, False, 0, [], "698be", "698d2", "", "",         "Mu: Hope Statue 1                   "],
        70: [39, 1, False, 0, [], "69966", "69975", "", "",         "Mu: Hope Statue 2                   "],
        71: [40, 1, False, 0, [18], "1B00D", "", "", "",            "Mu: Chest s/o Hope Room 2           "],
        72: [40, 1, False, 0, [18], "1B009", "", "", "",            "Mu: Rama Chest N                    "],
        73: [40, 1, False, 0, [18], "1B016", "", "", "",            "Mu: Rama Chest E                    "],
        # Always open
        74: [38, 2, True, 0, [], "ca92d", "", "", b"\x60",           "Mu: Open Dark Space                 "],
        75: [71, 2, False, 0, [], "caa99", "", "", b"\x62",          "Mu: Slider Dark Space               "],

        76: [42, 1, False, 0, [], "F81D", "F82D", "F843", "",       "Angel Village: Dance Hall           "],
        77: [42, 2, False, 0, [51, 52, 53], "caf67", "Safe", b"\x90\x01\xb0\x00\x83\x01\x12", b"\x6c",
             "Angel Village: Dark Space           "],

        78: [43, 1, False, 0, [], "1B020", "", "", "",              "Angel Dungeon: Slider Chest         "],
        79: [43, 1, False, 0, [], "F89D", "F8AD", "F8C3", "",       "Angel Dungeon: Ishtar's Room        "],
        80: [43, 1, False, 0, [], "1B02A", "", "", "",              "Angel Dungeon: Puzzle Chest 1       "],
        81: [43, 1, False, 0, [], "1B02E", "", "", "",              "Angel Dungeon: Puzzle Chest 2       "],
        82: [43, 1, False, 0, [], "1B025", "", "", "",              "Angel Dungeon: Ishtar's Chest       "],

        83: [44, 1, False, 0, [], "F91D", "F92D", "F943", "",       "Watermia: West Jar                  "],
        # 84: [44,1,False,0,[],"7a5a8","","","",             "Watermia: Lance's Letter"],
        # text2 was 7afa7
        85: [44, 1, False, 0, [], "7ad21", "7aede", "", "",         "Watermia: Lance                     "],
        86: [44, 1, False, 0, [], "F99D", "F9AD", "F9C3", "",       "Watermia: Gambling House            "],
        87: [44, 1, False, 0, [], "79248", "79288", "792a1", "",    "Watermia: Russian Glass             "],
        88: [44, 2, False, 0, [51, 52, 53], "cb644", "Safe", b"\x40\x00\xa0\x00\x83\x00\x11", b"\x7c",
             "Watermia: Dark Space                "],

        89: [45, 1, False, 0, [], "7b5c5", "7b5d1", "", "",         "Great Wall: Necklace 1              "],
        90: [45, 1, False, 0, [], "7b625", "7b631", "", "",         "Great Wall: Necklace 2              "],
        91: [45, 1, False, 0, [], "1B033", "", "", "",              "Great Wall: Chest 1                 "],
        92: [45, 1, False, 0, [], "1B038", "", "", "",              "Great Wall: Chest 2                 "],
        93: [80, 2, False, 0, [], "cbb11", "Unsafe", b"\x60\x00\xc0\x02\x83\x20\x38", b"\x85",
             "Great Wall: Archer Dark Space       "],
        94: [80, 2, True, 0, [], "cbb80", "Unsafe", b"\x50\x01\x80\x04\x83\x00\x63", b"\x86",
             "Great Wall: Platform Dark Space     "],   # Always open
        95: [46, 2, False, 0, [51], "cbc60", "", "", b"\x88",        "Great Wall: Appearing Dark Space    "],

        96: [48, 1, False, 0, [], "FA1D", "FA2D", "FA43", "",       "Euro: Alley                         "],
        97: [48, 1, False, 0, [], "7c0b3", "7c0f3", "", "",         "Euro: Apple Vendor                  "],
        98: [48, 1, False, 0, [], "7e51f", "7e534", "7e54a", "",    "Euro: Hidden House                  "],
        99: [48, 1, False, 0, [], "7cd12", "7cd39", "7cd9b", "",    "Euro: Store Item 1                  "],
        # text2 was 7cedd
        100: [48, 1, False, 0, [], "7cdf9", "7ce28", "7ce3e", "",   "Euro: Store Item 2                  "],
        101: [48, 1, False, 0, [], "FA9D", "FAAD", "FAC3", "",      "Euro: Laborer Room                  "],
        102: [49, 1, False, 0, [40], "7df58", "7e10a", "", "",      "Euro: Ann                           "],
        103: [48, 2, False, 0, [51, 52, 53], "cc0b0", "Safe", b"\xb0\x00\xb0\x00\x83\x00\x11", b"\x99",
              "Euro: Dark Space                    "],

        104: [50, 1, False, 0, [], "1B03D", "", "", "",             "Mt. Temple: Red Jewel Chest         "],
        105: [50, 1, False, 0, [], "1B042", "", "", "",             "Mt. Temple: Drops Chest 1           "],
        106: [51, 1, False, 0, [], "1B047", "", "", "",             "Mt. Temple: Drops Chest 2           "],
        107: [52, 1, False, 0, [], "1B04C", "", "", "",             "Mt. Temple: Drops Chest 3           "],
        108: [53, 1, False, 0, [26], "1B051", "", "", "",           "Mt. Temple: Final Chest             "],
        109: [50, 2, False, 0, [50], "cc24f", "Unsafe", b"\xf0\x01\x10\x03\x83\x00\x44", b"\xa1",
              "Mt. Temple: Dark Space 1            "],
        110: [50, 2, False, 0, [50], "cc419", "Unsafe", b"\xc0\x07\xc0\x00\x83\x00\x28", b"\xa3",
              "Mt. Temple: Dark Space 2            "],
        111: [52, 2, False, 0, [50], "cc7b8", "", "", b"\xa7",       "Mt. Temple: Dark Space 3            "],

        112: [54, 1, False, 0, [], "FB1D", "FB2D", "FB43", "",      "Natives' Village: Statue Room       "],
        113: [55, 1, False, 0, [29], "893af", "8942a", "", "",      "Natives' Village: Statue            "],
        114: [54, 2, False, 0, [51, 52, 53], "cca37", "Safe", b"\xc0\x01\x50\x00\x83\x00\x22", b"\xac",
              "Natives' Village: Dark Space        "],

        115: [56, 1, False, 0, [], "1B056", "", "", "",              "Ankor Wat: Ramp Chest               "],
        116: [57, 1, False, 0, [], "1B05B", "", "", "",              "Ankor Wat: Flyover Chest            "],
        117: [59, 1, False, 0, [], "1B060", "", "", "",              "Ankor Wat: U-Turn Chest             "],
        118: [60, 1, False, 0, [28], "1B065", "", "", "",            "Ankor Wat: Drop Down Chest          "],
        119: [60, 1, False, 0, [28], "1B06A", "", "", "",            "Ankor Wat: Forgotten Chest          "],
        # slow text @89fdc
        120: [59, 1, False, 0, [], "89fa3", "89fbb", "", "",         "Ankor Wat: Glasses Location         "],
        # item was 89b0d, text was 89e2e
        121: [60, 1, False, 0, [28], "89adc", "89af1", "89b07", "",  "Ankor Wat: Spirit                   "],
        122: [76, 2, True, 0, [49, 50], "cce92", "Unsafe", b"\x20\x04\x30\x03\x83\x00\x46", b"\xb6",
              "Ankor Wat: Garden Dark Space        "],    # Always open
        123: [58, 2, False, 0, [49, 50, 51], "cd0a2", "", "", b"\xb8",  "Ankor Wat: Earthquaker Dark Space   "],
        124: [59, 2, True, 0, [49, 50, 51, 53], "cd1a7", "Unsafe", b"\xb0\x02\xc0\x01\x83\x00\x33", b"\xbb",
              "Ankor Wat: Drop Down Dark Space     "],   # Always open

        125: [61, 1, False, 0, [], "8b1b0", "", "", "",              "Dao: Entrance Item 1                "],
        126: [61, 1, False, 0, [], "8b1b5", "", "", "",              "Dao: Entrance Item 2                "],
        127: [61, 1, False, 0, [], "FB9D", "FBAD", "FBC3", "",       "Dao: East Grass                     "],
        128: [61, 1, False, 0, [], "8b016", "8b073", "8b090", "",    "Dao: Snake Game                     "],
        129: [61, 2, False, 0, [51, 52, 53], "cd3d0", "Safe", b"\x20\x00\x80\x00\x83\x00\x23", b"\xc3",
              "Dao: Dark Space                     "],

        # text2 was 8e800
        130: [62, 1, False, 0, [], "8dcb7", "8e66c", "8e800", "",    "Pyramid: Dark Space Top             "],
        131: [63, 1, False, 0, [36], "FC1D", "FC2D", "FC43", "",     "Pyramid: Under Stairs               "],
        132: [64, 1, False, 0, [36], "8c7b2", "8c7c9", "", "",       "Pyramid: Hieroglyph 1               "],
        133: [63, 1, False, 0, [36], "1B06F", "", "", "",            "Pyramid: Room 2 Chest               "],
        134: [63, 1, False, 0, [36], "8c879", "8c88c", "", "",       "Pyramid: Hieroglyph 2               "],
        135: [64, 1, False, 0, [36], "1B079", "", "", "",            "Pyramid: Room 3 Chest               "],
        136: [78, 1, False, 0, [36], "8c921", "8c934", "", "",       "Pyramid: Hieroglyph 3               "],
        137: [64, 1, False, 0, [36], "1B07E", "", "", "",            "Pyramid: Room 4 Chest               "],
        138: [64, 1, False, 0, [36], "8c9c9", "8c9dc", "", "",       "Pyramid: Hieroglyph 4               "],
        139: [63, 1, False, 0, [36], "1B074", "", "", "",            "Pyramid: Room 5 Chest               "],
        140: [79, 1, False, 0, [36], "8ca71", "8ca84", "", "",       "Pyramid: Hieroglyph 5               "],
        141: [77, 1, False, 0, [36], "8cb19", "8cb2c", "", "",       "Pyramid: Hieroglyph 6               "],
        142: [77, 2, True, 0, [], "cd570", "Unsafe", b"\xc0\x01\x90\x03\x83\x00\x44", b"\xcc",
              "Pyramid: Dark Space Bottom          "],   # Always open

        143: [66, 1, False, 0, [], "FC9D", "FCAD", "FCC3", "",       "Babel: Pillow                       "],
        # item was  99a61
        144: [66, 1, False, 0, [], "99a4f", "99ae4", "99afe", "",    "Babel: Force Field                  "],
        145: [66, 2, False, 0, [51, 52, 53], "ce09b", "Forced Unsafe", b"\x90\x07\xb0\x01\x83\x10\x28", b"\xdf",
              "Babel: Dark Space Bottom            "],
        146: [67, 2, False, 0, [51, 52, 53], "ce159", "Safe", b"\xb0\x02\xb0\x01\x83\x10\x23", b"\xe3",
              "Babel: Dark Space Top               "],

        147: [68, 1, False, 0, [], "1B083", "", "", "",              "Jeweler's Mansion: Chest            "],

        148: [18, 3, False, 0, [55, 56, 57, 58, 59], "", "", "", "",     "Castoth Prize                       "],
        149: [32, 3, False, 0, [54, 56, 57, 58, 59], "", "", "", "",     "Viper Prize                         "],
        150: [41, 3, False, 0, [54, 55, 57, 58, 59], "", "", "", "",     "Vampires Prize                      "],
        151: [47, 3, False, 0, [54, 55, 56, 58, 59], "", "", "", "",     "Sand Fanger Prize                   "],
        152: [65, 3, False, 0, [54, 55, 56, 57, 59], "", "", "", "",     "Mummy Queen Prize                   "],
        153: [67, 3, False, 0, [54, 55, 56, 57, 58], "", "", "", "",     "Babel Prize                         "]
    }
    # Initialize item pool, considers special attacks as "items"
    # Format = { ID:  [Quantity, Type code (1=item, 2=ability, 3=statue),
    #                  ROM Code, Name, TakesInventorySpace,
    #                  ProgressionType (1=unlocks new locations,2=quest item,3=no progression)] }
    ITEM_POOL = {
        0: [2, 1, b"\x00", "Nothing", False, 3],
        1: [45, 1, b"\x01", "Red Jewel", False, 1],
        2: [1, 1, b"\x02", "Prison Key", True, 1],
        3: [1, 1, b"\x03", "Inca Statue A", True, 1],
        4: [1, 1, b"\x04", "Inca Statue B", True, 1],
        5: [0, 1, b"\x05", "Inca Melody", True, 3],
        6: [12, 1, b"\x06", "Herb", False, 3],
        7: [1, 1, b"\x07", "Diamond Block", True, 1],
        8: [1, 1, b"\x08", "Wind Melody", True, 1],
        9: [1, 1, b"\x09", "Lola's Melody", True, 1],
        10: [1, 1, b"\x0a", "Large Roast", True, 1],
        11: [1, 1, b"\x0b", "Mine Key A", True, 1],
        12: [1, 1, b"\x0c", "Mine Key B", True, 1],
        13: [1, 1, b"\x0d", "Memory Melody", True, 1],
        14: [4, 1, b"\x0e", "Crystal Ball", True, 2],
        15: [1, 1, b"\x0f", "Elevator Key", True, 1],
        16: [1, 1, b"\x10", "Mu Palace Key", True, 1],
        17: [1, 1, b"\x11", "Purification Stone", True, 1],
        18: [2, 1, b"\x12", "Statue of Hope", True, 1],
        19: [2, 1, b"\x13", "Rama Statue", False, 2],
        20: [1, 1, b"\x14", "Magic Dust", True, 2],
        21: [0, 1, b"\x15", "Blue Journal", False, 3],
        22: [1, 1, b"\x16", "Lance's Letter", False, 3],
        23: [1, 1, b"\x17", "Necklace Stones", True, 1],
        24: [1, 1, b"\x18", "Will", True, 1],
        25: [1, 1, b"\x19", "Teapot", True, 1],
        26: [3, 1, b"\x1a", "Mushroom Drops", True, 1],
        27: [0, 1, b"\x1b", "Bag of Gold", False, 3],
        28: [1, 1, b"\x1c", "Black Glasses", False, 1],
        29: [1, 1, b"\x1d", "Gorgon Flower", True, 1],
        30: [1, 1, b"\x1e", "Hieroglyph", False, 2],
        31: [1, 1, b"\x1f", "Hieroglyph", False, 2],
        32: [1, 1, b"\x20", "Hieroglyph", False, 2],
        33: [1, 1, b"\x21", "Hieroglyph", False, 2],
        34: [1, 1, b"\x22", "Hieroglyph", False, 2],
        35: [1, 1, b"\x23", "Hieroglyph", False, 2],
        36: [1, 1, b"\x24", "Aura", True, 1],
        37: [1, 1, b"\x25", "Lola's Letter", False, 1],
        38: [1, 1, b"\x26", "Father's Journal", False, 2],
        39: [1, 1, b"\x27", "Crystal Ring", False, 1],
        40: [1, 1, b"\x28", "Apple", True, 1],
        41: [3, 1, b"\x29", "HP Jewel", False, 3],
        42: [1, 1, b"\x2a", "DEF Jewel", False, 3],
        43: [2, 1, b"\x2b", "STR Jewel", False, 3],
        44: [1, 1, b"\x2c", "Light Jewel", False, 3],
        45: [2, 1, b"\x2d", "Dark Jewel", False, 3],
        46: [1, 1, b"\x2e", "2 Red Jewels", False, 3],
        47: [1, 1, b"\x2f", "3 Red Jewels", False, 3],
        48: [1, 2, "", "Psycho Dash", False, 1],
        49: [1, 2, "", "Psycho Slider", False, 1],
        50: [1, 2, "", "Spin Dash", False, 1],
        51: [1, 2, "", "Dark Friar", False, 1],
        52: [1, 2, "", "Aura Barrier", False, 1],
        53: [1, 2, "", "Earthquaker", False, 1],
        54: [1, 3, "", "Mystic Statue 1", False, 2],
        55: [1, 3, "", "Mystic Statue 2", False, 2],
        56: [1, 3, "", "Mystic Statue 3", False, 2],
        57: [1, 3, "", "Mystic Statue 4", False, 2],
        58: [1, 3, "", "Mystic Statue 5", False, 2],
        59: [1, 3, "", "Mystic Statue 6", False, 2],
        60: [0, 2, "", "Nothing", False, 3]
    }
    # Define long item text for in-game format
    ITEM_TEXT_LONG = {
        0: b"\xd3\xd6\x1d\x8d\x8e\xa4\x87\x88\x8d\x86\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac\xac",
        1: b"\xd3\xd6\x1d\x80\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac\xac\xac",
        2: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x60\xa2\x88\xa3\x8e\x8d\xac\x4a\x84\xa9\x4f\xac\xac\xac",
        3: b"\xd3\xd6\x1d\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x40\x4f\xac\xac\xac\xac",
        4: b"\xd3\xd6\x1d\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x41\x4f\xac\xac\xac\xac",
        5: "",
        6: b"\xd3\xd6\x1d\x80\x8d\xac\x87\x84\xa2\x81\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac\xac",
        7: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x43\x88\x80\x8c\x8e\x8d\x83\xac\x41\x8b\x8e\x82\x8a\x4f",
        8: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x67\x88\x8d\x83\xac\x4c\x84\x8b\x8e\x83\xa9\x4f\xac\xac",
        9: b"\xd3\xd6\x1d\x4b\x8e\x8b\x80\x0e\xa3\xac\x4c\x84\x8b\x8e\x83\xa9\x4f\xac\xac\xac\xac",
        10: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x4b\x80\xa2\x86\x84\xac\x62\x8e\x80\xa3\xa4\x4f\xac\xac",
        11: b"\xd3\xd6\x1d\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x40\x4f\xac\xac\xac\xac\xac\xac\xac",
        12: b"\xd3\xd6\x1d\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x41\x4f\xac\xac\xac\xac\xac\xac\xac",
        13: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x4c\x84\x8c\x8e\xa2\xa9\xac\x4c\x84\x8b\x8e\x83\xa9\x4f",
        14: b"\xd3\xd6\x1d\x80\xac\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x41\x80\x8b\x8b\x4f\xac\xac\xac",
        15: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x44\x8b\x84\xa6\x80\xa4\x8e\xa2\xac\x4a\x84\xa9\x4f\xac",
        16: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x4c\xa5\xac\x60\x80\x8b\x80\x82\x84\xac\x4a\x84\xa9\x4f",
        17: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x60\xa5\xa2\x88\xa4\xa9\xac\x63\xa4\x8e\x8d\x84\x4f\xac",
        18: b"\xd3\xd6\x1d\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x8e\x85\xac\x47\x8e\xa0\x84\x4f\xac",
        19: b"\xd3\xd6\x1d\x80\xac\x62\x80\x8c\x80\xac\x63\xa4\x80\xa4\xa5\x84\x4f\xac\xac\xac\xac",
        20: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x4c\x80\x86\x88\x82\xac\x43\xa5\xa3\xa4\x4f\xac\xac\xac",
        21: "",
        22: b"\xd3\xd6\x1d\x4b\x80\x8d\x82\x84\x0e\xa3\xac\x4b\x84\xa4\xa4\x84\xa2\x4f\xac\xac\xac",
        23: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x4d\x84\x82\x8a\x8b\x80\x82\x84\x4f\xac\xac\xac\xac\xac",
        24: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x67\x88\x8b\x8b\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac",
        25: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x64\x84\x80\xa0\x8e\xa4\x4f\xac\xac\xac\xac\xac\xac\xac",
        26: b"\xd3\xd6\x1d\x4c\xa5\xa3\x87\xa2\x8e\x8e\x8c\xac\x43\xa2\x8e\xa0\xa3\x4f\xac\xac\xac",
        27: "",
        28: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x41\x8b\x80\x82\x8a\xac\x46\x8b\x80\xa3\xa3\x84\xa3\x4f",
        29: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x46\x8e\xa2\x86\x8e\x8d\xac\x45\x8b\x8e\xa7\x84\xa2\x4f",
        30: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
        31: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
        32: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
        33: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
        34: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
        35: b"\xd3\xd6\x1d\x80\xac\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\x64\x88\x8b\x84\x4f",
        36: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x40\xa5\xa2\x80\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac",
        37: b"\xd3\xd6\x1d\x4b\x8e\x8b\x80\x0e\xa3\xac\x4b\x84\xa4\xa4\x84\xa2\x4f\xac\xac\xac\xac",
        38: b"\xd3\xd6\x1d\x45\x80\xa4\x87\x84\xa2\x0e\xa3\xac\x49\x8e\xa5\xa2\x8d\x80\x8b\x4f\xac",
        39: b"\xd3\xd6\x1d\xa4\x87\x84\xac\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x62\x88\x8d\x86\x4f\xac",
        40: b"\xd3\xd6\x1d\x80\x8d\xac\x40\xa0\xa0\x8b\x84\x4f\xac\xac\xac\xac\xac\xac\xac\xac\xac",
        41: b"\xd3\xd6\x1d\x80\x8d\xac\x47\x60\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac\xac\xac",
        42: b"\xd3\xd6\x1d\x80\xac\x43\x44\x45\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac\xac\xac",
        43: b"\xd3\xd6\x1d\x80\xac\x63\x64\x62\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac\xac\xac",
        44: b"\xd3\xd6\x1d\x80\xac\x4b\x88\x86\x87\xa4\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac",
        45: b"\xd3\xd6\x1d\x80\xac\x43\x80\xa2\x8a\xac\x49\x84\xa7\x84\x8b\x4f\xac\xac\xac\xac\xac",
        46: b"\xd3\xd6\x1d\x22\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\x4f\xac\xac\xac\xac\xac",
        47: b"\xd3\xd6\x1d\x23\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\x4f\xac\xac\xac\xac\xac",
        48: "",
        49: "",
        50: "",
        51: "",
        52: "",
        53: "",
        54: "",
        55: "",
        56: "",
        57: "",
        58: "",
        59: "",
        60: ""
    }
    # Define short item text for in-game format
    # Currently only used in Jeweler's inventory
    ITEM_TEXT_SHORT = {
        0: b"\x4d\x8e\xa4\x87\x88\x8d\x86\xac\xac\xac\xac\xac\xac",
        1: b"\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xac\xac\xac\xac",
        2: b"\x60\xa2\x88\xa3\x8e\x8d\xac\x4a\x84\xa9\xac\xac\xac",
        3: b"\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x40",
        4: b"\x48\x8d\x82\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\x41",
        5: "",
        6: b"\x47\x84\xa2\x81\xac\xac\xac\xac\xac\xac\xac\xac\xac",
        7: b"\x43\x88\x80\x8c\x8e\x8d\x83\xac\x41\x8b\x8e\x82\x8a",
        8: b"\x67\x88\x8d\x83\xac\x4c\x84\x8b\x8e\x83\xa9\xac\xac",
        9: b"\x4b\x8e\x8b\x80\x0e\xa3\xac\x4c\x84\x8b\x8e\x83\xa9",
        10: b"\x4b\x80\xa2\x86\x84\xac\x62\x8e\x80\xa3\xa4\xac\xac",
        11: b"\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x40\xac\xac\xac",
        12: b"\x4c\x88\x8d\x84\xac\x4a\x84\xa9\xac\x41\xac\xac\xac",
        13: b"\x4c\x84\x8c\x8e\xa2\xa9\xac\x4c\x84\x8b\x8e\x83\xa9",
        14: b"\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x41\x80\x8b\x8b\xac",
        15: b"\x44\x8b\x84\xa6\x80\xa4\x8e\xa2\xac\x4a\x84\xa9\xac",
        16: b"\x4c\xa5\xac\x60\x80\x8b\x80\x82\x84\xac\x4a\x84\xa9",
        17: b"\x60\xa5\xa2\x88\xa4\xa9\xac\x63\xa4\x8e\x8d\x84\xac",
        18: b"\x47\x8e\xa0\x84\xac\x63\xa4\x80\xa4\xa5\x84\xac\xac",
        19: b"\x62\x80\x8c\x80\xac\x63\xa4\x80\xa4\xa5\x84\xac\xac",
        20: b"\x4c\x80\x86\x88\x82\xac\x43\xa5\xa3\xa4\xac\xac\xac",
        21: "",
        22: b"\x4b\x80\x8d\x82\x84\xac\x4b\x84\xa4\xa4\x84\xa2\xac",
        23: b"\x4d\x84\x82\x8a\x8b\x80\x82\x84\xac\xac\xac\xac\xac",
        24: b"\x67\x88\x8b\x8b\xac\xac\xac\xac\xac\xac\xac\xac\xac",
        25: b"\x64\x84\x80\xa0\x8e\xa4\xac\xac\xac\xac\xac\xac\xac",
        26: b"\x63\x87\xa2\x8e\x8e\x8c\xac\x43\xa2\x8e\xa0\xa3\xac",
        27: "",
        28: b"\x41\x8b\x80\x82\x8a\xac\x46\x8b\x80\xa3\xa3\x84\xa3",
        29: b"\x46\x8e\xa2\x86\x8e\x8d\xac\x45\x8b\x8e\xa7\x84\xa2",
        30: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
        31: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
        32: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
        33: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
        34: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
        35: b"\x47\x88\x84\xa2\x8e\x86\x8b\xa9\xa0\x87\xac\xac\xac",
        36: b"\x40\xa5\xa2\x80\xac\xac\xac\xac\xac\xac\xac\xac\xac",
        37: b"\x4b\x8e\x8b\x80\x0e\xa3\xac\x4b\x84\xa4\xa4\x84\xa2",
        38: b"\x49\x8e\xa5\xa2\x8d\x80\x8b\xac\xac\xac\xac\xac\xac",
        39: b"\x42\xa2\xa9\xa3\xa4\x80\x8b\xac\x62\x88\x8d\x86\xac",
        40: b"\x40\xa0\xa0\x8b\x84\xac\xac\xac\xac\xac\xac\xac\xac",
        41: b"\x47\x60\xac\x49\x84\xa7\x84\x8b\xac\xac\xac\xac\xac",
        42: b"\x43\x44\x45\xac\x49\x84\xa7\x84\x8b\xac\xac\xac\xac",
        43: b"\x63\x64\x62\xac\x49\x84\xa7\x84\x8b\xac\xac\xac\xac",
        44: b"\x4b\x88\x86\x87\xa4\xac\x49\x84\xa7\x84\x8b\xac\xac",
        45: b"\x43\x80\xa2\x8a\xac\x49\x84\xa7\x84\x8b\xac\xac\xac",
        46: b"\x22\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\xac",
        47: b"\x23\xac\x62\x84\x83\xac\x49\x84\xa7\x84\x8b\xa3\xac",
        48: b"\xd6\x3c\x43\x80\xa3\x87",
        49: b"\xd6\x3c\x63\x8b\x88\x83\x84\xa2",
        50: b"\xd7\x31\x43\x80\xa3\x87",
        51: b"\xd6\x0c\x45\xa2\x88\x80\xa2",
        52: b"\xd6\x03\x41\x80\xa2\xa2\x88\x84\xa2",
        53: b"\x44\x80\xa2\xa4\x87\xa1\xa5\x80\x8a\x84\xa2",
        54: "",
        55: "",
        56: "",
        57: "",
        58: "",
        59: "",
        60: ""
    }
    # Define location text for in-game format
    LOCATION_TEXT = {
        0: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
        1: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
        2: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
        3: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
        4: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"
        5: b"\x64\x87\x84\xac\x49\x84\xa7\x84\x8b\x84\xa2",  # "the Jeweler"

        6: b"\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",    # "South Cape"
        7: b"\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",    # "South Cape"
        8: b"\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",    # "South Cape"
        9: b"\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",    # "South Cape"
        10: b"\x63\x8e\xa5\xa4\x87\xac\x42\x80\xa0\x84",    # "South Cape"

        11: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x42\x80\xa3\xa4\x8b\x84",   # "Edward's Castle"
        12: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x42\x80\xa3\xa4\x8b\x84",   # "Edward's Castle"

        13: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x60\xa2\x88\xa3\x8e\x8d",   # "Edward's Prison"
        14: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x60\xa2\x88\xa3\x8e\x8d",   # "Edward's Prison"

        15: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",   # "Edward's Tunnel"
        16: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",   # "Edward's Tunnel"
        17: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",   # "Edward's Tunnel"
        18: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",   # "Edward's Tunnel"
        19: b"\x44\x83\xa7\x80\xa2\x83\x0e\xa3\xac\x64\xa5\x8d\x8d\x84\x8b",   # "Edward's Tunnel"

        20: b"\x48\xa4\x8e\xa2\xa9",   # "Itory"
        21: b"\x48\xa4\x8e\xa2\xa9",   # "Itory"
        22: b"\x48\xa4\x8e\xa2\xa9",   # "Itory"

        23: b"\x4c\x8e\x8e\x8d\xac\x44\xa2\x88\x81\x84",   # "Moon Tribe"

        24: b"\x48\x8d\x82\x80",   # "Inca"
        25: b"\x48\x8d\x82\x80",   # "Inca"
        26: b"\x48\x8d\x82\x80",   # "Inca"
        27: b"\x48\x8d\x82\x80",   # "Inca"
        28: b"\x63\x88\x8d\x86\x88\x8d\x86\xac\xa3\xa4\x80\xa4\xa5\x84",   # "Singing Statue"
        29: b"\x48\x8d\x82\x80",   # "Inca"
        30: b"\x48\x8d\x82\x80",   # "Inca"
        31: b"\x48\x8d\x82\x80",   # "Inca"

        32: b"\x46\x8e\x8b\x83\xac\x63\x87\x88\xa0",   # "Gold Ship"

        33: b"\xd6\x0e\x42\x8e\x80\xa3\xa4",   # "Diamond Coast"

        34: b"\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"
        35: b"\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"
        36: b"\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"
        37: b"\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"
        38: b"\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"
        39: b"\x45\xa2\x84\x84\x89\x88\x80",   # "Freejia"

        40: b"\xd6\x0e\x4c\x88\x8d\x84",       # "Diamond Mine"
        41: b"\x4b\x80\x81\x8e\xa2\x84\xa2",   # "Laborer"
        42: b"\x4b\x80\x81\x8e\xa2\x84\xa2",   # "Laborer"
        43: b"\xd6\x0e\x4c\x88\x8d\x84",       # "Diamond Mine"
        44: b"\x4b\x80\x81\x8e\xa2\x84\xa2",   # "Laborer"
        45: b"\x63\x80\x8c",                   # "Sam"
        46: b"\xd6\x0e\x4c\x88\x8d\x84",       # "Diamond Mine"
        47: b"\xd6\x0e\x4c\x88\x8d\x84",       # "Diamond Mine"
        48: b"\xd6\x0e\x4c\x88\x8d\x84",       # "Diamond Mine"


        49: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
        50: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
        51: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
        52: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
        53: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
        54: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
        55: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
        56: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
        57: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
        58: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
        59: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"
        60: b"\x63\x8a\xa9\xac\x46\x80\xa2\x83\x84\x8d",   # "Sky Garden"

        61: b"\xd7\x32\xd7\x93",   # "Seaside Palace"
        62: b"\xd7\x32\xd7\x93",   # "Seaside Palace"
        63: b"\xd7\x32\xd7\x93",   # "Seaside Palace"
        64: b"\x41\xa5\x85\x85\xa9",   # "Buffy"
        65: b"\x42\x8e\x85\x85\x88\x8d",   # "Coffin"
        66: b"\xd7\x32\xd7\x93",   # "Seaside Palace"

        67: b"\x4c\xa5",   # "Mu"
        68: b"\x4c\xa5",   # "Mu"
        69: b"\x4c\xa5",   # "Mu"
        70: b"\x4c\xa5",   # "Mu"
        71: b"\x4c\xa5",   # "Mu"
        72: b"\x4c\xa5",   # "Mu"
        73: b"\x4c\xa5",   # "Mu"
        74: b"\x4c\xa5",   # "Mu"
        75: b"\x4c\xa5",   # "Mu"

        76: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
        77: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
        78: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
        79: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
        80: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
        81: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"
        82: b"\xd6\x01\x66\x88\x8b\x8b\x80\x86\x84",   # "Angel Village"

        83: b"\x67\x80\xa4\x84\xa2\x8c\x88\x80",   # "Watermia"
        84: b"\x67\x80\xa4\x84\xa2\x8c\x88\x80",   # "Watermia"
        85: b"\x4b\x80\x8d\x82\x84",   # "Lance"
        86: b"\x67\x80\xa4\x84\xa2\x8c\x88\x80",   # "Watermia"
        87: b"\x67\x80\xa4\x84\xa2\x8c\x88\x80",   # "Watermia"
        88: b"\x67\x80\xa4\x84\xa2\x8c\x88\x80",   # "Watermia"

        89: b"\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
        90: b"\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
        91: b"\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
        92: b"\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
        93: b"\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
        94: b"\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"
        95: b"\xd6\x16\x67\x80\x8b\x8b",   # "Great Wall"

        96: b"\x44\xa5\xa2\x8e",   # "Euro"
        97: b"\x44\xa5\xa2\x8e",   # "Euro"
        98: b"\x44\xa5\xa2\x8e",   # "Euro"
        99: b"\x44\xa5\xa2\x8e",   # "Euro"
        100: b"\x44\xa5\xa2\x8e",   # "Euro"
        101: b"\x44\xa5\xa2\x8e",   # "Euro"
        102: b"\x40\x8d\x8d",       # "Ann"
        103: b"\x44\xa5\xa2\x8e",   # "Euro"

        104: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
        105: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
        106: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
        107: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
        # "Mt. Kress (end)"
        108: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3\xac\x6e\x84\x8d\x83\x6f",
        109: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
        110: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"
        111: b"\x4c\xa4\x2a\xac\x4a\xa2\x84\xa3\xa3",   # "Mt. Kress"

        112: b"\xd7\x21\x66\x88\x8b\x8b\x80\x86\x84",   # "Native Village"
        113: b"\x63\xa4\x80\xa4\xa5\x84",               # "Statue"
        114: b"\xd7\x21\x66\x88\x8b\x8b\x80\x86\x84",   # "Native Village"

        115: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
        116: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
        117: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
        118: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
        119: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
        120: b"\x63\x87\xa2\xa5\x81\x81\x84\xa2",       # "Shrubber"
        121: b"\x63\xa0\x88\xa2\x88\xa4",               # "Spirit"
        122: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
        123: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"
        124: b"\x40\x8d\x8a\x8e\xa2\xac\x67\x80\xa4",   # "Ankor Wat"

        125: b"\x43\x80\x8e",   # "Dao"
        126: b"\x43\x80\x8e",   # "Dao"
        127: b"\x43\x80\x8e",   # "Dao"
        128: b"\x63\x8d\x80\x8a\x84\xac\x86\x80\x8c\x84",   # "Snake Game"
        129: b"\x43\x80\x8e",   # "Dao"

        130: b"\x46\x80\x88\x80",   # "Gaia"
        131: b"\xd6\x3f",   # "Pyramid"
        132: b"\xd6\x3f",   # "Pyramid"
        133: b"\xd6\x3f",   # "Pyramid"
        134: b"\xd6\x3f",   # "Pyramid"
        135: b"\xd6\x3f",   # "Pyramid"
        136: b"\x4a\x88\x8b\x8b\x84\xa2\xac\x26",   # "Killer 6"
        137: b"\xd6\x3f",   # "Pyramid"
        138: b"\xd6\x3f",   # "Pyramid"
        139: b"\xd6\x3f",   # "Pyramid"
        140: b"\xd6\x3f",   # "Pyramid"
        141: b"\xd6\x3f",   # "Pyramid"
        142: b"\xd6\x3f",   # "Pyramid"

        143: b"\x41\x80\x81\x84\x8b",   # "Babel"
        144: b"\x41\x80\x81\x84\x8b",   # "Babel"
        145: b"\x41\x80\x81\x84\x8b",   # "Babel"
        146: b"\x41\x80\x81\x84\x8b",   # "Babel"

        # "Jeweler's Mansion"
        147: b"\x49\x84\xa7\x84\x8b\x84\xa2\x0e\xa3\xac\x4c\x80\x8d\xa3\x88\x8e\x8d",

        148: "",   # "Castoth"
        149: "",   # "Viper"
        150: "",   # "Vampires"
        151: "",   # "Sand Fanger"
        152: "",   # "Mummy Queen"
        153: ""    # "Olman"
    }
    # Enemy map database
    # FORMAT: { ID: [EnemySet, RewardBoss(0 for no reward), Reward, SearchHeader,
    #           SpritesetOffset,EventAddrLow,EventAddrHigh,RestrictedEnemysets]}
    # ROM address for room reward table is mapID + $1aade
    MAPS = {
        # For now, no one can have enemyset 10 (Ankor Wat outside)
        # Underground Tunnel
        12: [0, 1, 0, b"\x0C\x00\x02\x05\x03", 4, "c867a", "c86ac", []],
        13: [0, 1, 0, b"\x0D\x00\x02\x03\x03", 4, "c86ac", "c875c", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],
        # Weird 4way issues
        14: [0, 1, 0, b"\x0E\x00\x02\x03\x03", 4, "c875c", "c8847", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],
        15: [0, 1, 0, b"\x0F\x00\x02\x03\x03", 4, "c8847", "c8935", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
        # Spike balls
        18: [0, 1, 0, b"\x12\x00\x02\x03\x03", 4, "c8986", "c8aa9", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],

        # Inca Ruins
        # Moon Tribe cave
        27: [1, 0, 0, b"\x1B\x00\x02\x05\x03", 4, "c8c33", "c8c87", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]],
        29: [1, 1, 0, b"\x1D\x00\x02\x0F\x03", 4, "c8cc4", "c8d85", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
        32: [1, 1, 0, b"\x20\x00\x02\x08\x03", 4, "c8e16", "c8e75", []],  # Broken statue
        # Floor switch
        33: [2, 1, 0, b"\x21\x00\x02\x08\x03", 4, "c8e75", "c8f57", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],
        34: [2, 1, 0, b"\x22\x00\x02\x08\x03", 4, "c8f57", "c9029", []],  # Floor switch
        35: [2, 1, 0, b"\x23\x00\x02\x0A\x03", 4, "c9029", "c90d5", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],
        37: [1, 1, 0, b"\x25\x00\x02\x08\x03", 4, "c90f3", "c91a0", [1]],  # Diamond block
        38: [1, 1, 0, b"\x26\x00\x02\x08\x03", 4, "c91a0", "c9242", []],  # Broken statues
        39: [1, 1, 0, b"\x27\x00\x02\x0A\x03", 4, "c9242", "c92f2", []],
        # Falling blocks
        40: [1, 1, 0, b"\x28\x00\x02\x08\x03", 4, "c92f2", "c935f", [1]],

        # Diamond Mine
        61: [3, 2, 0, b"\x3D\x00\x02\x08\x03", 4, "c9836", "c98b7", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
        62: [3, 2, 0, b"\x3E\x00\x02\x08\x03", 4, "c98b7", "c991a", []],
        63: [3, 2, 0, b"\x3F\x00\x02\x05\x03", 4, "c991a", "c9a41", []],
        # Trapped laborer (??)
        64: [3, 2, 0, b"\x40\x00\x02\x08\x03", 4, "c9a41", "c9a95", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
        # Stationary Grundit
        65: [3, 2, 0, b"\x41\x00\x02\x00\x03", 4, "c9a95", "c9b39", [0, 2, 3, 4, 5, 11]],
        69: [3, 2, 0, b"\x45\x00\x02\x08\x03", 4, "c9ba1", "c9bf4", []],
        70: [3, 2, 0, b"\x46\x00\x02\x08\x03", 4, "c9bf4", "c9c5c", [3, 13]],

        # Sky Garden
        77: [4, 2, 0, b"\x4D\x00\x02\x12\x03", 4, "c9db3", "c9e92", []],
        78: [5, 2, 0, b"\x4E\x00\x02\x10\x03", 4, "c9e92", "c9f53", []],
        79: [4, 2, 0, b"\x4F\x00\x02\x12\x03", 4, "c9f53", "ca01a", [4, 5]],
        80: [5, 2, 0, b"\x50\x00\x02\x10\x03", 4, "ca01a", "ca0cb", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
        81: [4, 2, 0, b"\x51\x00\x02\x12\x03", 4, "ca0cb", "ca192", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
        82: [5, 2, 0, b"\x52\x00\x02\x10\x03", 4, "ca192", "ca247", [4, 5]],
        83: [4, 2, 0, b"\x53\x00\x02\x12\x03", 4, "ca247", "ca335", [4, 5]],
        84: [5, 2, 0, b"\x54\x00\x02\x12\x03", 4, "ca335", "ca43b", [4, 5]],

        # Mu
        #            92: [6,0,0,b"\x5C\x00\x02\x15\x03",4,[]],  # Seaside Palace
        95: [6, 3, 0, b"\x5F\x00\x02\x14\x03", 4, "ca71b", "ca7ed", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]],
        96: [6, 3, 0, b"\x60\x00\x02\x14\x03", 4, "ca7ed", "ca934", [6]],
        97: [6, 3, 0, b"\x61\x00\x02\x14\x03", 4, "ca934", "caa7b", [6]],
        98: [6, 3, 0, b"\x62\x00\x02\x14\x03", 4, "caa7b", "cab28", []],
        100: [6, 3, 0, b"\x64\x00\x02\x14\x03", 4, "cab4b", "cabd4", []],
        101: [6, 3, 0, b"\x65\x00\x02\x14\x03", 4, "cabd4", "cacc3", [6]],

        # Angel Dungeon
        # Add 10's back in once flies are fixed
        109: [7, 3, 0, b"\x6D\x00\x02\x16\x03", 4, "caf6e", "cb04b", [2, 7, 8, 9, 10, 11]],
        110: [7, 3, 0, b"\x6E\x00\x02\x18\x03", 4, "cb04b", "cb13e", [2, 7, 8, 9, 10, 11]],
        111: [7, 3, 0, b"\x6F\x00\x02\x1B\x03", 4, "cb13e", "cb1ae", [2, 7, 8, 9, 10, 11]],
        112: [7, 3, 0, b"\x70\x00\x02\x16\x03", 4, "cb1ae", "cb258", [2, 7, 8, 9, 10, 11]],
        113: [7, 3, 0, b"\x71\x00\x02\x18\x03", 4, "cb258", "cb29e", [2, 7, 8, 9, 10, 11]],
        114: [7, 3, 0, b"\x72\x00\x02\x18\x03", 4, "cb29e", "cb355", [2, 7, 8, 9, 10, 11]],

        # Great Wall
        # Add 10's back in once flies are fixed
        130: [8, 4, 0, b"\x82\x00\x02\x1D\x03", 4, "cb6c1", "cb845", [2, 8, 9, 10, 11]],
        131: [8, 4, 0, b"\x83\x00\x02\x1D\x03", 4, "cb845", "cb966", [2, 7, 8, 9, 10, 11]],
        133: [8, 4, 0, b"\x85\x00\x02\x1D\x03", 4, "cb97d", "cbb18", [2, 8, 9, 10, 11]],
        134: [8, 4, 0, b"\x86\x00\x02\x1D\x03", 4, "cbb18", "cbb87", [2, 7, 8, 9, 10, 11]],
        135: [8, 4, 0, b"\x87\x00\x02\x1D\x03", 4, "cbb87", "cbc3b", [2, 7, 8, 9]],
        136: [8, 4, 0, b"\x88\x00\x02\x1D\x03", 4, "cbc3b", "cbd0a", [2, 7, 8, 9, 11]],

        # Mt Temple
        160: [9, 4, 0, b"\xA0\x00\x02\x20\x03", 4, "cc18c", "cc21c", []],
        161: [9, 4, 0, b"\xA1\x00\x02\x20\x03", 4, "cc21c", "cc335", []],
        162: [9, 4, 0, b"\xA2\x00\x02\x20\x03", 4, "cc335", "cc3df", []],
        163: [9, 4, 0, b"\xA3\x00\x02\x20\x03", 4, "cc3df", "cc4f7", []],
        164: [9, 4, 0, b"\xA4\x00\x02\x20\x03", 4, "cc4f7", "cc5f8", [0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13]],
        165: [9, 4, 0, b"\xA5\x00\x02\x20\x03", 4, "cc5f8", "cc703", []],
        166: [9, 4, 0, b"\xA6\x00\x02\x20\x03", 4, "cc703", "cc7a1", []],
        167: [9, 4, 0, b"\xA7\x00\x02\x20\x03", 4, "cc7a1", "cc9a3", [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13]],
        168: [9, 4, 0, b"\xA8\x00\x02\x20\x03", 4, "cc9a3", "cca02", []],

        # Ankor Wat
        176: [10, 6, 0, b"\xB0\x00\x02\x2C\x03", 4, "ccb1b", "ccbd8", []],
        177: [11, 6, 0, b"\xB1\x00\x02\x08\x03", 4, "ccbd8", "ccca5", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],
        178: [11, 6, 0, b"\xB2\x00\x02\x08\x03", 4, "ccca5", "ccd26", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],
        179: [11, 6, 0, b"\xB3\x00\x02\x08\x03", 4, "ccd26", "ccd83", []],
        180: [11, 6, 0, b"\xB4\x00\x02\x08\x03", 4, "ccd83", "ccdd7", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],
        181: [11, 6, 0, b"\xB5\x00\x02\x08\x03", 4, "ccdd7", "cce7b", []],
        182: [10, 6, 0, b"\xB6\x00\x02\x2C\x03", 4, "cce7b", "cd005", [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13]],
        # Earthquaker Golem
        183: [11, 6, 0, b"\xB7\x00\x02\x08\x03", 4, "cd005", "cd092", []],
        184: [11, 6, 0, b"\xB8\x00\x02\x08\x03", 4, "cd092", "cd0df", [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 13]],
        185: [11, 6, 0, b"\xB9\x00\x02\x08\x03", 4, "cd0df", "cd137", []],
        186: [10, 6, 0, b"\xBA\x00\x02\x2C\x03", 4, "cd137", "cd197", []],
        187: [11, 6, 0, b"\xBB\x00\x02\x08\x03", 4, "cd197", "cd1f4", []],
        188: [11, 6, 0, b"\xBC\x00\x02\x24\x03", 4, "cd1f4", "cd29a", []],
        189: [11, 6, 0, b"\xBD\x00\x02\x08\x03", 4, "cd29a", "cd339", []],
        190: [11, 6, 0, b"\xBE\x00\x02\x08\x03", 4, "cd339", "cd392", []],

        # Pyramid
        204: [12, 5, 0, b"\xCC\x00\x02\x08\x03", 4, "cd539", "cd58c", []],
        206: [12, 5, 0, b"\xCE\x00\x02\x08\x03", 4, "cd5c6", "cd650", []],
        207: [12, 5, 0, b"\xCF\x00\x02\x08\x03", 4, "cd650", "cd6f3", []],
        208: [12, 5, 0, b"\xD0\x00\x02\x08\x03", 4, "cd6f3", "cd752", []],
        209: [12, 5, 0, b"\xD1\x00\x02\x08\x03", 4, "cd752", "cd81b", []],
        210: [12, 5, 0, b"\xD2\x00\x02\x08\x03", 4, "cd81b", "cd8f1", []],
        211: [12, 5, 0, b"\xD3\x00\x02\x08\x03", 4, "cd8f1", "cd9a1", []],
        212: [12, 5, 0, b"\xD4\x00\x02\x08\x03", 4, "cd9a1", "cda80", []],
        213: [12, 5, 0, b"\xD5\x00\x02\x08\x03", 4, "cda80", "cdb4b", []],
        214: [12, 5, 0, b"\xD6\x00\x02\x26\x03", 4, "cdb4b", "cdc1e", []],
        215: [12, 5, 0, b"\xD7\x00\x02\x28\x03", 4, "cdc1e", "cdcfd", [0, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13]],
        216: [12, 5, 0, b"\xD8\x00\x02\x08\x03", 4, "cdcfd", "cde4f", [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13]],
        217: [12, 5, 0, b"\xD9\x00\x02\x26\x03", 4, "cde4f", "cdf3c", []],
        219: [12, 5, 0, b"\xDB\x00\x02\x26\x03", 4, "cdf76", "ce010", []],

        # Jeweler's Mansion
        233: [13, 0, 0, b"\xE9\x00\x02\x22\x03", 4, "ce224", "ce3a6", [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13]]

    }
    # Required items are more likely to be placed in easier modes
    PROGRESS_ADJ = [1.5, 1.25, 1, 1]
    # Define addresses for in-game spoiler text
    SPOILER_ADDRESSES = {
        0: "4caf5",   # Edward's Castle guard, top floor (4c947)
        1: "4e9ff",   # Itory elder (4e929)
        2: "58ac0",   # Gold Ship queen (589ff)
        3: "5ad6b",   # Man at Diamond Coast (5ab5c)
        # 4: "5bfde",   # Freejia laborer (5bfaa)
        5: "69167",   # Seaside Palace empty coffin (68feb)
        6: "6dc97",   # Ishtar's apprentice (6dc50)
        7: "79c81",   # Watermia, Kara's journal (79bf5)
        8: "7d892",   # Euro: Erasquez (7d79e)
        9: "89b2a",   # Ankor Wat, spirit (89abf)
        10: "8ad0c",   # Dao: girl with note (8acc5)
        11: "99b8f",   # Babel: spirit (99b2e)
    }
